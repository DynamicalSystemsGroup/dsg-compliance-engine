"""BOM assembly + hash-reference into the registry."""

from pathlib import Path

import pytest

from pathlib import Path

from compliance_engine.order_compiler import compiler
from compliance_engine.order_compiler import cop
from rdflib import Literal
from rdflib.namespace import RDF

from compliance_engine.ontology.prefixes import CE, CMMC
from compliance_engine.pipeline.backends.local import LocalBackend
from compliance_engine.pipeline.dataset import create_dataset, graph_for, load_into
from compliance_engine.pipeline.provision import FakeProvisionBackend
from compliance_engine.pipeline.provision.base import PlanResult, PlannedResource
from compliance_engine.pipeline.registry import ContentMismatch, Registry, content_hash
from compliance_engine.pipeline.runner import run_factory
from compliance_engine.pipeline.state import (
    ApplyStageResult,
    EvidenceStageResult,
    FetchResult,
    LoadOrderResult,
    OracleStageResult,
    PipelineState,
    PlanStageResult,
    PolicyCheckResult,
)
from compliance_engine.traceability import bom as bommod
from compliance_engine.traceability.attestation import OUTCOME_PASSED, request_attestation

CATALOG = Path(__file__).resolve().parent.parent / "data" / "ontology" / "cmmc-edit.ttl"
NOW = "2026-07-02T00:00:00+00:00"
# ---------------------------------------------------------------------------
# Real Factory state (rich: real evidence + oracle outcomes + attestations)
# ---------------------------------------------------------------------------

def _factory_state(attest: list[str] | None = None):
    ds, obl = compiler.load_pipeline_dataset()
    att = cop.attest_cop(ds, obl, auto=True, now=NOW)
    order = compiler.compile_order(ds, obl, att, now=NOW)
    state = run_factory(
        ds, order.iri, provision_backend=FakeProvisionBackend(),
        store_backend=LocalBackend(), now=NOW, run_preflight=False,
    )
    for control_id in (attest or []):
        request_attestation(ds, control_id, "Jane Official", auto_attest=True,
                            adequacy="adequate", sufficiency="sufficient",
                            outcome=OUTCOME_PASSED)
    return state, ds
# ---------------------------------------------------------------------------
# Hand-assembled mini state (controlled artifact bytes for registry tests)
# ---------------------------------------------------------------------------

_ART = {
    "order": b"order-bytes-1",
    "module": b"module-bytes-1",
    "state": b"state-bytes-1",
    "evidence": b"evidence-bytes-1",
}
OH, MH, SH, EH = (content_hash(_ART[k]) for k in ("order", "module", "state", "evidence"))
ARTIFACTS = {OH: _ART["order"], MH: _ART["module"], SH: _ART["state"], EH: _ART["evidence"]}
def _mini_state():
    ds = create_dataset()
    load_into(ds, "ontology", CATALOG)
    evg = graph_for(ds, "evidence")
    ev = CE["evidence/mini-1"]
    evg.add((ev, RDF.type, CE.Evidence))
    evg.add((ev, CE.contentHash, Literal(EH)))
    evg.add((ev, CE.resultSummary, Literal("mini evidence")))
    evg.add((ev, CE.addresses, CMMC["AC.L2-3.1.1"]))
    evg.add((ev, CE.evidentiaryStatus, Literal("mock")))

    state = PipelineState(ds=ds, provision_backend=None, store_backend=None,
                          order_iri="urn:order:mini")
    state.load_order = LoadOrderResult(
        order_iri="urn:order:mini", order_hash=OH, verified=True,
        contract="NV012", tier="Tier1", impact_level="IL4",
        standard="NIST SP 800-171 Rev 2",
        required_controls=("AC.L2-3.1.1",), included_modules=("CUI_Users_Group",),
    )
    state.fetch = FetchResult(modules_verified=True,
                              module_hashes={"CUI_Users_Group": MH})
    pr = PlanResult(plan_json={}, resources=(PlannedResource(
        resource_id="CUI_Users_Group", address="terraform_data.iam",
        type="terraform_data", controls=("AC.L2-3.1.1",), values={}, region="us-central1",
    ),))
    state.plan = PlanStageResult(plan_result=pr, resource_ids=("CUI_Users_Group",),
                                 plan_controls=("AC.L2-3.1.1",))
    state.apply = ApplyStageResult(state_hash=SH, applied=True, resource_count=1)
    state.evidence = EvidenceStageResult(evidence_node_count=1,
                                         evidence_hashes=(EH,),
                                         controls_addressed=("AC.L2-3.1.1",))
    state.oracles = OracleStageResult(outcomes={"AC.L2-3.1.1": "passed"},
                                      assertion_iris=())
    state.policy_check = PolicyCheckResult(passed=True, findings=(), oracle_outcomes={})
    return state, ds
# ---------------------------------------------------------------------------
# Happy path + determinism
# ---------------------------------------------------------------------------

def test_bom_references_every_artifact_and_hash_recomputes(tmp_path):
    state, ds = _factory_state(attest=["IA.L2-3.5.3"])
    bom = bommod.build_bom(state, ds, contract_id="NV012")

    # Recomputing the BOM hash over its canonical bytes matches (determinism).
    assert bom.compute_hash() == bom.bom_hash
    assert bommod.build_bom(state, ds, "NV012").bom_hash == bom.bom_hash

    reg = Registry(tmp_path)
    h = bommod.store_bom(bom, reg, "NV012")
    # Recomputing the BOM hash over the STORED bytes matches.
    assert content_hash(reg.get(h)) == bom.bom_hash
    # References the order, state, module, and evidence hashes.
    refs = set(bom.artifact_hashes())
    assert bom.order_hash in refs
    assert bom.state_hash in refs
    assert set(bom.module_hashes.values()) <= refs
    assert set(bom.evidence_hashes) <= refs
    assert bom.hash_reference(reg) == f"registry://{bom.bom_hash}"


def test_store_bom_signs_the_bom_and_records_it_in_the_registry(tmp_path):
    from compliance_engine.signing.signer import Ed25519LocalSigner

    state, ds = _factory_state(attest=["IA.L2-3.5.3"])
    bom = bommod.build_bom(state, ds, contract_id="NV012")

    reg = Registry(tmp_path)
    bommod.store_bom(bom, reg, "NV012")

    sig_hash = reg.bom_signature(bom.bom_hash)
    assert sig_hash is not None
    sig_bytes = reg.get(sig_hash)
    assert Ed25519LocalSigner().verify(bom.canonical_bytes(), sig_bytes)


def test_control_mapping_covers_every_required_control():
    state, ds = _factory_state()
    bom = bommod.build_bom(state, ds, "NV012")
    mapped = {r.control_id for r in bom.control_mapping}
    assert mapped == set(state.load_order.required_controls)
    assert len(bom.control_mapping) == 22


def test_to_rdf_emits_evidence_backing_per_control_mapping_row():
    state, ds = _factory_state(attest=["IA.L2-3.5.3"])
    bom = bommod.build_bom(state, ds, "NV012")

    g = bom.to_rdf()
    for row in bom.control_mapping:
        node = CE[f"BOM/{bom.bom_hash}/mapping/{row.control_id}"]
        backing_values = list(g.objects(node, CE.evidenceBacking))
        assert backing_values == [Literal(row.evidence_backing)]
# ---------------------------------------------------------------------------
# R12 — evidentiary status propagation
# ---------------------------------------------------------------------------

def test_mock_input_makes_bom_mock():
    state, ds = _factory_state()
    bom = bommod.build_bom(state, ds, "NV012")
    assert bom.evidentiary_status == "mock"
# ---------------------------------------------------------------------------
# Status is driven by the ATTESTATION, not the oracle
# ---------------------------------------------------------------------------

def test_status_requires_attestation_not_just_oracle():
    # IA.L2-3.5.3 has a passing oracle AND is attested → MET.
    # SC.L2-3.13.16 has a passing oracle but NO attestation → NOT MET.
    state, ds = _factory_state(attest=["IA.L2-3.5.3"])
    bom = bommod.build_bom(state, ds, "NV012")
    rows = {r.control_id: r for r in bom.control_mapping}

    ia = rows["IA.L2-3.5.3"]
    assert ia.oracle_outcome == "passed"
    assert ia.attestation_outcome == "passed"
    assert ia.status == "MET"

    sc = rows["SC.L2-3.13.16"]
    assert sc.oracle_outcome == "passed"      # oracle passes ...
    assert sc.attestation_outcome is None      # ... but no human attested ...
    assert sc.status == "NOT MET"              # ... so NOT MET.

    # attestations[] carries the one Gate-2 record.
    assert {a.control_id for a in bom.attestations} == {"IA.L2-3.5.3"}
    assert bom.attestations[0].role == "Affirming Official"
# ---------------------------------------------------------------------------
# Write-once / idempotent registry
# ---------------------------------------------------------------------------

def test_store_is_idempotent(tmp_path):
    state, ds = _mini_state()
    bom = bommod.build_bom(state, ds, "NV012")
    reg = Registry(tmp_path)
    h1 = bommod.store_bom(bom, reg, "NV012", artifacts=ARTIFACTS)
    h2 = bommod.store_bom(bom, reg, "NV012", artifacts=ARTIFACTS)
    assert h1 == h2 == bom.bom_hash
    # Single stored object for the BOM.
    assert reg.has(bom.bom_hash)
def test_write_once_rejects_different_bytes_under_existing_hash(tmp_path):
    state, ds = _mini_state()
    bom = bommod.build_bom(state, ds, "NV012")
    reg = Registry(tmp_path)
    bommod.store_bom(bom, reg, "NV012", artifacts=ARTIFACTS)
    # Force different bytes under the BOM's existing key → ContentMismatch.
    reg._object_path(bom.bom_hash).write_bytes(b"tampered-bom-bytes")
    with pytest.raises(ContentMismatch):
        reg.put(bom.canonical_bytes())
# ---------------------------------------------------------------------------
# Two-level index integration
# ---------------------------------------------------------------------------

def test_two_level_index_resolves_contract_to_artifacts(tmp_path):
    state, ds = _mini_state()
    bom = bommod.build_bom(state, ds, "NV012")
    reg = Registry(tmp_path)
    bom_hash = bommod.store_bom(bom, reg, "NV012", artifacts=ARTIFACTS)

    # contract_id → latest BOM hash (level 1)
    assert reg.latest_bom("NV012") == bom_hash
    # BOM hash → artifact hashes (level 2)
    arts = set(reg.bom_artifacts(bom_hash))
    assert arts == set(bom.artifact_hashes())
    assert {OH, MH, SH, EH} <= arts
# ---------------------------------------------------------------------------
# Tamper detection
# ---------------------------------------------------------------------------

def test_tampering_stored_evidence_fails_verify(tmp_path):
    state, ds = _mini_state()
    bom = bommod.build_bom(state, ds, "NV012")
    reg = Registry(tmp_path)
    bommod.store_bom(bom, reg, "NV012", artifacts=ARTIFACTS)
    assert bommod.verify_bom(bom, reg) is True

    # Mutate one stored evidence file → its bytes no longer hash to the key.
    reg._object_path(EH).write_bytes(b"tampered-evidence")
    assert reg.verify(EH) is False
    assert bommod.verify_bom(bom, reg) is False
