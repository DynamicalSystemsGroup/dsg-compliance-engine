"""Cross-unit SHACL closure + graph-consistency integration probe.

Assembles ONE Dataset spanning the units — catalog (U2) + structural (U3) +
evidence (U6) + oracle assertions (U7) + Gate-2 attestations (U9) — and asserts
the closure suite (U2 shapes, run via U9 `verification.verify`) is conformant
across unit boundaries. If a unit emitted a predicate the shapes don't accept,
this fails HERE (at the shape layer), not in U13.

Read-only probe: builds synthetic-but-real graphs from the shipped code; touches
no other file. Fixtures are small and deterministic (timestamps fed in).

Design note surfaced by this probe (see results/agent-2.md "DRIFT FOUND"):
`ForwardTraceabilityShape` (ontology/cmmc_shapes.ttl) targets EVERY `cmmc:Control`,
so verifying over the full 110-control catalog flags every control not
attested+evidenced. A clean, conformant slice therefore loads only the controls
under test; `test_full_catalog_*` documents the full-scale behavior explicitly.
"""
from __future__ import annotations

import json

from rdflib import Graph, URIRef

from ontology.prefixes import CE, CMMC, G_AUDIT, G_EVIDENCE, G_ATTESTATIONS
from pipeline.dataset import create_dataset, graph_for
from evidence.binding import bind_config_evidence, CollectionMetadata
from evidence.generators import EvidenceArtifact
from oracles.criteria import CRITERIA, evaluate
from oracles.assertion import emit_control_check_assertion
from traceability.attestation import request_attestation, OUTCOME_PASSED
from traceability.verification import verify

_NOW = "2026-07-02T00:00:00+00:00"

# Machine-verifiable controls + a passing summary (metric key from criteria.py).
_PASSING = {
    "IA.L2-3.5.3": {"mfa_enforced_privileged": True},
    "SC.L2-3.13.11": {"fips_module_present": True},
    "AC.L2-3.1.1": {"unauthorized_principals": 0},
}
_CATALOG = Graph()
_CATALOG.parse("ontology/cmmc-edit.ttl", format="turtle")


# ---------------------------------------------------------------------------
# Fixture assembly (spans U2/U3/U6/U7/U9)
# ---------------------------------------------------------------------------

def _load_control(ds, cid: str) -> None:
    """Copy one control's ABox triples from the committed catalog into <ce:ontology>."""
    og = graph_for(ds, "ontology")
    c = CMMC[cid]
    for p, o in _CATALOG.predicate_objects(c):
        og.add((c, p, o))


def _bind_evidence(ds, cid: str, summary: dict) -> URIRef:
    art = EvidenceArtifact(
        raw_bytes=json.dumps(summary, sort_keys=True).encode("utf-8"),
        summary=summary,
        controls=[cid],
        collection_metadata=CollectionMetadata(
            "gcp.test", "gcloud describe", _NOW, "mock-1.0"),
        evidentiary_status="mock",
        method="config-export",
        source_file=f"fixtures/{cid}.json",
    )
    return bind_config_evidence(graph_for(ds, "evidence"), art, evidence_id=cid)


def _emit_oracle(ds, cid: str, summary: dict) -> URIRef:
    result = evaluate(summary, cid)
    return emit_control_check_assertion(
        ds, CE[f"evidence/{cid}"], CMMC[cid], result,
        criterion=CRITERIA.get(cid), now_iso=_NOW,
    )


def _wire_control(
    ds, cid: str, summary: dict, *,
    outcome=OUTCOME_PASSED, override: str | None = None,
) -> URIRef:
    """Fully wire one control: catalog node + evidence + oracle + Gate-2 attestation."""
    _load_control(ds, cid)
    _bind_evidence(ds, cid, summary)
    assertion = _emit_oracle(ds, cid, summary)
    request_attestation(
        ds, cid, "Jane Official", auto_attest=True,
        adequacy="Implementation is adequate for this control.",
        sufficiency="Evidence + passing oracle are sufficient to mark MET.",
        outcome=outcome, backing_oracle=assertion, override_justification=override,
    )
    return assertion


def _clean_slice():
    ds = create_dataset()
    for cid, summary in _PASSING.items():
        _wire_control(ds, cid, summary)
    return ds


# ---------------------------------------------------------------------------
# Clean run conforms (the real integration assertion)
# ---------------------------------------------------------------------------

def test_clean_assembled_graph_conforms():
    ds = _clean_slice()
    report = verify(ds)
    assert report.conforms, (
        "cross-unit closure failed — named drift: "
        + "; ".join(f"{v.shape.rsplit('#', 1)[-1]}: {v.message[:80]}"
                    for v in report.shape_violations)
    )
    assert report.shape_violations == []
    assert report.reverification_mismatches == []


# ---------------------------------------------------------------------------
# R13 ContradictionShape fires cross-unit
# ---------------------------------------------------------------------------

def _r13_slice(*, override: str | None):
    ds = create_dataset()
    # MET attestation over a FAILED oracle (fips absent -> oracle failed)
    _wire_control(ds, "SC.L2-3.13.11", {"fips_module_present": False},
                  outcome=OUTCOME_PASSED, override=override)
    return ds


def test_r13_contradiction_fires_without_override():
    ds = _r13_slice(override=None)
    report = verify(ds)
    assert report.conforms is False
    assert "ContradictionShape" in report.shapes_named() \
        or "Contradiction (R13)" in report.shape_results_text


def test_r13_override_clears_contradiction():
    ds = _r13_slice(override="Compensating control X in place; risk accepted 2026-07-02.")
    report = verify(ds)
    assert "ContradictionShape" not in report.shapes_named()
    assert "Contradiction (R13)" not in report.shape_results_text
    assert report.conforms, [v.shape for v in report.shape_violations]


# ---------------------------------------------------------------------------
# PoamLegalityShape fires cross-unit
# ---------------------------------------------------------------------------

def test_poam_legality_fires_for_weight_gt1_on_poam():
    ds = _clean_slice()
    # SC.L2-3.13.11 is weight 5; placing it on a POA&M is illegal.
    graph_for(ds, "ontology").add((CMMC["SC.L2-3.13.11"], CMMC.poamItem, CE["poam/1"]))
    report = verify(ds)
    assert report.conforms is False
    assert "PoamLegalityShape" in report.shapes_named()


# ---------------------------------------------------------------------------
# Re-verification catches evidence tamper
# ---------------------------------------------------------------------------

def test_reverification_catches_content_hash_tamper():
    ds = _clean_slice()
    eg = graph_for(ds, "evidence")
    ev = CE["evidence/IA.L2-3.5.3"]
    stored = eg.value(ev, CE.contentHash)
    eg.remove((ev, CE.contentHash, stored))
    eg.add((ev, CE.contentHash, __import__("rdflib").Literal("0" * 64)))
    report = verify(ds)
    assert report.reverification_mismatches
    assert any(m.evidence == str(ev) for m in report.reverification_mismatches)
    assert report.conforms is False


# ---------------------------------------------------------------------------
# Evidence never attests — cross-graph invariant
# ---------------------------------------------------------------------------

def test_evidence_graph_never_carries_attests():
    ds = _clean_slice()
    evidence_g = ds.graph(URIRef(G_EVIDENCE))
    attest_g = ds.graph(URIRef(G_ATTESTATIONS))
    # No ce:attests anywhere in <ce:evidence>...
    assert not list(evidence_g.triples((None, CE.attests, None)))
    # ...but <ce:attestations> does carry it (only humans attest).
    assert list(attest_g.triples((None, CE.attests, None)))
    # And the oracle graph evaluates-against but never attests.
    audit_g = ds.graph(URIRef(G_AUDIT))
    assert list(audit_g.triples((None, CE.evaluatesAgainst, None)))
    assert not list(audit_g.triples((None, CE.attests, None)))


# ---------------------------------------------------------------------------
# Full-catalog + in-scope Order — ForwardTraceabilityShape is scoped to
# ce:requiresControl, so out-of-scope controls (the ~88 a Phase-I Tier-1 Order
# doesn't require) no longer produce false failures.
# ---------------------------------------------------------------------------

def _wire_no_load(ds, cid: str, summary: dict) -> None:
    """Evidence + oracle + attestation for a control, WITHOUT loading its ABox
    (the full catalog is loaded separately in these full-catalog cases)."""
    _bind_evidence(ds, cid, summary)
    assertion = _emit_oracle(ds, cid, summary)
    request_attestation(
        ds, cid, "Jane Official", auto_attest=True,
        adequacy="adequate", sufficiency="sufficient",
        outcome=OUTCOME_PASSED, backing_oracle=assertion,
    )


def _require(ds, cid: str) -> None:
    graph_for(ds, "order").add((CE["Order-NV012"], CE.requiresControl, CMMC[cid]))


def test_full_catalog_with_inscope_order_conforms():
    # Full 110-control catalog loaded, but the Order requires only the 3 controls
    # we fully wire → out-of-scope controls must NOT fire ForwardTraceability.
    ds = create_dataset()
    og = graph_for(ds, "ontology")
    for t in _CATALOG:
        og.add(t)
    for cid, summary in _PASSING.items():
        _wire_no_load(ds, cid, summary)
        _require(ds, cid)
    report = verify(ds)
    assert report.conforms is True, (
        "out-of-scope controls should not fire ForwardTraceability: "
        + "; ".join(f"{v.shape.rsplit('#', 1)[-1]}: {v.focus}"
                    for v in report.shape_violations)
    )
    assert report.shape_violations == []


def test_required_but_unattested_control_fires_forward():
    # Full catalog + an Order requiring one control that is NOT attested →
    # ForwardTraceability fires for EXACTLY that control (real in-scope gap),
    # and for no other (out-of-scope controls stay silent).
    ds = create_dataset()
    og = graph_for(ds, "ontology")
    for t in _CATALOG:
        og.add(t)
    # wire + require the 3 machine controls...
    for cid, summary in _PASSING.items():
        _wire_no_load(ds, cid, summary)
        _require(ds, cid)
    # ...then require an extra control with NO evidence/attestation.
    gap = "AU.L2-3.3.1"
    _require(ds, gap)
    report = verify(ds)
    assert report.conforms is False
    assert report.shapes_named() == {"ForwardTraceabilityShape"}
    assert len(report.shape_violations) == 1
    assert report.shape_violations[0].focus == str(CMMC[gap])
