"""StoreBackend protocol and factory."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from rdflib import Dataset, Graph, URIRef


class BackendUnavailable(RuntimeError):
    """Preflight probe detected the backend is unreachable / misconfigured.

    Raised by `StoreBackend.probe()`. The runner catches this at startup,
    prints the backend's `describe()` output + the cause, and exits
    with a non-zero code — the integration story must not silently
    degrade.
    """


@runtime_checkable
class StoreBackend(Protocol):
    """Persistence target for the runtime compliance-engine Dataset.

    Implementations:
      - LocalBackend  (default): writes .ttl + .trig files to a directory

    The runtime always builds the Dataset locally first. The backend is
    invoked at the end of the pipeline to persist results.
    """

    name: str

    def probe(self) -> None:
        """Preflight reachability check; raise BackendUnavailable on failure.

        Called by the runner before the first stage so failure is fast and
        clear rather than discovered at the last stage. Implementations
        should be cheap (target seconds, not minutes) and report concrete
        causes (HTTP status, missing path, missing credentials).
        """
        ...

    def record_uri(self, layer: str) -> URIRef | None:
        """Stable IRI for the location where this layer's graph lives.

        `layer` is a named-graph key from compliance_engine.ontology.prefixes.NAMED_GRAPHS
        (e.g. "evidence", "attestations"); the implementation may map
        it to the backend-specific identifier.

        Implementations:
          - LocalBackend  : returns None (no remote IRI)
        """
        ...

    def emit_service_node(self, graph: Graph, hosting_org_iri: URIRef | None) -> URIRef | None:
        """Emit this backend's service node + per-service auspices edge.

        Hosted services emit a stable service node typed prov:Location
        plus an `operatedBy` edge when the hosting org is known. Returns
        the service IRI, or None for backends that are not hosted
        services:

          - LocalBackend  : returns None (local filesystem)
        """
        ...

    def persist(self, ds: Dataset, output_dir: Path) -> dict:
        """Push `ds` to the persistence target.

        Returns a dict of {graph_iri: count_of_triples_persisted} for
        reporting / verification. `output_dir` is used by LocalBackend
        for file outputs; other backends may ignore it (but should still
        return the per-graph counts).
        """
        ...

    def describe(self) -> str:
        """Single-line human description for the Stage-0 narrative banner
        (e.g. 'Local filesystem at /path/to/output')."""
        ...


def get_backend(name: str, **kwargs) -> StoreBackend:
    """Backend factory. Imports lazily so backend-specific dependencies
    aren't loaded when not needed."""
    if name == "local":
        from compliance_engine.pipeline.backends.local import LocalBackend
        return LocalBackend(**kwargs)
    if name == "flexo":
        from compliance_engine.pipeline.backends.flexo import FlexoBackend
        return FlexoBackend(**kwargs)
    raise ValueError(f"Unknown backend {name!r}. Choose: local, flexo")
