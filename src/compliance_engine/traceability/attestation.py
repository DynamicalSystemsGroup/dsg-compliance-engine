"""Gate 2 — the Affirming Official's per-control MET / NOT MET determination.

This is the ONLY place a CMMC control is asserted MET. `ce:attests` lives HERE
and nowhere else (evidence *addresses*; oracles *evaluate against*; only human
attestation *attests*). Ported from ADCS-lifecycle-demo/traceability/attestation.py
and retargeted to ce:/cmmc:.

The Affirming Official judges two things per control:
  (a) Adequacy    — "Is the implementation adequate?"    → a gsn:Assumption
  (b) Sufficiency — "Is the evidence sufficient to mark MET?" → a gsn:Justification

The determination is recorded as a `ce:Attestation` (also a prov:Activity) in the
`<ce:attestations>` graph, with an EARL outcome, a PROV qualified association to
the Affirming Official role, the backing-oracle outcome (so R13's
ContradictionShape can fire), and an optional `cmmc:overrideJustification` that
clears R13 when the official knowingly attests MET over a failing oracle.

EARL outcome mapping:  passed=MET · failed=NOT MET · inapplicable=N/A · untested=PLANNED.
"""

from __future__ import annotations

from datetime import datetime, timezone

from rdflib import BNode, Dataset, Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

from compliance_engine.ontology.prefixes import CE, CMMC, EARL, G_ATTESTATIONS, GSN, PROV
from compliance_engine.traceability.queries import EVIDENCE_FOR_CONTROL, query_to_dicts

# Stable individuals (Affirming Official role + the standard SOP plan).
ROLE_AFFIRMING_OFFICIAL = URIRef(f"{CE}role-AffirmingOfficial")
PLAN_STANDARD_PROCEDURE = URIRef(f"{CE}plan-StandardAttestationProcedure-v1")

# EARL outcome values (upstream EARL vocabulary) + ce:needsAction (local, a
# subclass of earl:OutcomeValue defined in ontology/ce-attestation-refs.ttl).
OUTCOME_PASSED = EARL.passed          # MET
OUTCOME_FAILED = EARL.failed          # NOT MET
OUTCOME_INAPPLICABLE = EARL.inapplicable  # N/A
OUTCOME_UNTESTED = EARL.untested      # PLANNED
OUTCOME_NEEDS_ACTION = CE.needsAction  # actionable missing piece (e.g. declined on sufficiency)

# Outcome IRI -> CMMC determination label (consumed by SPRS audit + SSP compiler).
STATUS_LABEL: dict[URIRef, str] = {
    OUTCOME_PASSED: "MET",
    OUTCOME_FAILED: "NOT MET",
    OUTCOME_INAPPLICABLE: "N/A",
    OUTCOME_UNTESTED: "PLANNED",
    OUTCOME_NEEDS_ACTION: "NEEDS ACTION",
}

MODE_MANUAL = EARL.manual
MODE_SEMI_AUTO = EARL.semiAuto
MODE_AUTO = EARL.automatic


def _writable_graph(target: Graph | Dataset) -> Graph:
    """Return the graph attestation triples are written to.

    Dataset → its <ce:attestations> named graph view. Flat Graph → itself.
    """
    if isinstance(target, Dataset):
        return target.graph(URIRef(G_ATTESTATIONS))
    return target


def _resolve_oracle_outcome(ds: Graph | Dataset, assertion_iri: URIRef) -> URIRef | None:
    """Read a ce:ControlCheckAssertion's outcome (assertion → earl:result →
    earl:TestResult → earl:outcome). Works over a Dataset (all graphs) or Graph.
    """
    def _iter(pattern):
        if isinstance(ds, Dataset):
            for s, p, o, _g in ds.quads(pattern):
                yield s, p, o
        else:
            for s, p, o in ds.triples(pattern):
                yield s, p, o

    for _s, _p, result_node in _iter((assertion_iri, EARL.result, None)):
        for _s2, _p2, outcome in _iter((result_node, EARL.outcome, None)):
            if isinstance(outcome, URIRef):
                return outcome
    # Fallback: some emitters may put earl:outcome directly on the assertion.
    for _s, _p, outcome in _iter((assertion_iri, EARL.outcome, None)):
        if isinstance(outcome, URIRef):
            return outcome
    return None


def request_attestation(
    ds: Graph | Dataset,
    control_id: str,
    official_name: str,
    *,
    auto_attest: bool = False,
    adequacy: str = "",
    sufficiency: str = "",
    outcome: URIRef = OUTCOME_PASSED,
    backing_oracle: URIRef | None = None,
    oracle_outcome: URIRef | None = None,
    override_justification: str | None = None,
    override_evidence: str | None = None,
    document_evidence: URIRef | None = None,
    now: str | None = None,
) -> URIRef:
    """Record a Gate-2 attestation for one control. Returns the attestation IRI.

    Emits into <ce:attestations> a well-formed `ce:Attestation` per the closure
    suite (AttestationShape):
      - ce:attests            -> the cmmc:Control (the MET/NOT-MET assertion)
      - gsn:inContextOf        -> gsn:Assumption   (adequacy, in gsn:statement)
      - gsn:inContextOf        -> gsn:Justification (sufficiency, in gsn:statement)
      - ce:hasOutcome          -> an EARL outcome
      - ce:attestationMode     -> earl:manual | earl:semiAuto
      - prov:qualifiedAssociation -> [agent + hadRole(AffirmingOfficial) + hadPlan]

    Backing-oracle link (R13): if `backing_oracle` is given, `ce:backedBy` points
    to it and its outcome is stamped as `ce:oracleOutcome` (or pass
    `oracle_outcome` directly). `override_justification` → `cmmc:overrideJustification`
    (this is what clears ContradictionShape when attesting MET over a failing oracle).

    Declined attestations (earl:failed / ce:needsAction) are well-formed too. The
    interactive path prompts the official; `auto_attest=True` requires the two
    judgement texts up front and records earl:semiAuto.

    `now` (ISO-8601, e.g. "2026-07-02T00:00:00+00:00") is used verbatim as the
    `prov:generatedAtTime` literal so a fully-specified run is byte-reproducible
    (the SSP's `document_date = MAX(prov:generatedAtTime)` no longer drifts). When
    `None`, the wall clock is used exactly as before (backward-compatible).
    """
    mode = MODE_SEMI_AUTO if auto_attest else MODE_MANUAL

    if not auto_attest:
        print(f"\n  Attestation for {control_id} — Affirming Official: {official_name}")
        adequacy_in = input(
            "  (a) Is the implementation adequate? "
            "(statement, or 'no' to decline): "
        ).strip()
        if adequacy_in.lower() in ("no", "n", ""):
            adequacy = "Implementation deemed inadequate for this control."
            sufficiency = "Not evaluated; attestation declined on adequacy grounds."
            outcome = OUTCOME_FAILED
        else:
            sufficiency_in = input(
                "  (b) Is the evidence sufficient to mark this control MET? "
                "(statement, or 'no'): "
            ).strip()
            if sufficiency_in.lower() in ("no", "n", ""):
                adequacy = adequacy_in
                sufficiency = "Evidence deemed insufficient to conclude MET."
                outcome = OUTCOME_NEEDS_ACTION
            else:
                adequacy, sufficiency = adequacy_in, sufficiency_in
                outcome = OUTCOME_PASSED
    else:
        if not adequacy or not sufficiency:
            raise ValueError(
                "auto_attest=True requires `adequacy` and `sufficiency` text."
            )

    write = _writable_graph(ds)

    att_id = f"ATT-{control_id}"
    att_uri = CE[att_id]
    control_uri = CMMC[control_id]
    official_uri = CE[f"official-{official_name.replace(' ', '_')}"]
    adequacy_uri = CE[f"adequacy/{att_id}"]
    sufficiency_uri = CE[f"sufficiency/{att_id}"]

    # Core attestation — ce:attests is the MET assertion (human-only).
    write.add((att_uri, RDF.type, CE.Attestation))
    write.add((att_uri, RDF.type, PROV.Activity))
    write.add((att_uri, CE.attests, control_uri))
    write.add((att_uri, CE.hasOutcome, outcome))
    write.add((att_uri, CE.attestationMode, mode))
    write.add((att_uri, PROV.wasAssociatedWith, official_uri))
    write.add((att_uri, EARL.assertedBy, official_uri))
    stamp = now if now is not None else datetime.now(timezone.utc).isoformat()
    write.add((att_uri, PROV.generatedAtTime, Literal(stamp, datatype=XSD.dateTime)))

    # Adequacy → gsn:Assumption; Sufficiency → gsn:Justification.
    write.add((adequacy_uri, RDF.type, GSN.Assumption))
    write.add((adequacy_uri, GSN.statement, Literal(adequacy)))
    write.add((att_uri, GSN.inContextOf, adequacy_uri))
    write.add((sufficiency_uri, RDF.type, GSN.Justification))
    write.add((sufficiency_uri, GSN.statement, Literal(sufficiency)))
    write.add((att_uri, GSN.inContextOf, sufficiency_uri))

    # PROV qualified association: who, in what role, following what plan.
    assoc = BNode()
    write.add((att_uri, PROV.qualifiedAssociation, assoc))
    write.add((assoc, RDF.type, PROV.Association))
    write.add((assoc, PROV.agent, official_uri))
    write.add((assoc, PROV.hadRole, ROLE_AFFIRMING_OFFICIAL))
    write.add((assoc, PROV.hadPlan, PLAN_STANDARD_PROCEDURE))

    # Backing-oracle link (R13). ce:oracleOutcome carries the outcome the shape
    # checks directly; ce:backedBy keeps the provenance pointer to the assertion.
    resolved = oracle_outcome
    if resolved is None and backing_oracle is not None:
        resolved = _resolve_oracle_outcome(ds, backing_oracle)
    if backing_oracle is not None:
        write.add((att_uri, CE.backedBy, backing_oracle))
    if resolved is not None:
        write.add((att_uri, CE.oracleOutcome, resolved))

    # Override justification + appended evidence. An override that attests MET over
    # a FAILED oracle must carry BOTH a written justification AND concrete appended
    # evidence — the justification alone does not clear the R13 contradiction
    # (OverrideEvidenceShape enforces the pairing).
    if override_justification:
        if not override_evidence:
            raise ValueError(
                f"override_justification for {control_id} requires override_evidence "
                f"(an appended, resolvable artifact hash/URI); justification alone is "
                f"not sufficient to overrule a failed machine check."
            )
        write.add((att_uri, CMMC.overrideJustification, Literal(override_justification)))
        write.add((att_uri, CE.overrideEvidence, Literal(override_evidence)))

    # Evidence linkage: attach every ce:Evidence that addresses this control.
    for ev in query_to_dicts(ds, EVIDENCE_FOR_CONTROL % control_id):
        if ev.get("ev"):
            write.add((att_uri, CE.hasEvidence, URIRef(ev["ev"])))
    # Track B: link the machine-recorded document evidence (ce:DocumentEvidence) the
    # human attestation rests on, so the chain control→attestation→document is explicit.
    if document_evidence is not None:
        write.add((att_uri, CE.hasEvidence, document_evidence))
        write.add((att_uri, CE.documentEvidence, document_evidence))

    # Affirming Official agent node (label used by the attestation queries).
    write.add((official_uri, RDF.type, PROV.Person))
    write.add((official_uri, RDFS.label, Literal(official_name)))

    outcome_short = str(outcome).rsplit("#", 1)[-1]
    print(f"  {control_id}: outcome=earl:{outcome_short} "
          f"({STATUS_LABEL.get(outcome, outcome_short)}) — {official_name}")
    return att_uri
