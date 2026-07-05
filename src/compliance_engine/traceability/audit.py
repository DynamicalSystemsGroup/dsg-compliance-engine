"""Bidirectional audit + contradiction dimension + SPRS verdict.

Ported from ADCS-lifecycle-demo/traceability/audit.py, retargeted to cmmc:/ce:
and with the Docker dead-code dropped (DockerProvenanceRow / _DOCKER_PROVENANCE_Q
/ docker_provenance() / the AuditReport.docker_provenance field + md section).

Forward and backward checks are INDEPENDENT (each emits its own failure list, so
messages name which direction broke). The forward check runs against the Order's
required-control set (`ce:requiresControl` in <ce:order>), NOT all 110.

Two CMMC-specific dimensions are added on top of the ADCS template:
  - Contradiction (R13): MET attestations whose backing oracle is failed/absent
    and which carry no cmmc:overrideJustification — the FCA "clean 110 over
    failing evidence" fraud pattern.
  - Proven-vs-attested split: how many MET controls are backed by a passing
    machine oracle vs marked MET by human judgement only (no config oracle result).

The SPRS score + POA&M-legality gate (traceability.sprs) is wired in: met_control_ids
is derived from the attestation graph (every ce:attests with earl:passed).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Literal

from rdflib import Dataset, Graph, Literal as RdfLiteral, URIRef
from rdflib.namespace import RDF, XSD

from compliance_engine.ontology.prefixes import CE, DCTERMS, EARL, G_AUDIT, PROV
from compliance_engine.traceability import sprs

Direction = Literal["forward", "backward", "bidirectional"]

_PREFIXES = """
PREFIX ce:    <http://dynamicalsystems.group/compliance-engine/>
PREFIX cmmc:  <http://dynamicalsystems.group/ontology/cmmc#>
PREFIX earl:  <http://www.w3.org/ns/earl#>
PREFIX prov:  <http://www.w3.org/ns/prov#>
PREFIX sysml: <https://www.omg.org/spec/SysML/2.0/>
"""

def _local(iri: str) -> str:
    """Control id from a cmmc: control IRI (local part after # or /)."""
    return str(iri).rsplit("#", 1)[-1].rsplit("/", 1)[-1]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Failure:
    subject: str
    reason: str
    details: dict = field(default_factory=dict)


@dataclass
class DirectionResult:
    direction: str
    passed: bool
    checked_count: int
    failures: list[Failure] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (f"{self.direction.title():<10} {status:<5} "
                f"({self.checked_count} checked, {len(self.failures)} failures)")


@dataclass
class BidirectionalResult:
    forward: DirectionResult
    backward: DirectionResult

    @property
    def passed(self) -> bool:
        return self.forward.passed and self.backward.passed


@dataclass
class ContradictionRow:
    """A MET attestation whose backing oracle is failed/absent, no override (R13)."""
    attestation: str
    control: str
    oracle_outcome: str    # "failed" | "absent" | other short name
    has_override: bool = False


@dataclass
class ProvenVsAttested:
    """The MET split: machine-proven (passing oracle) vs human-only."""
    met_by_machine: list[str] = field(default_factory=list)   # oracle earl:passed
    met_by_human_only: list[str] = field(default_factory=list)  # no config oracle result

    @property
    def machine_count(self) -> int:
        return len(self.met_by_machine)

    @property
    def human_count(self) -> int:
        return len(self.met_by_human_only)

    def summary(self) -> str:
        return (f"{self.machine_count} MET-by-machine / "
                f"{self.human_count} MET-by-human-only")


@dataclass
class CoverageCell:
    control: str
    evidence: str
    status: str        # covered+passed | covered+failed | covered+needsAction | covered+unattested | uncovered


@dataclass
class OrphanReport:
    controls_without_evidence: list[str] = field(default_factory=list)
    evidence_without_control: list[str] = field(default_factory=list)

    @property
    def any(self) -> bool:
        return bool(self.controls_without_evidence or self.evidence_without_control)


@dataclass
class AuditReport:
    forward: DirectionResult
    backward: DirectionResult
    contradictions: list[ContradictionRow]
    proven: ProvenVsAttested
    coverage: list[CoverageCell]
    orphans: OrphanReport
    required_controls: list[str]
    met_control_ids: list[str]
    timestamp: str
    sprs: "sprs.SprsResult | None" = None

    @property
    def passed(self) -> bool:
        return (self.forward.passed and self.backward.passed
                and not self.contradictions)

    def bidirectional(self) -> BidirectionalResult:
        return BidirectionalResult(forward=self.forward, backward=self.backward)


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def _rows(ds: Graph | Dataset, body: str) -> list:
    return list(ds.query(_PREFIXES + body))


def _required_controls(ds: Graph | Dataset) -> set[str]:
    """The Order's required-control set (ce:requiresControl in <ce:order>)."""
    return {_local(str(r[0])) for r in _rows(ds, "SELECT ?c WHERE { ?o ce:requiresControl ?c . }")}


def _module_claims(ds: Graph | Dataset) -> set[str]:
    return {_local(str(r[0])) for r in _rows(ds, "SELECT ?c WHERE { ?m cmmc:controlsSatisfied ?c . }")}


def _addresses_pairs(ds: Graph | Dataset) -> set[tuple[str, str]]:
    return {(str(r[0]), str(r[1]))
            for r in _rows(ds, "SELECT ?ev ?c WHERE { ?ev ce:addresses ?c . }")}


def _met_attestations(ds: Graph | Dataset) -> list[dict]:
    """One row per attestation: control, outcome, oracle outcome, override, backed."""
    q = """
    SELECT ?att ?control ?outcome ?oracle ?override ?backed ?overrideEv WHERE {
        ?att a ce:Attestation ;
             ce:attests ?control ;
             ce:hasOutcome ?outcome .
        OPTIONAL { ?att ce:oracleOutcome ?oracle }
        OPTIONAL { ?att cmmc:overrideJustification ?override }
        OPTIONAL { ?att ce:backedBy ?backed }
        OPTIONAL { ?att ce:overrideEvidence ?overrideEv }
    }
    """
    out = []
    for r in _rows(ds, q):
        # A valid override requires BOTH a written justification AND appended
        # evidence — a justification alone no longer clears the contradiction.
        override_ok = r[4] is not None and r[6] is not None
        out.append({
            "att": str(r[0]),
            "control": str(r[1]),
            "control_id": _local(str(r[1])),
            "outcome": r[2],
            "oracle": r[3],
            "override": override_ok,
            "override_justification_only": r[4] is not None and r[6] is None,
            "backed": r[5] is not None,
        })
    return out


# ---------------------------------------------------------------------------
# Direction checks — INDEPENDENT
# ---------------------------------------------------------------------------

def forward_trace(ds: Graph | Dataset, required: set[str] | None = None) -> DirectionResult:
    """Every REQUIRED control must have a claiming module AND a Gate-2 attestation.

    A required control with evidence but no attestation is a named forward failure.
    """
    required = _required_controls(ds) if required is None else required
    modules = _module_claims(ds)
    attested = {a["control_id"] for a in _met_attestations(ds)}
    evidence_controls = {c for _ev, c in _addresses_pairs(ds)}
    evidence_ids = {_local(c) for c in evidence_controls}

    failures: list[Failure] = []
    for cid in sorted(required):
        if cid not in modules:
            failures.append(Failure(
                subject=cid,
                reason=f"required control {cid} has no claiming module (cmmc:controlsSatisfied)",
                details={"has_module": False, "attested": cid in attested},
            ))
        elif cid not in attested:
            has_ev = cid in evidence_ids
            reason = (f"required control {cid} has evidence but no Gate-2 attestation"
                      if has_ev else
                      f"required control {cid} is not attested (no Gate-2 attestation)")
            failures.append(Failure(
                subject=cid, reason=reason,
                details={"has_module": True, "has_evidence": has_ev, "attested": False},
            ))

    return DirectionResult("forward", not failures, len(required), failures)


def backward_trace(ds: Graph | Dataset) -> DirectionResult:
    """Every attestation's cited evidence must ce:addresses the SAME control."""
    addresses = _addresses_pairs(ds)
    q = """
    SELECT ?att ?control ?ev WHERE {
        ?att a ce:Attestation ; ce:attests ?control ; ce:hasEvidence ?ev .
    }
    """
    failures: list[Failure] = []
    seen: set[str] = set()
    for r in _rows(ds, q):
        att, control, ev = str(r[0]), str(r[1]), str(r[2])
        seen.add(att)
        if (ev, control) not in addresses:
            failures.append(Failure(
                subject=att,
                reason=(f"attestation cites evidence {_local(ev)} that does not "
                        f"ce:addresses {_local(control)}"),
                details={"attestation": att, "evidence": ev, "control": control},
            ))
    return DirectionResult("backward", not failures, len(seen), failures)


def bidirectional_trace(ds: Graph | Dataset, required: set[str] | None = None) -> BidirectionalResult:
    return BidirectionalResult(forward=forward_trace(ds, required), backward=backward_trace(ds))


# ---------------------------------------------------------------------------
# Contradiction dimension (R13) + proven-vs-attested split
# ---------------------------------------------------------------------------

def contradictions_and_split(
    ds: Graph | Dataset,
) -> tuple[list[ContradictionRow], ProvenVsAttested]:
    """Compute the R13 contradiction list and the MET machine-vs-human split.

    Contradiction = MET (earl:passed) AND no cmmc:overrideJustification AND the
    backing oracle is failed OR asserted-but-absent (ce:backedBy present with no
    resolvable outcome). A needsAction oracle or no backing at all is NOT a
    contradiction — it is legitimate human-only judgement.
    """
    rows: list[ContradictionRow] = []
    split = ProvenVsAttested()
    for a in _met_attestations(ds):
        if a["outcome"] != EARL.passed:
            continue  # only MET attestations
        cid = a["control_id"]
        oracle = a["oracle"]
        # proven-vs-attested split
        if oracle == EARL.passed:
            split.met_by_machine.append(cid)
        else:
            split.met_by_human_only.append(cid)
        # contradiction detection
        if a["override"]:
            continue
        failed = oracle == EARL.failed
        absent = a["backed"] and oracle is None
        if failed or absent:
            rows.append(ContradictionRow(
                attestation=a["att"], control=cid,
                oracle_outcome="failed" if failed else "absent",
                has_override=False,
            ))
    split.met_by_machine.sort()
    split.met_by_human_only.sort()
    rows.sort(key=lambda r: r.control)
    return rows, split


# ---------------------------------------------------------------------------
# Coverage + orphans
# ---------------------------------------------------------------------------

def coverage_matrix(ds: Graph | Dataset) -> list[CoverageCell]:
    """One row per (control, addressing-evidence) with an outcome-derived status."""
    outcome_by_control: dict[str, object] = {}
    for a in _met_attestations(ds):
        outcome_by_control.setdefault(a["control_id"], a["outcome"])

    cells: list[CoverageCell] = []
    covered: set[str] = set()
    for ev, control in _addresses_pairs(ds):
        cid = _local(control)
        covered.add(cid)
        outcome = outcome_by_control.get(cid)
        if outcome == EARL.passed:
            status = "covered+passed"
        elif outcome == EARL.failed:
            status = "covered+failed"
        elif outcome is None:
            status = "covered+unattested"
        else:
            # ce:needsAction and any other outcome IRI render by local name.
            status = f"covered+{_local(str(outcome))}"
        cells.append(CoverageCell(control=cid, evidence=_local(ev), status=status))
    cells.sort(key=lambda c: (c.control, c.evidence))
    return cells


def orphans(ds: Graph | Dataset) -> OrphanReport:
    report = OrphanReport()
    all_controls = {_local(str(r[0]))
                    for r in _rows(ds, "SELECT ?c WHERE { ?c a cmmc:Control . }")}
    addressed = {_local(c) for _ev, c in _addresses_pairs(ds)}
    for cid in sorted(all_controls - addressed):
        report.controls_without_evidence.append(cid)
    q_ev = """
    SELECT ?ev WHERE {
        ?ev a ce:Evidence .
        FILTER NOT EXISTS { ?ev ce:addresses ?c }
    }
    """
    for r in _rows(ds, q_ev):
        report.evidence_without_control.append(str(r[0]))
    return report


# ---------------------------------------------------------------------------
# SPRS wiring
# ---------------------------------------------------------------------------

def met_control_ids(ds: Graph | Dataset) -> set[str]:
    """Controls attested MET (ce:attests + ce:hasOutcome earl:passed).

    Includes CSP-inherited-and-attested controls automatically — they are just
    controls carrying a passed attestation.
    """
    return {a["control_id"] for a in _met_attestations(ds)
            if a["outcome"] == EARL.passed}


def _poam_control_ids(ds: Graph | Dataset) -> set[str]:
    """Controls placed on a POA&M (carry a cmmc:poamItem)."""
    return {_local(str(r[0]))
            for r in _rows(ds, "SELECT ?c WHERE { ?c cmmc:poamItem ?p . }")}


def compute_sprs(
    ds: Graph | Dataset,
    *,
    catalog: "str | Graph | Dataset | None" = None,
    required: set[str] | None = None,
) -> "sprs.SprsResult | None":
    """Derive met/poam sets from the graph, then load statuses + score.

    Returns None only if the catalog has no scorable controls (so callers can
    render "SPRS: n/a" rather than crash).
    """
    met = met_control_ids(ds)
    poam = _poam_control_ids(ds)
    source = catalog if catalog is not None else ds
    statuses = sprs.load_control_statuses(
        source,
        met_control_ids=met,
        poam_control_ids=poam,
        required_control_ids=(required or None),
    )
    if not statuses:
        return None
    return sprs.score(statuses)


# ---------------------------------------------------------------------------
# Full audit
# ---------------------------------------------------------------------------

def audit(
    ds: Graph | Dataset,
    *,
    catalog: "str | Graph | Dataset | None" = None,
    timestamp: str | None = None,
) -> AuditReport:
    """Run the full audit suite + SPRS. Forward is scoped to the Order's required set."""
    required = _required_controls(ds)
    contradictions, split = contradictions_and_split(ds)
    sprs_result = compute_sprs(ds, catalog=catalog, required=(required or None))
    return AuditReport(
        forward=forward_trace(ds, required),
        backward=backward_trace(ds),
        contradictions=contradictions,
        proven=split,
        coverage=coverage_matrix(ds),
        orphans=orphans(ds),
        required_controls=sorted(required),
        met_control_ids=sorted(met_control_ids(ds)),
        timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
        sprs=sprs_result,
    )


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def _render_markdown(report: AuditReport) -> str:
    lines = ["# CMMC Traceability Audit", f"_generated {report.timestamp}_", ""]
    lines.append("## Direction summary")
    lines.append(f"- {report.forward.summary()}")
    lines.append(f"- {report.backward.summary()}")
    lines.append(f"- **Bidirectional: {'PASS' if report.bidirectional().passed else 'FAIL'}**")
    lines.append("")

    for direction in (report.forward, report.backward):
        if direction.failures:
            lines.append(f"## {direction.direction.title()} failures ({len(direction.failures)})")
            for f in direction.failures:
                lines.append(f"- **{f.subject}**: {f.reason}")
            lines.append("")

    # Contradiction dimension (rule R13 in the build plan)
    lines.append("## Contradictions (attested MET over failed machine check)")
    if not report.contradictions:
        lines.append("No contradictions: no MET attestation stands over a failed/absent oracle without an override.")
    else:
        lines.append(f"{len(report.contradictions)} MET attestation(s) over a failed/absent oracle WITHOUT override:")
        for c in report.contradictions:
            lines.append(f"- **{c.control}** ({c.attestation}): oracle={c.oracle_outcome}, override=none")
    lines.append("")
    lines.append(f"**Proven vs attested: {report.proven.summary()}**")
    if report.proven.met_by_human_only:
        lines.append(f"  - human-only MET: {', '.join(report.proven.met_by_human_only)}")
    lines.append("")

    # SPRS verdict
    lines.append("## SPRS")
    if report.sprs is None:
        lines.append("SPRS: n/a (no scorable controls in catalog).")
    else:
        s = report.sprs
        lines.append(f"- Score: **{s.score}** — status **{s.status}**")
        lines.append(f"- Valid submission: **{s.valid_submission}**")
        if s.illegal_poam:
            lines.append(f"- **Illegal POA&M** (weight>1 / excluded on a POA&M): {', '.join(s.illegal_poam)}")
        if s.unmet:
            lines.append(f"- Unmet controls: {len(s.unmet)}")
    lines.append("")

    lines.append("## Coverage matrix")
    lines.append("| Control | Evidence | Status |")
    lines.append("| --- | --- | --- |")
    for cell in report.coverage:
        lines.append(f"| {cell.control} | {cell.evidence} | {cell.status} |")
    return "\n".join(lines)


def _render_json(report: AuditReport) -> str:
    return json.dumps({
        "timestamp": report.timestamp,
        "passed": report.passed,
        "forward": {"passed": report.forward.passed,
                    "checked_count": report.forward.checked_count,
                    "failures": [asdict(f) for f in report.forward.failures]},
        "backward": {"passed": report.backward.passed,
                     "checked_count": report.backward.checked_count,
                     "failures": [asdict(f) for f in report.backward.failures]},
        "bidirectional": {"passed": report.bidirectional().passed},
        "contradictions": [asdict(c) for c in report.contradictions],
        "proven_vs_attested": {
            "met_by_machine": report.proven.met_by_machine,
            "met_by_human_only": report.proven.met_by_human_only,
            "summary": report.proven.summary(),
        },
        "required_controls": report.required_controls,
        "met_control_ids": report.met_control_ids,
        "coverage": [asdict(c) for c in report.coverage],
        "orphans": asdict(report.orphans),
        "sprs": (None if report.sprs is None else {
            "score": report.sprs.score,
            "status": report.sprs.status,
            "illegal_poam": report.sprs.illegal_poam,
            "valid_submission": report.sprs.valid_submission,
            "unmet": report.sprs.unmet,
        }),
    }, indent=2)


def render_report(report: AuditReport, fmt: Literal["md", "json"] = "md") -> str:
    if fmt == "json":
        return _render_json(report)
    return _render_markdown(report)


# ---------------------------------------------------------------------------
# RDF emission of the audit summary into <ce:audit>
# ---------------------------------------------------------------------------

def emit_audit_graph(ds: Dataset, report: AuditReport) -> URIRef:
    """Write the audit summary as RDF into <ce:audit> so it is itself queryable."""
    audit_g = ds.graph(URIRef(G_AUDIT))
    stamp = report.timestamp.replace(":", "").replace("-", "").replace(".", "")[:18]
    audit_iri = CE[f"audit/report-{stamp}"]

    audit_g.add((audit_iri, RDF.type, CE.AuditReport))
    audit_g.add((audit_iri, DCTERMS.created, RdfLiteral(report.timestamp, datatype=XSD.dateTime)))
    audit_g.add((audit_iri, CE.forwardPassed, RdfLiteral(report.forward.passed, datatype=XSD.boolean)))
    audit_g.add((audit_iri, CE.backwardPassed, RdfLiteral(report.backward.passed, datatype=XSD.boolean)))
    audit_g.add((audit_iri, CE.bidirectionalPassed, RdfLiteral(report.bidirectional().passed, datatype=XSD.boolean)))
    audit_g.add((audit_iri, CE.contradictionCount, RdfLiteral(len(report.contradictions), datatype=XSD.integer)))
    audit_g.add((audit_iri, CE.metByMachine, RdfLiteral(report.proven.machine_count, datatype=XSD.integer)))
    audit_g.add((audit_iri, CE.metByHumanOnly, RdfLiteral(report.proven.human_count, datatype=XSD.integer)))
    if report.sprs is not None:
        audit_g.add((audit_iri, CE.sprsScore, RdfLiteral(report.sprs.score, datatype=XSD.integer)))
        audit_g.add((audit_iri, CE.sprsStatus, RdfLiteral(report.sprs.status)))
        audit_g.add((audit_iri, CE.validSubmission, RdfLiteral(report.sprs.valid_submission, datatype=XSD.boolean)))
    audit_g.add((audit_iri, PROV.wasGeneratedBy, CE["agent/audit-module"]))
    return audit_iri
