"""Override-requires-evidence rule + the evidence-backing column (Phase D).

An Affirming Official may overrule a FAILED machine check, but a written
justification alone is not enough: the override must carry concrete, appended
evidence. Enforced at the write path (ValueError) and in the audit (a
justification without evidence does NOT clear the R13 contradiction).
"""

from __future__ import annotations

import pytest
from rdflib import Dataset, Literal, URIRef
from rdflib.namespace import RDF

from compliance_engine.ontology.prefixes import CE, CMMC, EARL, G_ATTESTATIONS
from compliance_engine.pipeline.dataset import create_dataset
from compliance_engine.traceability import audit as auditmod
from compliance_engine.traceability.attestation import request_attestation
from compliance_engine.traceability.bom import ControlMappingRow


def test_write_path_rejects_override_without_evidence():
    ds = create_dataset()
    with pytest.raises(ValueError, match="override_evidence"):
        request_attestation(
            ds, "IA.L2-3.5.3", "Jane Official", auto_attest=True,
            adequacy="Compensating control asserted.", sufficiency="Deemed MET.",
            outcome=EARL.passed, oracle_outcome=EARL.failed,
            override_justification="risk accepted; documented",
            override_evidence=None,
        )


def test_write_path_accepts_override_with_evidence():
    ds = create_dataset()
    att = request_attestation(
        ds, "IA.L2-3.5.3", "Jane Official", auto_attest=True,
        adequacy="Compensating control asserted.", sufficiency="Deemed MET.",
        outcome=EARL.passed, oracle_outcome=EARL.failed,
        override_justification="risk accepted; documented",
        override_evidence="artifact-sha256:compensating-policy-export",
    )
    g = ds.graph(URIRef(G_ATTESTATIONS))
    assert list(g.objects(att, CE.overrideEvidence)), "override evidence not emitted"


def _met_over_failed(ds, cid, *, justification=None, evidence=None):
    g = ds.graph(URIRef(G_ATTESTATIONS))
    att = CE[f"ATT-{cid}"]
    g.add((att, RDF.type, CE.Attestation))
    g.add((att, CE.attests, CMMC[cid]))
    g.add((att, CE.hasOutcome, EARL.passed))
    g.add((att, CE.oracleOutcome, EARL.failed))
    if justification:
        g.add((att, CMMC.overrideJustification, Literal(justification)))
    if evidence:
        g.add((att, CE.overrideEvidence, Literal(evidence)))
    return att


def test_audit_flags_override_without_evidence_as_contradiction():
    ds = create_dataset()
    _met_over_failed(ds, "IA.L2-3.5.3", justification="risk accepted", evidence=None)
    rows, _split = auditmod.contradictions_and_split(ds)
    assert len(rows) == 1  # justification alone does not clear it


def test_audit_clears_override_with_evidence():
    ds = create_dataset()
    _met_over_failed(
        ds, "IA.L2-3.5.3", justification="risk accepted",
        evidence="artifact-sha256:compensating-policy-export",
    )
    rows, _split = auditmod.contradictions_and_split(ds)
    assert rows == []  # justification + evidence clears the contradiction


@pytest.mark.parametrize("oracle,attest,evidence,expected", [
    ("passed", "passed", ("h1",), "machine"),
    ("failed", "passed", ("h1",), "override"),
    ("needsAction", "passed", (), "human-only"),
    (None, "passed", (), "human-only"),
])
def test_evidence_backing_property(oracle, attest, evidence, expected):
    row = ControlMappingRow(
        control_id="IA.L2-3.5.3",
        resource_ids=(),
        evidence_hashes=evidence,
        oracle_outcome=oracle,
        attestation_outcome=attest,
        status="MET",
    )
    assert row.evidence_backing == expected


# ---------------------------------------------------------------------------
# KI-7: same override-requires-evidence rule, enforced at the store-record
# level (traceability.attestation_store.AttestationRecord), not just at the
# request_attestation() write path above.
# ---------------------------------------------------------------------------

from compliance_engine.traceability.attestation_store import (  # noqa: E402
    AttestationRecord,
    AttestationStoreError,
    _record_from_obj,
)

_REC_BASE = dict(
    id="att-override-test",
    signer="Jane Official",
    signer_role="Role_AffirmingOfficial",
    signed_at="2026-07-01T12:00:00+00:00",
    covers=("ref-x",),
    controls_attested=("IA.L2-3.5.3",),
    outcome="passed",
    adequacy="Compensating control asserted.",
    sufficiency="Deemed MET.",
)


def test_attestation_record_rejects_override_without_evidence():
    with pytest.raises(AttestationStoreError, match="override_evidence"):
        AttestationRecord(
            **_REC_BASE,
            override_justification="risk accepted; documented",
            override_evidence=None,
        )


def test_attestation_record_accepts_override_with_evidence():
    rec = AttestationRecord(
        **_REC_BASE,
        override_justification="risk accepted; documented",
        override_evidence="artifact-sha256:compensating-policy-export",
    )
    assert rec.override_justification == "risk accepted; documented"
    assert rec.override_evidence == "artifact-sha256:compensating-policy-export"


def test_attestation_record_omitting_both_override_fields_still_works():
    # The common case (all real tier1.jsonl records today): no override at all.
    rec = AttestationRecord(**_REC_BASE)
    assert rec.override_justification is None
    assert rec.override_evidence is None


def test_attestation_record_parses_override_fields_from_jsonl():
    obj = dict(_REC_BASE)
    obj["override_justification"] = "risk accepted; documented"
    obj["override_evidence"] = "artifact-sha256:compensating-policy-export"
    rec = _record_from_obj(obj, path="test.jsonl", lineno=1)
    assert rec.override_justification == "risk accepted; documented"
    assert rec.override_evidence == "artifact-sha256:compensating-policy-export"
