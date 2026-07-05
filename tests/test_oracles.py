"""Tests for the CMMC control-check oracle.

Ported from ADCS-lifecycle-demo/tests/test_oracle.py. Covers the pure evaluation
logic (oracles.criteria.evaluate) and the EARL emitter (oracles.assertion). A
dedicated regression guards the core principle that the oracle NEVER uses
ce:attests — verification, not validation.
"""
from __future__ import annotations

import dataclasses

import pytest
from rdflib import Dataset, URIRef
from rdflib.namespace import RDF, XSD

from compliance_engine.oracles.criteria import (
    CRITERIA,
    OUTCOME_NEEDS_ACTION,
    OUTCOME_FAILED,
    OUTCOME_PASSED,
    Criterion,
    OracleResult,
    evaluate,
)
from compliance_engine.oracles.assertion import emit_control_check_assertion
from compliance_engine.ontology.prefixes import CE, CMMC, EARL, G_AUDIT, G_EVIDENCE, PROV


# ---------------------------------------------------------------------------
# evaluate — pure logic
# ---------------------------------------------------------------------------

def test_mfa_true_passes():
    result = evaluate({"mfa_enforced_privileged": True}, "IA.L2-3.5.3")
    assert result.outcome == OUTCOME_PASSED
    assert result.metric_value is True


def test_mfa_false_fails():
    result = evaluate({"mfa_enforced_privileged": False}, "IA.L2-3.5.3")
    assert result.outcome == OUTCOME_FAILED


def test_no_criterion_needs_action():
    # AT.L2-3.2.1 (training) has no automatable signal -> absent from CRITERIA.
    assert "AT.L2-3.2.1" not in CRITERIA
    result = evaluate({"anything": 1}, "AT.L2-3.2.1")
    assert result.outcome == OUTCOME_NEEDS_ACTION
    assert result.reason == "no-machine-criterion"
    assert "criterion" in result.detail


def test_criterion_present_metric_absent_needs_action():
    # Criterion exists for IA.L2-3.5.3 but the metric key is missing -> needsAction,
    # never fabricated as pass/fail.
    result = evaluate({"unrelated_key": True}, "IA.L2-3.5.3")
    assert result.outcome == OUTCOME_NEEDS_ACTION
    assert result.reason == "metric-absent"
    assert "absent" in result.detail
    assert result.metric_value is None


def test_iam_count_le_zero_passes_and_fails():
    assert evaluate({"overprivileged_bindings": 0}, "AC.L2-3.1.5").outcome == OUTCOME_PASSED
    assert evaluate({"overprivileged_bindings": 3}, "AC.L2-3.1.5").outcome == OUTCOME_FAILED


def test_logging_signal_bool():
    assert evaluate({"audit_log_export_enabled": True}, "AU.L2-3.3.1").outcome == OUTCOME_PASSED
    assert evaluate({"audit_log_export_enabled": False}, "AU.L2-3.3.1").outcome == OUTCOME_FAILED


def test_string_metric_region():
    assert evaluate({"data_region": "US"}, "ITAR-120.54").outcome == OUTCOME_PASSED
    assert evaluate({"data_region": "EU"}, "ITAR-120.54").outcome == OUTCOME_FAILED


def test_oracle_result_is_frozen():
    result = evaluate({"mfa_enforced_privileged": True}, "IA.L2-3.5.3")
    assert isinstance(result, OracleResult)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.outcome = OUTCOME_FAILED  # type: ignore[misc]


def test_evaluate_backward_compatible_signature():
    # explicit criteria arg still works (backward compat)
    custom = {"X.L2-3.9.9": Criterion("X.L2-3.9.9", "k", "eq", 1)}
    assert evaluate({"k": 1}, "X.L2-3.9.9", custom).outcome == OUTCOME_PASSED
    assert evaluate({"k": 1}, "IA.L2-3.5.3", custom).outcome == OUTCOME_NEEDS_ACTION


# ---------------------------------------------------------------------------
# emit_control_check_assertion — RDF emission into <ce:audit>
# ---------------------------------------------------------------------------

_EVIDENCE = URIRef("urn:ce:evidence:EV-mfa-2sv")
_CONTROL = CMMC["IA.L2-3.5.3"]
_NOW = "2026-07-02T00:00:00+00:00"


def _emit(summary, control_id="IA.L2-3.5.3"):
    ds = Dataset()
    result = evaluate(summary, control_id)
    crit = CRITERIA.get(control_id)
    assertion = emit_control_check_assertion(
        ds, _EVIDENCE, CMMC[control_id], result, criterion=crit, now_iso=_NOW
    )
    return ds, assertion, result


def test_emit_passed_shape():
    ds, assertion, _ = _emit({"mfa_enforced_privileged": True})
    g = ds.graph(URIRef(G_AUDIT))
    assert (assertion, RDF.type, CE.ControlCheckAssertion) in g
    assert (assertion, RDF.type, EARL.Assertion) in g
    assert (assertion, EARL.mode, EARL.automatic) in g
    assert (assertion, EARL.subject, _EVIDENCE) in g
    assert (assertion, CE.evaluatesAgainst, _CONTROL) in g
    assert (assertion, CE.backedBy, _EVIDENCE) in g
    assert (assertion, PROV.wasGeneratedBy, CE["step-Oracles"]) in g
    # outcome lives on an earl:TestResult node
    result_node = g.value(assertion, EARL.result)
    assert (result_node, RDF.type, EARL.TestResult) in g
    assert (result_node, EARL.outcome, EARL.passed) in g


def test_emit_failed_outcome():
    ds, assertion, _ = _emit({"mfa_enforced_privileged": False})
    g = ds.graph(URIRef(G_AUDIT))
    result_node = g.value(assertion, EARL.result)
    assert (result_node, EARL.outcome, EARL.failed) in g


def test_emit_needsaction_outcome_no_metric_value():
    ds, assertion, _ = _emit({"unrelated": 1})
    g = ds.graph(URIRef(G_AUDIT))
    result_node = g.value(assertion, EARL.result)
    assert (result_node, EARL.outcome, CE.needsAction) in g
    # no fabricated metric value
    assert g.value(assertion, CE.metricValue) is None


def test_boolean_metric_no_decimal_coercion():
    # Typing regression: a boolean metric must serialize as xsd:boolean, and the
    # whole dataset must serialize without an xsd:decimal coercion error.
    ds, assertion, _ = _emit({"mfa_enforced_privileged": True})
    g = ds.graph(URIRef(G_AUDIT))
    lit = g.value(assertion, CE.metricValue)
    assert lit.datatype == XSD.boolean
    assert lit.datatype != XSD.decimal
    # serialization does not raise
    ds.serialize(format="trig")


def test_string_metric_serializes_as_string():
    ds, assertion, _ = _emit({"data_region": "US"}, control_id="ITAR-120.54")
    g = ds.graph(URIRef(G_AUDIT))
    lit = g.value(assertion, CE.metricValue)
    assert lit.datatype in (XSD.string, None)
    ds.serialize(format="trig")


def test_emit_never_uses_attests():
    # Core principle: the oracle never links a control to satisfaction.
    ds, assertion, _ = _emit({"mfa_enforced_privileged": False})
    # search ALL quads in the dataset for any ce:attests triple
    for s, p, o, _ctx in ds.quads((None, CE.attests, None, None)):
        pytest.fail(f"oracle emitted a forbidden ce:attests triple: {s} {p} {o}")
    g = ds.graph(URIRef(G_AUDIT))
    assert (assertion, CE.evaluatesAgainst, _CONTROL) in g


def test_emit_writes_to_audit_graph_not_evidence():
    ds, assertion, _ = _emit({"mfa_enforced_privileged": True})
    audit = ds.graph(URIRef(G_AUDIT))
    evidence = ds.graph(URIRef(G_EVIDENCE))
    assert len(audit) > 0
    assert (assertion, RDF.type, CE.ControlCheckAssertion) not in evidence
