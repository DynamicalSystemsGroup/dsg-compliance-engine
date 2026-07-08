"""FlexoBackend — persist the Dataset to a Flexo MMS versioned quadstore.

Flexo MMS is a server-based, git-like *versioned* RDF quadstore: an
append-only commit history over named graphs, partitioned by
project / branch / ref. It is deployed self-hosted inside an IL4 enclave.

The live remote server is not reachable from this sandbox, so — exactly
like the repo's ``FakeProvisionBackend`` and the deferred ``terraform
apply`` — this module ships two things:

  - ``FakeFlexoStore``: a deterministic, local-filesystem simulation of
    Flexo's append-only versioned semantics. Every ``commit`` appends a
    new immutable version keyed by ``(project, ref)``; earlier versions
    remain resolvable forever. It is fully offline and testable with no
    network.
  - ``FlexoBackend``: the real ``StoreBackend`` implementation. By
    default it is backed by a ``FakeFlexoStore`` (the test / demo path),
    so ``probe()`` is always available and offline. A real-endpoint mode,
    constructed from an ``endpoint`` (or ``FLEXO_ENDPOINT`` env var), is
    written but connection-guarded: if a real endpoint is configured and
    unreachable, ``probe()`` raises ``BackendUnavailable`` the same way
    ``LocalBackend`` signals unavailability. The live connection path is
    documented as deferred.

Content addressing reuses the registry's SHA-256 discipline
(``registry.content_hash``): each named graph is canonicalized to sorted
N-Triples bytes and hashed, and a commit's version id is the SHA-256 of
its sorted per-graph hashes. Identical content therefore yields an
identical version id, and the store never invents a new hash.

The Dataset-building responsibility stays OUT of this backend, matching
``LocalBackend`` and the ``StoreBackend`` docstring: the runtime builds
the rdflib Dataset; the backend only persists / loads named graphs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from rdflib import Dataset, Graph, URIRef

from compliance_engine.ontology.prefixes import CE, NAMED_GRAPHS, bind_prefixes
from compliance_engine.pipeline.backends.base import BackendUnavailable
from compliance_engine.pipeline.dataset import triples_by_graph
from compliance_engine.pipeline.registry import content_hash

_DEFAULT_STORE_ROOT = Path(__file__).resolve().parent.parent.parent / "output" / "flexo"
_DEFAULT_PROJECT = "compliance-engine"
_DEFAULT_REF = "main"

# Env var that selects a live remote Flexo endpoint. When unset, the
# backend runs entirely on a local FakeFlexoStore (offline).
_ENDPOINT_ENV = "FLEXO_ENDPOINT"


def _canonical_ntriples(graph: Graph) -> bytes:
    """Serialize a graph to sorted N-Triples bytes (deterministic).

    N-Triples has a stable one-triple-per-line grammar; sorting the lines
    removes rdflib's iteration-order nondeterminism so identical triple
    sets always hash to the same value. Blank nodes are rare in this
    engine's named graphs; when present their skolem ids are preserved as
    emitted, which is acceptable for the demo simulation.
    """
    text = graph.serialize(format="nt")
    lines = sorted(line for line in text.splitlines() if line.strip())
    return ("\n".join(lines) + "\n").encode("utf-8")


class FakeFlexoStore:
    """Deterministic local-filesystem simulation of Flexo MMS.

    Commits are stored under ``root`` keyed by ``(project, ref)``. Each
    ``commit`` APPENDS a new immutable version and never overwrites a
    prior one, mirroring Flexo's append-only commit history. A version id
    is the SHA-256 of the commit's sorted per-graph content hashes, so it
    is content-addressed and consistent with ``registry.content_hash``.

    On-disk layout::

        <root>/<project>/<ref>/history.json          ordered version ids
        <root>/<project>/<ref>/commits/<version>.json commit manifest
        <root>/<project>/<ref>/objects/<hash>.nt      canonical graph bytes

    Graph bytes are shared (content-addressed) across commits, so an
    unchanged graph is stored once even if committed in many versions.
    """

    def __init__(self, root: str | Path, project: str = _DEFAULT_PROJECT) -> None:
        self.root = Path(root)
        self.project = project
        self.root.mkdir(parents=True, exist_ok=True)

    # -- paths --------------------------------------------------------------

    def _ref_dir(self, ref: str) -> Path:
        return self.root / self.project / ref

    def _history_path(self, ref: str) -> Path:
        return self._ref_dir(ref) / "history.json"

    def _commit_path(self, ref: str, version_id: str) -> Path:
        return self._ref_dir(ref) / "commits" / f"{version_id}.json"

    def _object_path(self, ref: str, hash_: str) -> Path:
        return self._ref_dir(ref) / "objects" / f"{hash_}.nt"

    # -- history ------------------------------------------------------------

    def _read_history(self, ref: str) -> list[str]:
        path = self._history_path(ref)
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_history(self, ref: str, history: list[str]) -> None:
        path = self._history_path(ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(history), encoding="utf-8")
        tmp.replace(path)

    def history(self, ref: str) -> list[str]:
        """Ordered list of version ids for ``ref`` (oldest first)."""
        return self._read_history(ref)

    # -- commit / resolve ---------------------------------------------------

    def commit(self, ref: str, named_graphs: dict[str, Graph]) -> str:
        """Append an immutable commit of ``named_graphs`` to ``ref``.

        ``named_graphs`` maps a graph IRI (str) to the rdflib Graph whose
        triples make up that named graph for this commit. Returns the new
        version id. Appends to the ref's history; earlier versions remain
        resolvable unchanged. Re-committing identical content yields the
        same content-addressed version id and appends it again (Flexo
        records an empty-diff commit rather than overwriting).
        """
        ref_dir = self._ref_dir(ref)
        (ref_dir / "commits").mkdir(parents=True, exist_ok=True)
        (ref_dir / "objects").mkdir(parents=True, exist_ok=True)

        graph_hashes: dict[str, str] = {}
        for iri, graph in named_graphs.items():
            payload = _canonical_ntriples(graph)
            h = content_hash(payload)
            obj_path = self._object_path(ref, h)
            if not obj_path.exists():
                tmp = obj_path.with_name(obj_path.name + ".tmp")
                tmp.write_bytes(payload)
                tmp.replace(obj_path)  # atomic, write-once object
            graph_hashes[iri] = h

        # Version id: content hash of the sorted per-graph hashes. Stable
        # and deterministic for identical content across runs / machines.
        manifest = {
            "project": self.project,
            "ref": ref,
            "graphs": dict(sorted(graph_hashes.items())),
        }
        manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
        version_id = content_hash(manifest_bytes)

        commit_path = self._commit_path(ref, version_id)
        if not commit_path.exists():
            tmp = commit_path.with_name(commit_path.name + ".tmp")
            tmp.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
            tmp.replace(commit_path)

        history = self._read_history(ref)
        history.append(version_id)
        self._write_history(ref, history)
        return version_id

    def resolve(self, ref: str, version: str | None = None) -> dict[str, Graph]:
        """Return the named graphs at ``version`` (latest if ``version`` is None).

        Reconstructs each named graph from its content-addressed bytes, so
        an earlier version resolves to exactly the triples committed then —
        immutability of prior versions is guaranteed by content addressing.
        """
        history = self._read_history(ref)
        if not history:
            raise KeyError(f"ref {ref!r} has no commits in project {self.project!r}")
        if version is None:
            version = history[-1]
        elif version not in history:
            raise KeyError(f"version {version!r} not found on ref {ref!r}")

        manifest = json.loads(
            self._commit_path(ref, version).read_text(encoding="utf-8")
        )
        graphs: dict[str, Graph] = {}
        for iri, h in manifest["graphs"].items():
            g = Graph(identifier=URIRef(iri))
            payload = self._object_path(ref, h).read_bytes()
            if payload.strip():
                g.parse(data=payload.decode("utf-8"), format="nt")
            graphs[iri] = g
        return graphs

    def graph_hash(self, ref: str, iri: str, version: str | None = None) -> str | None:
        """Content hash recorded for named graph ``iri`` at ``version``.

        Returns None if the graph is absent from that commit. Exposed so
        callers (and tests) can assert content-addressing stability without
        re-parsing the graph.
        """
        history = self._read_history(ref)
        if not history:
            return None
        version = version or history[-1]
        manifest = json.loads(
            self._commit_path(ref, version).read_text(encoding="utf-8")
        )
        return manifest["graphs"].get(iri)

    # -- raw object store (Registry write-through/read-through tier) --------
    #
    # Separate from the graph-commit `objects/<ref>/objects/<hash>.nt` path
    # above: this is a plain content-addressed blob store (BOM bytes, artifact
    # bytes), not a named-graph snapshot. Kept in its own `_registry_objects`
    # ref so registry blobs never mix into named-graph commit history.

    _REGISTRY_REF = "_registry_objects"

    def _registry_object_path(self, hash_: str) -> Path:
        return self._ref_dir(self._REGISTRY_REF) / "objects" / hash_

    def put_object(self, content: bytes) -> str:
        """Write-once content-addressed blob storage. Returns the SHA-256 hex key."""
        h = content_hash(content)
        path = self._registry_object_path(h)
        if path.exists():
            if path.read_bytes() != content:
                raise ValueError(
                    f"object {h} exists in Flexo registry tier with different "
                    f"bytes (write-once violation or tampering)"
                )
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_bytes(content)
            tmp.replace(path)
        return h

    def get_object(self, hash_: str) -> bytes:
        """Return the stored bytes for ``hash_``. Raises KeyError if absent."""
        path = self._registry_object_path(hash_)
        if not path.exists():
            raise KeyError(hash_)
        return path.read_bytes()


class FlexoBackend:
    """Persist the runtime Dataset to a Flexo MMS versioned quadstore.

    Implements the ``StoreBackend`` protocol. Each ``<ce:*>`` named graph
    from the Dataset is committed to the Flexo ref for the run, so one
    ``persist`` call produces exactly one new immutable version (append-only).

    Two modes:
      - fake (default): backed by a ``FakeFlexoStore`` under ``store_root``.
        Always available, fully offline — the test / demo path.
      - real (deferred): constructed with an ``endpoint`` (or via the
        ``FLEXO_ENDPOINT`` env var). ``probe()`` issues a cheap reachability
        check and raises ``BackendUnavailable`` if the server cannot be
        reached. The live commit path is documented as deferred and is not
        exercised in this sandbox.
    """

    name = "flexo"

    def __init__(
        self,
        store_root: str | Path | None = None,
        *,
        project: str = _DEFAULT_PROJECT,
        ref: str = _DEFAULT_REF,
        endpoint: str | None = None,
        store: FakeFlexoStore | None = None,
    ) -> None:
        self.project = project
        self.ref = ref
        # A real endpoint may be passed explicitly or via the environment.
        self.endpoint = (
            endpoint if endpoint is not None else os.environ.get(_ENDPOINT_ENV)
        )

        if store is not None:
            self.store: FakeFlexoStore | None = store
        elif self.endpoint:
            # Real-endpoint mode: no local fake store is constructed.
            self.store = None
        else:
            root = Path(store_root) if store_root is not None else _DEFAULT_STORE_ROOT
            self.store = FakeFlexoStore(root, project=project)

    # -- StoreBackend protocol ---------------------------------------------

    def probe(self, output_dir: Path | None = None) -> None:
        """Preflight reachability check.

        Signature matches LocalBackend.probe (the runner calls
        ``probe(output_dir=...)`` and Registry calls ``probe(root)``);
        ``output_dir`` is accepted for parity and ignored — Flexo is a remote
        quadstore, not a file target.

        Fake-store mode is always reachable (offline). Real-endpoint mode
        performs a cheap, bounded HTTP HEAD-style GET and raises
        ``BackendUnavailable`` on any connection failure — fail-fast, never
        hangs (a short timeout is enforced).
        """
        if self.store is not None:
            # Offline simulation: verify the store root is usable.
            try:
                self.store.root.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise BackendUnavailable(
                    f"flexo fake-store root {self.store.root} is not writable: {exc}"
                ) from exc
            return

        # Real-endpoint mode (deferred). Bounded probe so failure is fast.
        try:
            req = Request(self.endpoint, method="GET")
            urlopen(req, timeout=3).close()  # noqa: S310 - configured IL4 endpoint
        except (URLError, OSError, ValueError) as exc:
            raise BackendUnavailable(
                f"flexo endpoint {self.endpoint!r} is unreachable: {exc}"
            ) from exc

    def record_uri(self, layer: str) -> URIRef | None:
        """Stable Flexo IRI for a layer's named graph.

        Maps a named-graph key (e.g. "evidence") to the graph IRI Flexo
        commits it under. Returns None for unknown layers.
        """
        iri = NAMED_GRAPHS.get(layer)
        return URIRef(iri) if iri is not None else None

    def emit_service_node(
        self, graph: Graph, hosting_org_iri: URIRef | None
    ) -> URIRef | None:
        """Emit the Flexo service node typed prov:Location + auspices edge.

        Flexo MMS is a hosted service, so it emits a stable service node and
        an ``operatedBy`` edge when the hosting org is known. Returns the
        service IRI.
        """
        from rdflib.namespace import RDF

        from compliance_engine.ontology.prefixes import PROV

        service = CE["service/flexo-mms"]
        graph.add((service, RDF.type, PROV.Location))
        if hosting_org_iri is not None:
            graph.add((service, CE["operatedBy"], hosting_org_iri))
        return service

    def persist(self, ds: Dataset, output_dir: Path) -> dict:
        """Commit each ``<ce:*>`` named graph to the Flexo ref (append-only).

        Produces exactly one new immutable version per call. ``output_dir``
        is accepted for interface parity with ``LocalBackend`` but is not
        used — Flexo is a remote quadstore, not a file target. Returns
        ``{graph_iri: triple_count}`` for the graphs persisted.
        """
        if self.store is None:
            # Live-endpoint commit path is deferred in this sandbox.
            raise BackendUnavailable(
                "flexo real-endpoint commit path is deferred; configure a "
                "FakeFlexoStore for offline persistence"
            )

        # Collect only the named graphs Flexo partitions (the eight ce: graphs),
        # skipping empty ones — mirrors triples_by_graph's populated filter.
        graph_iris = set(NAMED_GRAPHS.values())
        named_graphs: dict[str, Graph] = {}
        for ctx in ds.contexts():
            iri = str(ctx.identifier)
            if iri in graph_iris and len(ctx) > 0:
                snapshot = Graph(identifier=URIRef(iri))
                for triple in ctx:
                    snapshot.add(triple)
                named_graphs[iri] = snapshot

        self.store.commit(self.ref, named_graphs)
        return triples_by_graph(ds)

    def describe(self) -> str:
        if self.store is not None:
            return (
                f"Flexo MMS (offline FakeFlexoStore at {self.store.root}, "
                f"project={self.project}, ref={self.ref}, append-only versioned)"
            )
        return (
            f"Flexo MMS (remote endpoint {self.endpoint!r}, project={self.project}, "
            f"ref={self.ref}, append-only versioned) [live path deferred]"
        )

    # -- convenience (not part of the StoreBackend protocol) ----------------
    #
    # put_object/get_object: a narrow, separate object-store surface used by
    # Registry (pipeline/registry.py) for write-through/read-through of
    # single content-addressed blobs (BOM bytes, artifacts) — distinct from
    # persist()'s whole-Dataset named-graph snapshots above. Feature-detected
    # by Registry via hasattr; LocalBackend does not implement this surface.

    def put_object(self, content: bytes) -> str:
        """Write-once content-addressed blob storage. Returns the SHA-256 hex key."""
        if self.store is None:
            raise BackendUnavailable(
                "flexo real-endpoint object store is deferred; configure a "
                "FakeFlexoStore for offline persistence"
            )
        return self.store.put_object(content)

    def get_object(self, hash_: str) -> bytes:
        """Return the stored bytes for ``hash_``. Raises KeyError if absent."""
        if self.store is None:
            raise BackendUnavailable(
                "flexo real-endpoint object store is deferred; configure a "
                "FakeFlexoStore for offline persistence"
            )
        return self.store.get_object(hash_)

    def load(self, version: str | None = None) -> Dataset:
        """Rebuild a Dataset from a committed version (latest if None).

        Round-trip counterpart of ``persist``: reconstructs the full
        Dataset from the content-addressed named graphs in the commit.
        Fake-store mode only.
        """
        if self.store is None:
            raise BackendUnavailable(
                "flexo real-endpoint load path is deferred; configure a FakeFlexoStore"
            )
        ds = Dataset(default_union=True)
        bind_prefixes(ds)
        for iri, graph in self.store.resolve(self.ref, version).items():
            target = ds.graph(URIRef(iri))
            for triple in graph:
                target.add(triple)
        return ds
