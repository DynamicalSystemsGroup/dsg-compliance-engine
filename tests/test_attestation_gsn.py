"""U9 — Gate-2 attestation onto GSN nodes (ported from ADCS test_attestation_gsn).

Confirms request_attestation emits a well-formed ce:Attestation: ce:attests +
adequacy gsn:Assumption + sufficiency gsn:Justification + prov:qualifiedAssociation
(Affirming Official) + EARL outcome + the backing-oracle link. Keeps the declined
(NOT MET) case. Builds its own tiny fixture Dataset — no pipeline.runner.
"""
from __future__ import annotations

from unittest.mock import patch

from rdflib import Dataset, Literal, URIRef
from rdflib.namespace import RDF, XSD
from rdflib.compare import isomorphic, to_canonical_graph

from ontology.prefixes import CE, CMMC, EARL, GSN, PROV, G_ATTESTATIONS, G_AUDIT
from oracles.criteria import evaluate
from oracles.assertion import emit_control_check_assertion
from traceability.attestation import (
    OUTCOME_FAILED,
    OUTCOME_PASSED,
    PLAN_STANDARD_PROCEDURE,
    ROLE_AFFIRMING_OFFICIAL,
    STATUS_LABEL,
    request_attestation,
)

_CONTROL = "IA.L2-3.5.3"


def _fixture_with_oracle(outcome_summary: dict) -> tuple[Dataset, URIRef]:
    """Dataset with one U7 ControlCheckAssertion in <ce:audit>. Returns (ds, assertion)."""
    ds = Dataset(default_union=True)
    result = evaluate(outcome_summary, _CONTROL)
    evidence = CE["evidence/EV-mfa"]
    assertion = emit_control_check_assertion(
        ds, evidence, CMMC[_CONTROL], result, now_iso="2026-07-02T00:00:00+00:00"
    )
    return ds, assertion


def _att_graph(ds: Dataset):
    return ds.graph(URIRef(G_ATTESTATIONS))


# ---------------------------------------------------------------------------
# Happy path — MET attestation, fully well-formed
# ---------------------------------------------------------------------------

def _attest_met():
    ds, assertion = _fixture_with_oracle({"mfa_enforced_privileged": True})
    att = request_attestation(
        ds, _CONTROL, "Jane Official",
        auto_attest=True,
        adequacy="MFA is enforced on all privileged accounts via 2SV.",
        sufficiency="Config export + oracle PASS are sufficient to mark MET.",
        outcome=OUTCOME_PASSED,
        backing_oracle=assertion,
    )
    return ds, att, assertion


def test_attests_the_control():
    ds, att, _ = _attest_met()
    g = _att_graph(ds)
    assert (att, CE.attests, CMMC[_CONTROL]) in g


def test_has_adequacy_assumption():
    ds, att, _ = _attest_met()
    g = _att_graph(ds)
    adequacy = CE[f"adequacy/ATT-{_CONTROL}"]
    assert (att, GSN.inContextOf, adequacy) in g
    assert (adequacy, RDF.type, GSN.Assumption) in g
    statements = list(g.objects(adequacy, GSN.statement))
    assert statements and str(statements[0]).strip()


def test_has_sufficiency_justification():
    ds, att, _ = _attest_met()
    g = _att_graph(ds)
    sufficiency = CE[f"sufficiency/ATT-{_CONTROL}"]
    assert (att, GSN.inContextOf, sufficiency) in g
    assert (sufficiency, RDF.type, GSN.Justification) in g
    statements = list(g.objects(sufficiency, GSN.statement))
    assert statements and str(statements[0]).strip()


def test_outcome_is_earl_passed():
    ds, att, _ = _attest_met()
    g = _att_graph(ds)
    assert list(g.objects(att, CE.hasOutcome)) == [OUTCOME_PASSED]
    assert STATUS_LABEL[OUTCOME_PASSED] == "MET"


def test_mode_is_semi_auto():
    ds, att, _ = _attest_met()
    g = _att_graph(ds)
    assert list(g.objects(att, CE.attestationMode)) == [EARL.semiAuto]


def test_qualified_association_affirming_official():
    ds, att, _ = _attest_met()
    g = _att_graph(ds)
    assocs = list(g.objects(att, PROV.qualifiedAssociation))
    assert len(assocs) == 1
    assoc = assocs[0]
    assert ROLE_AFFIRMING_OFFICIAL in list(g.objects(assoc, PROV.hadRole))
    assert PLAN_STANDARD_PROCEDURE in list(g.objects(assoc, PROV.hadPlan))


def test_backing_oracle_link():
    ds, att, assertion = _attest_met()
    g = _att_graph(ds)
    # provenance pointer to the U7 assertion + the resolved oracle outcome
    assert (att, CE.backedBy, assertion) in g
    assert list(g.objects(att, CE.oracleOutcome)) == [EARL.passed]


def test_oracle_assertion_never_attests():
    # Regression: ce:attests lives only in attestation, never on the oracle side.
    ds, _att, assertion = _attest_met()
    audit = ds.graph(URIRef(G_AUDIT))
    assert (assertion, CE.evaluatesAgainst, CMMC[_CONTROL]) in audit
    assert not list(audit.triples((assertion, CE.attests, None)))


# ---------------------------------------------------------------------------
# Declined (NOT MET) — still well-formed
# ---------------------------------------------------------------------------

def test_declined_not_met_is_well_formed():
    ds, assertion = _fixture_with_oracle({"mfa_enforced_privileged": False})
    att = request_attestation(
        ds, _CONTROL, "Jane Official",
        auto_attest=True,
        adequacy="MFA is only enforced for remote users; local privileged gap.",
        sufficiency="Evidence shows the control is NOT satisfied; gap remains.",
        outcome=OUTCOME_FAILED,
        backing_oracle=assertion,
    )
    g = _att_graph(ds)
    assert list(g.objects(att, CE.hasOutcome)) == [OUTCOME_FAILED]
    assert STATUS_LABEL[OUTCOME_FAILED] == "NOT MET"
    # still carries adequacy + sufficiency + attests (well-formed decline)
    assert (att, CE.attests, CMMC[_CONTROL]) in g
    assert (CE[f"adequacy/ATT-{_CONTROL}"], RDF.type, GSN.Assumption) in g
    assert (CE[f"sufficiency/ATT-{_CONTROL}"], RDF.type, GSN.Justification) in g


def test_interactive_decline_on_adequacy_yields_failed():
    ds = Dataset(default_union=True)
    with patch("builtins.input", side_effect=lambda prompt="": "no"):
        att = request_attestation(ds, _CONTROL, "Jane Official", auto_attest=False)
    g = _att_graph(ds)
    assert list(g.objects(att, CE.hasOutcome)) == [OUTCOME_FAILED]


def test_auto_attest_requires_judgement_text():
    ds = Dataset(default_union=True)
    import pytest
    with pytest.raises(ValueError):
        request_attestation(ds, _CONTROL, "Jane Official", auto_attest=True)


# ---------------------------------------------------------------------------
# Injectable timestamp — byte-stable SSP (Round-10 fix)
# ---------------------------------------------------------------------------

_NOW = "2026-07-02T00:00:00+00:00"


def _attestations_graph(now):
    """Return the <ce:attestations> graph for one MET attestation stamped `now`."""
    ds, assertion = _fixture_with_oracle({"mfa_enforced_privileged": True})
    request_attestation(
        ds, _CONTROL, "Jane Official", auto_attest=True,
        adequacy="MFA is enforced on all privileged accounts via 2SV.",
        sufficiency="Config export + oracle PASS are sufficient to mark MET.",
        outcome=OUTCOME_PASSED, backing_oracle=assertion, now=now,
    )
    return _att_graph(ds)


def test_now_sets_generated_at_time_verbatim():
    g = _attestations_graph(_NOW)
    att = next(g.subjects(RDF.type, CE.Attestation))
    assert list(g.objects(att, PROV.generatedAtTime)) == [
        Literal(_NOW, datatype=XSD.dateTime)
    ]


def test_same_now_yields_byte_identical_attestation_triples():
    # Two independent runs with the same `now` → byte-identical serialization
    # (blank nodes canonicalised so the qualifiedAssociation node can't drift).
    g1 = _attestations_graph(_NOW)
    g2 = _attestations_graph(_NOW)
    # Canonicalise blank nodes, then compare SORTED lines: rdflib's N-Triples
    # serializer stabilises blank-node labels via to_canonical_graph but does not
    # guarantee triple *line order* across independent builds, so sort before
    # comparing (matches how documents/ssp.py fingerprints over sorted quads).
    def _canon_lines(g):
        nt = to_canonical_graph(g).serialize(format="nt", encoding="utf-8")
        return sorted(nt.splitlines())
    assert _canon_lines(g1) == _canon_lines(g2)


def test_different_now_changes_the_subgraph():
    # Proves the timestamp is actually captured (not ignored).
    g1 = _attestations_graph(_NOW)
    g2 = _attestations_graph("2026-09-09T09:09:09+00:00")
    assert not isomorphic(g1, g2)


def test_omitting_now_is_backward_compatible():
    # No `now` → still emits a valid xsd:dateTime generatedAtTime (wall clock).
    g = _attestations_graph(None)
    att = next(g.subjects(RDF.type, CE.Attestation))
    stamps = list(g.objects(att, PROV.generatedAtTime))
    assert len(stamps) == 1
    assert stamps[0].datatype == XSD.dateTime
    assert str(stamps[0])  # non-empty timestamp present
