"""Emit a ce:ControlCheckAssertion (an earl:Assertion) for an oracle result.

Ported from ADCS-lifecycle-demo/traceability/oracle_assertion.py, retargeted to
the compliance-engine vocab (`rtm:` → `ce:`, requirement → cmmc:Control).

An oracle (oracles.criteria.evaluate) compares a control's evidence `summary`
metric against a machine criterion and produces an EARL outcome. That outcome is
an automated, fully-specified **verification** result — it fits the EARL
assertion pattern exactly.

Discipline (R4/R9):
  * earl:mode is ALWAYS earl:automatic — verification, never human validation.
  * The assertion `ce:evaluatesAgainst` the cmmc:Control it checked.
  * It NEVER uses `ce:attests` — that predicate is reserved for the human
    ce:Attestation (Gate 2). The oracle verifies a config-level claim; only an
    attestation connects evidence to a control being MET. A regression test
    (tests/test_oracles.py) guards this.

Typing: metric values may be boolean / string / numeric. We let rdflib infer the
literal datatype (Literal(value) with no explicit datatype) so a boolean metric
serializes as xsd:boolean — it is NOT coerced to xsd:decimal.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from rdflib import Dataset, Literal, URIRef
from rdflib.namespace import RDF, XSD

from ontology.prefixes import CE, EARL, G_AUDIT, PROV
from pipeline.plan_execution import step_iri

if TYPE_CHECKING:  # pragma: no cover
    from oracles.criteria import Criterion, OracleResult


# The automated assertor (the Oracles stage) and the abstract test it runs.
ORACLE_AGENT = URIRef("urn:ce:agent:control-oracle")
CONTROL_CHECK_TEST = URIRef("urn:ce:test:control-check")

# String outcome (oracles.criteria) -> outcome IRI. ce:needsAction is a
# compliance-engine-local outcome value (subclass of earl:OutcomeValue) —
# distinct from cantTell so 'action required' doesn't get lumped with
# 'genuinely unknowable'. See ontology/ce-attestation-refs.ttl.
_OUTCOME_IRI = {
    "passed": EARL.passed,
    "failed": EARL.failed,
    "cantTell": EARL.cantTell,
    "needsAction": CE.needsAction,
}


def emit_control_check_assertion(
    ds: Dataset,
    evidence_iri: URIRef,
    control_iri: URIRef,
    result: "OracleResult",
    *,
    oracle_activity: Optional[URIRef] = None,
    criterion: "Optional[Criterion]" = None,
    now_iso: Optional[str] = None,
) -> URIRef:
    """Persist one ce:ControlCheckAssertion in the <ce:audit> graph.

    Args:
        ds:            the quadstore Dataset.
        evidence_iri:  the ce:Evidence node whose summary was evaluated.
        control_iri:   the cmmc:Control that was checked (evaluatesAgainst target).
        result:        the OracleResult (outcome + metric_value).
        oracle_activity: the Oracles-stage activity; defaults to step_iri("Oracles").
        criterion:     the Criterion applied (for metricKey/thresholdValue provenance).
        now_iso:       override timestamp (for deterministic tests).

    Returns the assertion IRI. NEVER emits ce:attests.
    """
    now = now_iso or datetime.now(timezone.utc).isoformat()
    suffix = now.replace(":", "-").replace("+", "-").replace(".", "-")
    assertion = URIRef(f"urn:ce:assertion:controlcheck-{result.control_id}-{suffix}")
    activity = oracle_activity or step_iri("Oracles")

    g = ds.graph(URIRef(G_AUDIT))

    # Types: our subclass + the EARL assertion pattern + a PROV activity.
    g.add((assertion, RDF.type, CE.ControlCheckAssertion))
    g.add((assertion, RDF.type, EARL.Assertion))
    g.add((assertion, RDF.type, PROV.Activity))

    # EARL: subject (evidence under test), test, mode.
    g.add((assertion, EARL.subject, evidence_iri))
    g.add((assertion, EARL.test, CONTROL_CHECK_TEST))
    g.add((assertion, EARL.mode, EARL.automatic))

    # EARL outcome carried on an earl:TestResult node (proper EARL structure).
    result_node = URIRef(f"{assertion}/result")
    g.add((assertion, EARL.result, result_node))
    g.add((result_node, RDF.type, EARL.TestResult))
    g.add((result_node, EARL.outcome, _OUTCOME_IRI[result.outcome]))
    if result.reason:
        g.add((result_node, CE.outcomeReason, Literal(result.reason)))

    # Control link — ce:evaluatesAgainst, NOT ce:attests (human-only).
    g.add((assertion, CE.evaluatesAgainst, control_iri))

    # Backing + provenance: the evidence it was computed over, and who/when.
    g.add((assertion, CE.backedBy, evidence_iri))
    g.add((assertion, PROV.wasGeneratedBy, activity))
    g.add((assertion, PROV.wasAssociatedWith, ORACLE_AGENT))
    g.add((assertion, PROV.atTime, Literal(now, datatype=XSD.dateTime)))

    # Comparison provenance. Metric value keeps its native type — a boolean
    # serializes as xsd:boolean, a string as xsd:string, a number as its
    # inferred numeric type — NEVER coerced to xsd:decimal. Omitted on cantTell
    # where the value is typically absent.
    if criterion is not None:
        g.add((assertion, CE.metricKey, Literal(criterion.metric_key)))
        if criterion.threshold is not None:
            g.add((assertion, CE.thresholdValue, Literal(criterion.threshold)))
    if result.metric_value is not None:
        g.add((assertion, CE.metricValue, Literal(result.metric_value)))

    return assertion
