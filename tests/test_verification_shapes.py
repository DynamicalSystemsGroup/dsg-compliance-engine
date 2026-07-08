"""verification.py: SHACL closure suite + evidence re-hashing.

Builds tiny in-memory fixture graphs (no pipeline). Exercises:
  - a `passed` attestation missing adequacy/sufficiency fails the suite;
  - R13: MET over a failed oracle without override fails ContradictionShape,
    and adding the override clears it (full conformance);
  - re-verification re-hashes each ce:Evidence node and flags a byte mismatch.
"""
from __future__ import annotations

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import RDF

from compliance_engine.ontology.prefixes import CE, CMMC, EARL, GSN, PROV
from compliance_engine.traceability.attestation import (
    PLAN_STANDARD_PROCEDURE,
    ROLE_AFFIRMING_OFFICIAL,
)
from compliance_engine.traceability.verification import verify, verify_reverification
from compliance_engine.pipeline.evidence.hashing import hash_config_export, hash_evidence

_CONTROL = CMMC["AC.L2-3.1.1"]


def _passed_attestation(
    g: Graph, *, adequacy: bool = True, sufficiency: bool = True,
    oracle_failed: bool = False, override: bool = False,
) -> URIRef:
    """Hand-build a MET (earl:passed) ce:Attestation with controllable parts."""
    att = CE["ATT-fixture"]
    g.add((att, RDF.type, CE.Attestation))
    g.add((att, RDF.type, PROV.Activity))
    g.add((att, CE.attests, _CONTROL))
    g.add((att, CE.hasOutcome, EARL.passed))
    g.add((att, PROV.wasAssociatedWith, CE["official-x"]))
    assoc = BNode()
    g.add((att, PROV.qualifiedAssociation, assoc))
    g.add((assoc, RDF.type, PROV.Association))
    g.add((assoc, PROV.agent, CE["official-x"]))
    g.add((assoc, PROV.hadRole, ROLE_AFFIRMING_OFFICIAL))
    g.add((assoc, PROV.hadPlan, PLAN_STANDARD_PROCEDURE))
    if adequacy:
        a = CE["adequacy/ATT-fixture"]
        g.add((a, RDF.type, GSN.Assumption))
        g.add((a, GSN.statement, Literal("implementation is adequate")))
        g.add((att, GSN.inContextOf, a))
    if sufficiency:
        s = CE["sufficiency/ATT-fixture"]
        g.add((s, RDF.type, GSN.Justification))
        g.add((s, GSN.statement, Literal("evidence is sufficient to mark MET")))
        g.add((att, GSN.inContextOf, s))
    if oracle_failed:
        g.add((att, CE.oracleOutcome, EARL.failed))
    if override:
        g.add((att, CMMC.overrideJustification, Literal("risk accepted; documented")))
        g.add((att, CE.overrideEvidence, Literal("override-evidence-artifact-hash")))
    return att


# ---------------------------------------------------------------------------
# Missing adequacy / sufficiency -> suite fails
# ---------------------------------------------------------------------------

def test_missing_adequacy_fails_suite():
    g = Graph()
    _passed_attestation(g, adequacy=False)
    report = verify(g, skip_reverification=True)
    assert not report.conforms
    assert "AttestationShape" in report.shapes_named() or "adequacy" in report.shape_results_text


def test_missing_sufficiency_fails_suite():
    g = Graph()
    _passed_attestation(g, sufficiency=False)
    report = verify(g, skip_reverification=True)
    assert not report.conforms


def test_well_formed_passed_attestation_conforms():
    g = Graph()
    _passed_attestation(g)
    report = verify(g, skip_reverification=True)
    assert report.conforms, report.summary_lines()


# ---------------------------------------------------------------------------
# R13 ContradictionShape
# ---------------------------------------------------------------------------

def test_met_over_failed_oracle_without_override_fails():
    g = Graph()
    _passed_attestation(g, oracle_failed=True, override=False)
    report = verify(g, skip_reverification=True)
    assert not report.conforms
    assert "Contradiction (R13)" in report.shape_results_text


def test_override_clears_contradiction():
    g = Graph()
    _passed_attestation(g, oracle_failed=True, override=True)
    report = verify(g, skip_reverification=True)
    assert "Contradiction (R13)" not in report.shape_results_text
    assert report.conforms, report.summary_lines()


# ---------------------------------------------------------------------------
# KI-8: OverrideEvidenceShape, extracted as a standalone shape referenced
# from ContradictionShape via sh:node (not merged — see resolution note).
# ---------------------------------------------------------------------------

def test_override_justification_without_evidence_violates_standalone_shape():
    # No oracle failure at all — not a contradiction — but a justification with
    # no appended evidence. Proves OverrideEvidenceShape is genuinely reusable
    # and fires independent of the R13 contradiction condition.
    g = Graph()
    att = _passed_attestation(g, oracle_failed=False, override=False)
    g.add((att, CMMC.overrideJustification, Literal("risk accepted, no evidence yet")))
    report = verify(g, skip_reverification=True)
    assert not report.conforms
    assert "OverrideEvidenceShape" in report.shape_results_text
    assert "Contradiction (R13)" not in report.shape_results_text


def test_override_justification_with_evidence_conforms_standalone():
    g = Graph()
    att = _passed_attestation(g, oracle_failed=False, override=False)
    g.add((att, CMMC.overrideJustification, Literal("risk accepted; documented")))
    g.add((att, CE.overrideEvidence, Literal("override-evidence-artifact-hash")))
    report = verify(g, skip_reverification=True)
    assert report.conforms, report.summary_lines()


# ---------------------------------------------------------------------------
# Re-verification (evidence re-hashing)
# ---------------------------------------------------------------------------

def _evidence_node(g: Graph, model_hash: str, content_hash: str) -> URIRef:
    ev = CE["evidence/EV-1"]
    g.add((ev, RDF.type, CE.Evidence))
    g.add((ev, CE.modelHash, Literal(model_hash)))
    g.add((ev, CE.contentHash, Literal(content_hash)))
    return ev


def test_reverification_passes_for_consistent_hash_chain():
    g = Graph()
    model = hash_config_export("gcp.kms", "SC.L2-3.13.16", {"cui_encrypted_at_rest": True})
    content = hash_evidence(model)  # the binding.py chain
    _evidence_node(g, model, content)
    assert verify_reverification(g) == []


def test_reverification_flags_content_mismatch():
    g = Graph()
    model = hash_config_export("gcp.kms", "SC.L2-3.13.16", {"cui_encrypted_at_rest": True})
    content = hash_evidence(model)
    ev = _evidence_node(g, model, content)
    # Mutate the node's bytes: change the modelHash so content no longer matches.
    g.remove((ev, CE.modelHash, Literal(model)))
    g.add((ev, CE.modelHash, Literal(model + "TAMPERED")))
    mismatches = verify_reverification(g)
    assert len(mismatches) == 1
    assert mismatches[0].evidence == str(ev)
    assert mismatches[0].expected == content
    assert mismatches[0].actual == hash_evidence(model + "TAMPERED")


def test_verify_end_to_end_flags_mismatch_in_report():
    g = Graph()
    model = "deadbeef"
    content = hash_evidence(model)
    ev = _evidence_node(g, model, content)
    # tamper
    g.remove((ev, CE.contentHash, Literal(content)))
    g.add((ev, CE.contentHash, Literal("0" * 64)))
    report = verify(g)
    assert report.reverification_mismatches
    assert not report.conforms
