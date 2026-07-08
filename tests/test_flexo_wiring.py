"""Integration wiring for the Flexo store backend (Phase A).

Guards the seams between FlexoBackend and the rest of the engine: factory
registration and probe-signature parity with LocalBackend (the runner calls
`probe(output_dir=...)`, the Registry calls `probe(root)` — both must work).
"""

from __future__ import annotations

import pytest

from compliance_engine.pipeline.backends.base import StoreBackend, get_backend
from compliance_engine.pipeline.backends.flexo import FlexoBackend
from compliance_engine.pipeline.backends.local import LocalBackend


def test_get_backend_registers_flexo():
    b = get_backend("flexo")
    assert isinstance(b, FlexoBackend)
    assert isinstance(b, StoreBackend)
    assert b.name == "flexo"


def test_probe_signature_parity_with_local(tmp_path):
    # The runner calls store_backend.probe(output_dir=...); the Registry calls
    # backend.probe(root) positionally. Both backends must accept both forms.
    LocalBackend().probe(output_dir=tmp_path)
    FlexoBackend(store_root=tmp_path / "a").probe(output_dir=tmp_path)
    FlexoBackend(store_root=tmp_path / "b").probe(tmp_path)  # positional


def test_flexo_persist_is_append_only_across_runs(tmp_path):
    from rdflib import Dataset, Literal, URIRef

    from compliance_engine.ontology.prefixes import NAMED_GRAPHS

    ev_iri = URIRef(NAMED_GRAPHS["evidence"])
    b = FlexoBackend(store_root=tmp_path / "store", ref="NV012")

    ds1 = Dataset()
    ds1.graph(ev_iri).add((URIRef("urn:s"), URIRef("urn:p"), Literal("v1")))
    b.persist(ds1, tmp_path)

    ds2 = Dataset()
    ds2.graph(ev_iri).add((URIRef("urn:s"), URIRef("urn:p"), Literal("v2")))
    b.persist(ds2, tmp_path)

    assert b.store is not None
    versions = b.store.history("NV012")
    assert len(versions) == 2  # append-only: two retained versions
    # The earlier version is still resolvable unchanged.
    first = b.store.resolve("NV012", versions[0])
    triples = {str(o) for g in first.values() for _, _, o in g}
    assert "v1" in triples


def test_put_object_get_object_round_trip(tmp_path):
    b = FlexoBackend(store_root=tmp_path / "store", ref="NV012")
    h = b.put_object(b"bom-bytes")
    assert b.get_object(h) == b"bom-bytes"


def test_put_object_is_write_once_idempotent_on_same_content(tmp_path):
    b = FlexoBackend(store_root=tmp_path / "store", ref="NV012")
    h1 = b.put_object(b"same")
    h2 = b.put_object(b"same")
    assert h1 == h2
    assert b.get_object(h1) == b"same"


def test_put_object_rejects_mismatched_content_at_same_hash(tmp_path):
    b = FlexoBackend(store_root=tmp_path / "store", ref="NV012")
    h = b.put_object(b"original")
    assert b.store is not None
    # Force a hash-key mismatch by writing different bytes directly under the
    # same key, simulating tampering/write-once violation.
    path = b.store._registry_object_path(h)  # noqa: SLF001 - white-box tamper
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError):
        b.put_object(b"original")


def test_get_object_missing_raises_keyerror(tmp_path):
    b = FlexoBackend(store_root=tmp_path / "store", ref="NV012")
    with pytest.raises(KeyError):
        b.get_object("0" * 64)


def test_registry_objects_kept_separate_from_graph_commit_history(tmp_path):
    from rdflib import Dataset, Literal, URIRef

    from compliance_engine.ontology.prefixes import NAMED_GRAPHS

    ev_iri = URIRef(NAMED_GRAPHS["evidence"])
    b = FlexoBackend(store_root=tmp_path / "store", ref="NV012")
    h = b.put_object(b"registry-blob")

    ds = Dataset()
    ds.graph(ev_iri).add((URIRef("urn:s"), URIRef("urn:p"), Literal("v")))
    b.persist(ds, tmp_path)

    assert b.store is not None
    # The registry-object blob is not part of the "NV012" ref's own commit
    # history (append-only graph snapshots) — it lives under the separate
    # _registry_objects namespace and is unaffected by dataset persists.
    assert b.store.history("NV012") != []
    assert b.get_object(h) == b"registry-blob"
