"""Bidirectional audit + contradiction dimension + SPRS wiring.

Built on synthetic fixture graphs (order + attestations + evidence + tier1-style
module claims + a catalog Graph for SPRS). Ports the ADCS three-failure-mode
matrix as the template.
"""
from __future__ import annotations

from rdflib import Dataset, Graph, Literal, URIRef
from rdflib.namespace import RDF

from compliance_engine.ontology.prefixes import (
    CE, CMMC, EARL,
    G_ORDER, G_STRUCTURAL, G_EVIDENCE, G_ATTESTATIONS,
)
import compliance_engine.traceability.audit as audit_mod
from compliance_engine.traceability.audit import audit, compute_sprs, render_report


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------

def _catalog(*controls: tuple[str, int]) -> Graph:
    """A catalog Graph of cmmc:Control nodes (id + weight + poamEligible=False)."""
    g = Graph()
    for cid, weight in controls:
        c = CMMC[cid]
        g.add((c, RDF.type, CMMC.Control))
        g.add((c, CMMC.controlId, Literal(cid)))
        g.add((c, CMMC.weight, Literal(weight)))
        g.add((c, CMMC.poamEligible, Literal(weight == 1)))
    return g


def _ds() -> Dataset:
    return Dataset(default_union=True)


def _require(ds: Dataset, cid: str) -> None:
    ds.graph(URIRef(G_ORDER)).add((CE["Order-NV012"], CE.requiresControl, CMMC[cid]))


def _module(ds: Dataset, cid: str) -> None:
    ds.graph(URIRef(G_STRUCTURAL)).add((CE[f"module-{cid}"], CMMC.controlsSatisfied, CMMC[cid]))


def _evidence(ds: Dataset, cid: str, ev_id: str | None = None) -> URIRef:
    ev = CE[f"evidence/{ev_id or cid}"]
    g = ds.graph(URIRef(G_EVIDENCE))
    g.add((ev, RDF.type, CE.Evidence))
    g.add((ev, CE.addresses, CMMC[cid]))
    return ev


def _attest(
    ds: Dataset, cid: str, *,
    outcome=EARL.passed, oracle=None, override: str | None = None,
    evidence: URIRef | None = None, backed: bool = False,
) -> URIRef:
    g = ds.graph(URIRef(G_ATTESTATIONS))
    att = CE[f"ATT-{cid}"]
    g.add((att, RDF.type, CE.Attestation))
    g.add((att, CE.attests, CMMC[cid]))
    g.add((att, CE.hasOutcome, outcome))
    if oracle is not None:
        g.add((att, CE.oracleOutcome, oracle))
    if override:
        g.add((att, CMMC.overrideJustification, Literal(override)))
        # A valid override carries appended evidence (R13 requires the pair).
        g.add((att, CE.overrideEvidence, Literal("override-evidence-artifact-hash")))
    if evidence is not None:
        g.add((att, CE.hasEvidence, evidence))
    if backed:
        g.add((att, CE.backedBy, CE[f"oracle-assertion-{cid}"]))
    return att


def _fully_satisfied(ds: Dataset, cid: str, *, oracle=EARL.passed) -> None:
    """require + module + evidence + MET attestation citing that evidence."""
    _require(ds, cid)
    _module(ds, cid)
    ev = _evidence(ds, cid)
    _attest(ds, cid, oracle=oracle, evidence=ev)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_happy_path_forward_backward_pass_sprs_final():
    ds = _ds()
    controls = [("IA.L2-3.5.3", 5), ("SC.L2-3.13.11", 5), ("AC.L2-3.1.1", 5)]
    for cid, _w in controls:
        _fully_satisfied(ds, cid)
    report = audit(ds, catalog=_catalog(*controls))
    assert report.forward.passed
    assert report.backward.passed
    assert report.bidirectional().passed
    assert report.contradictions == []
    assert report.sprs is not None
    assert report.sprs.score == 110
    assert report.sprs.status == "Final"
    assert report.sprs.valid_submission
    assert report.passed


# ---------------------------------------------------------------------------
# R13 contradiction + proven-vs-attested split
# ---------------------------------------------------------------------------

def test_r13_contradiction_and_split():
    ds = _ds()
    # one machine-proven MET, one MET over a FAILED oracle without override
    _fully_satisfied(ds, "IA.L2-3.5.3", oracle=EARL.passed)          # machine
    ev = _evidence(ds, "SC.L2-3.13.11")
    _require(ds, "SC.L2-3.13.11"); _module(ds, "SC.L2-3.13.11")
    _attest(ds, "SC.L2-3.13.11", oracle=EARL.failed, evidence=ev)    # contradiction

    report = audit(ds, catalog=_catalog(("IA.L2-3.5.3", 5), ("SC.L2-3.13.11", 5)))

    assert len(report.contradictions) == 1
    row = report.contradictions[0]
    assert row.control == "SC.L2-3.13.11"
    assert row.oracle_outcome == "failed"
    assert not row.has_override
    # proven-vs-attested split
    assert report.proven.machine_count == 1
    assert report.proven.human_count == 1
    assert report.proven.summary() == "1 MET-by-machine / 1 MET-by-human-only"
    assert "1 MET-by-machine / 1 MET-by-human-only" in render_report(report)
    assert not report.passed  # a contradiction fails the audit


def test_override_clears_contradiction():
    ds = _ds()
    ev = _evidence(ds, "SC.L2-3.13.11")
    _require(ds, "SC.L2-3.13.11"); _module(ds, "SC.L2-3.13.11")
    _attest(ds, "SC.L2-3.13.11", oracle=EARL.failed, override="risk accepted", evidence=ev)
    report = audit(ds, catalog=_catalog(("SC.L2-3.13.11", 5)))
    assert report.contradictions == []
    # still human-only (oracle failed, not a passing machine proof)
    assert report.proven.human_count == 1
    assert report.proven.machine_count == 0


def test_needs_action_is_human_only_not_contradiction():
    ds = _ds()
    ev = _evidence(ds, "AT.L2-3.2.1")
    _require(ds, "AT.L2-3.2.1"); _module(ds, "AT.L2-3.2.1")
    _attest(ds, "AT.L2-3.2.1", oracle=CE.needsAction, evidence=ev)
    report = audit(ds, catalog=_catalog(("AT.L2-3.2.1", 5)))
    assert report.contradictions == []
    assert report.proven.met_by_human_only == ["AT.L2-3.2.1"]


# ---------------------------------------------------------------------------
# Gate-2 forward failure
# ---------------------------------------------------------------------------

def test_forward_fails_required_control_with_evidence_but_no_attestation():
    ds = _ds()
    _fully_satisfied(ds, "IA.L2-3.5.3")            # good
    # required + module + evidence, but NO attestation:
    _require(ds, "AC.L2-3.1.1")
    _module(ds, "AC.L2-3.1.1")
    _evidence(ds, "AC.L2-3.1.1")
    report = audit(ds, catalog=_catalog(("IA.L2-3.5.3", 5), ("AC.L2-3.1.1", 5)))
    assert not report.forward.passed
    subjects = {f.subject for f in report.forward.failures}
    assert "AC.L2-3.1.1" in subjects
    reason = next(f.reason for f in report.forward.failures if f.subject == "AC.L2-3.1.1")
    assert "no Gate-2 attestation" in reason


def test_forward_fails_required_control_with_no_module():
    ds = _ds()
    _require(ds, "AC.L2-3.1.1")   # required but nothing claims it
    report = audit(ds, catalog=_catalog(("AC.L2-3.1.1", 5)))
    assert not report.forward.passed
    reason = next(f.reason for f in report.forward.failures if f.subject == "AC.L2-3.1.1")
    assert "no claiming module" in reason


# ---------------------------------------------------------------------------
# Backward failure
# ---------------------------------------------------------------------------

def test_backward_fails_evidence_addresses_wrong_control():
    ds = _ds()
    # attestation for A cites evidence that addresses B, not A
    ev_b = _evidence(ds, "SC.L2-3.13.11", ev_id="ev-for-B")
    _attest(ds, "IA.L2-3.5.3", evidence=ev_b)
    report = audit(ds, catalog=_catalog(("IA.L2-3.5.3", 5)))
    assert not report.backward.passed
    assert any("IA.L2-3.5.3" in f.details.get("control", "") for f in report.backward.failures)


# ---------------------------------------------------------------------------
# SPRS wiring
# ---------------------------------------------------------------------------

def test_sprs_five_5pt_three_3pt_unmet_is_76_ineligible():
    ds = _ds()   # no attestations -> nothing MET
    controls = [(f"F{i}", 5) for i in range(5)] + [(f"T{i}", 3) for i in range(3)]
    catalog = _catalog(*controls)
    result = compute_sprs(ds, catalog=catalog)
    assert result is not None
    assert result.score == 76          # 110 - (5*5 + 3*3)
    assert result.status == "Ineligible"
    assert len(result.unmet) == 8


def test_sprs_5pt_on_poam_is_illegal_and_invalid():
    ds = _ds()
    # a 5-point control placed on a POA&M (carries cmmc:poamItem)
    ds.graph(URIRef(G_ORDER)).add((CMMC["AC.L2-3.1.1"], CMMC.poamItem, CE["poam/1"]))
    catalog = _catalog(("AC.L2-3.1.1", 5))
    result = compute_sprs(ds, catalog=catalog)
    assert result is not None
    assert "AC.L2-3.1.1" in result.illegal_poam
    assert result.valid_submission is False


def test_met_control_ids_derivation():
    ds = _ds()
    _fully_satisfied(ds, "IA.L2-3.5.3")
    _attest(ds, "SC.L2-3.13.11", outcome=EARL.failed)   # NOT MET
    met = audit_mod.met_control_ids(ds)
    assert met == {"IA.L2-3.5.3"}
