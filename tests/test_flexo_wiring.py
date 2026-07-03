"""Integration wiring for the Flexo store backend (Phase A).

Guards the seams between FlexoBackend and the rest of the engine: factory
registration and probe-signature parity with LocalBackend (the runner calls
`probe(output_dir=...)`, the Registry calls `probe(root)` — both must work).
"""

from __future__ import annotations

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
