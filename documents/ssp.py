"""NV012 System Security Plan (SSP) + Traceability Matrix (Document 2) compiler.

A deterministic *view* over the persisted RDF dataset: identical input quads
produce byte-identical Markdown. Nothing here consults the wall clock — the
document date is the maximum ``prov:generatedAtTime`` in the dataset, and the
dataset fingerprint is a stable sha256 over the sorted quads (blank nodes are
tokenised so the hash survives rdflib's per-parse blank-node relabelling).

Term discipline: the VCRM "status" column reports the human **attestation**
outcome (via ``STATUS_LABEL``). Evidence *addresses* a control; it never *attests*
one — a control with no attestation is PLANNED (a gap), never MET.

R12: if the dataset carries ANY ``ce:evidentiaryStatus`` of ``mock`` / ``mock-plan``,
a NON-EVIDENTIARY banner is emitted at the top AND stamped in the colophon. The
compiler cannot emit the document without it while mock status is present.

Hooks wired at integration (U10 audit + U11 BOM, next round): ``sprs_summary``
and ``bom_artifact_hashes`` default to ``None`` and render "pending" / fall back
to the committed ``ce:contentHash`` values respectively.
"""

from __future__ import annotations

import difflib
import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rdflib import BNode, Dataset, Literal, URIRef

if TYPE_CHECKING:
    from traceability.audit import AuditReport
    from traceability.bom import BOM

from ontology.prefixes import NAMED_GRAPHS
from traceability.attestation import STATUS_LABEL
from documents.queries import (
    ATTESTATION_DETAIL,
    CONTROL_IMPLEMENTATION,
    CONTROLS_FULL,
    EVIDENCE_HASHES,
    EVIDENCE_LOCATION,
    EVIDENTIARY_STATUSES,
    MAX_GENERATED_AT,
    POAM_REFS,
    query_to_dicts,
)

DOC_ID = "SSP-NV012"
DOC_TITLE = "NV012 System Security Plan + Traceability Matrix (Document 2)"
SHORT_HASH = 12

# Evidentiary-status literals that make the dataset NON-EVIDENTIARY (R12).
MOCK_STATUSES = frozenset({"mock", "mock-plan"})

# EARL outcome short-name → human status label (MET / NOT MET / N/A / PLANNED …).
_SHORT_TO_LABEL = {
    str(k).rsplit("#", 1)[-1].rsplit("/", 1)[-1]: v for k, v in STATUS_LABEL.items()
}
# A control with no attestation is a planned gap.
_NO_ATTESTATION_STATUS = "PLANNED"


@dataclass(frozen=True)
class SprsSummary:
    """The SPRS/contradiction numbers U10-audit + U11-BOM supply at integration."""

    score: int
    status: str                 # "Final" | "Conditional" | "Ineligible"
    met_by_machine: int
    met_by_human_only: int
    contradiction_count: int


# ---------------------------------------------------------------------------
# Deterministic building blocks (ported from ADCS design_description.py)
# ---------------------------------------------------------------------------

def _fp_term(term) -> str:
    """Render an RDF term for the fingerprint; blank nodes → a stable token."""
    if isinstance(term, BNode):
        return "_:b"
    if isinstance(term, URIRef):
        return f"<{term}>"
    if isinstance(term, Literal):
        dt = f"^^<{term.datatype}>" if term.datatype else ""
        return f'"{term}"{dt}'
    return str(term)


def dataset_fingerprint(ds: Dataset) -> str:
    """Stable sha256 over the sorted quads (blank nodes tokenised).

    Survives re-parsing the same dataset (rdflib relabels blank nodes on every
    parse) because every blank node collapses to a constant token before the
    quad lines are sorted and hashed.
    """
    lines: set[str] = set()
    for ctx in ds.contexts():
        gid = str(ctx.identifier)
        for s, p, o in ctx:
            lines.add("\t".join((_fp_term(s), _fp_term(p), _fp_term(o), gid)))
    canonical = "\n".join(sorted(lines))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def document_date(ds: Dataset) -> str:
    """Maximum ``prov:generatedAtTime`` in the dataset (data-derived, never now)."""
    rows = query_to_dicts(ds, MAX_GENERATED_AT)
    return (rows[0]["maxTime"] if rows and rows[0]["maxTime"] else "-")


def graph_quad_counts(ds: Dataset) -> list[tuple[str, str, int]]:
    """(layer, graph IRI, triple count) per named graph, sorted by layer."""
    return [
        (layer, iri, len(ds.graph(URIRef(iri))))
        for layer, iri in sorted(NAMED_GRAPHS.items())
    ]


def _local(iri: str | None) -> str:
    if not iri:
        return "-"
    return iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def _one_line(text: str | None) -> str:
    return " ".join(text.split()) if text else "-"


def _join(values: Iterable[str]) -> str:
    return ", ".join(sorted(set(v for v in values if v))) or "-"


def _cell(text: str | None) -> str:
    return _one_line(text).replace("|", "\\|")


def _short_hash(h: str | None) -> str:
    return h[:SHORT_HASH] if h else "-"


def _md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(" --- " for _ in headers) + "|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------

def _group(rows: list[dict], key: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:
        out.setdefault(r[key], []).append(r)
    return out


def mock_statuses_present(ds: Dataset) -> list[str]:
    """Sorted list of mock/mock-plan evidentiary statuses present (R12 gate)."""
    statuses = {r["status"] for r in query_to_dicts(ds, EVIDENTIARY_STATUSES)}
    return sorted(s for s in statuses if s in MOCK_STATUSES)


def _status_label(att_rows: list[dict]) -> str:
    """Human status label for a control from its attestation outcome(s)."""
    if not att_rows:
        return _NO_ATTESTATION_STATUS
    labels = sorted({
        _SHORT_TO_LABEL.get(a["outcomeShort"], a["outcomeShort"] or "?")
        for a in att_rows
    })
    return "; ".join(labels)


def _gap_note(status: str, att_rows: list[dict]) -> str:
    """Gap-notes cell: nothing for MET; a reason otherwise + any override."""
    notes: list[str] = []
    if status == _NO_ATTESTATION_STATUS:
        notes.append("not attested (planned)")
    elif status != "MET":
        notes.append(f"attested {status}")
    overrides = sorted({a["override"] for a in att_rows if a.get("override")})
    if overrides:
        notes.append("override: " + "; ".join(_one_line(o) for o in overrides))
    return "; ".join(notes) if notes else "-"


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------

def compile_ssp(
    ds: Dataset,
    *,
    dataset_path: Path | None = None,
    sprs_summary: SprsSummary | None = None,
    bom_artifact_hashes: list[str] | None = None,
) -> str:
    """Compile the SSP + Traceability Matrix as byte-stable Markdown.

    ``sprs_summary`` / ``bom_artifact_hashes`` are the U10-audit / U11-BOM hooks:
    when ``None`` they render "pending" / fall back to the committed evidence
    ``ce:contentHash`` values.
    """
    controls = sorted(query_to_dicts(ds, CONTROLS_FULL), key=lambda r: r["controlId"])
    impl_by = _group(query_to_dicts(ds, CONTROL_IMPLEMENTATION), "controlId")
    ev_by = _group(query_to_dicts(ds, EVIDENCE_LOCATION), "controlId")
    att_by = _group(query_to_dicts(ds, ATTESTATION_DETAIL), "controlId")
    poam_by = _group(query_to_dicts(ds, POAM_REFS), "controlId")

    mock_present = mock_statuses_present(ds)
    fingerprint = dataset_fingerprint(ds)
    counts = graph_quad_counts(ds)
    total_quads = sum(n for _, _, n in counts)
    doc_date = document_date(ds)

    lines: list[str] = [
        "<!-- AUTO-GENERATED ARTIFACT - DO NOT EDIT.",
        "     Deterministic view compiled from the RDF dataset by documents/ssp.py.",
        "     Edit the dataset (re-run the pipeline), then rebuild:",
        "       uv run python -m documents.ssp build --input <dataset.trig> -->",
        "",
        f"# {DOC_ID} — {DOC_TITLE}",
        "",
    ]

    # -- R12 banner (mandatory when any mock status is present) --------------
    if mock_present:
        lines.extend([
            "> ⚠ **NON-EVIDENTIARY — fixture-derived / auto-attested.**",
            f"> Evidentiary status present: {', '.join(mock_present)}. "
            "This is a demonstration artifact, **not a submittable SSP**.",
            "",
        ])

    # -- 1. System identification + CUI boundary ----------------------------
    lines.extend([
        "## 1. System identification and CUI boundary",
        "",
    ])
    lines.extend(_md_table(
        ["Field", "Value"],
        [
            ["Document ID", DOC_ID],
            ["System", "NV012 Tier 1 IL4 CUI enclave"],
            ["CUI boundary", "Google Workspace Enterprise Plus + GCP Assured Workloads (IL4)"],
            ["Dataset", dataset_path.as_posix() if dataset_path else "-"],
            ["Dataset SHA-256", fingerprint],
            ["Quad count", str(total_quads)],
            ["Document date", doc_date],
            ["Evidentiary status",
             "NON-EVIDENTIARY (" + ", ".join(mock_present) + ")" if mock_present else "evidentiary"],
            ["Compiler", "documents/ssp.py"],
        ],
    ))

    # -- 2. Framework applicability -----------------------------------------
    lines.extend([
        "",
        "## 2. Framework applicability",
        "",
        "Scope: NIST SP 800-171 Rev. 2 / CMMC Level 2 (110 controls). Status is the",
        "recorded human attestation (EARL outcome via `STATUS_LABEL`); evidence",
        "*addresses* controls but never *attests* them. The machine-checkable subset",
        "is verified by oracles; the remainder is human-attested from documentary",
        "evidence.",
        "",
        "## 3. Verification Cross-Reference Matrix (VCRM) — Document 2",
        "",
        "One row per control (all 110). Status is the attestation outcome; a control",
        "with no attestation is PLANNED (a gap).",
        "",
    ])

    vcrm_rows: list[list[str]] = []
    for c in controls:
        cid = c["controlId"]
        impls = impl_by.get(cid, [])
        evs = ev_by.get(cid, [])
        atts = att_by.get(cid, [])
        poams = poam_by.get(cid, [])
        status = _status_label(atts)
        vcrm_rows.append([
            cid,
            _join(i["moduleLabel"] for i in impls if i["moduleLabel"]),
            _join(a["official"] for a in atts if a["official"]),
            _join((e["sourceFile"] or e["documentRef"]) for e in evs),
            _join(_short_hash(e["contentHash"]) for e in evs),
            status,
            _cell(_gap_note(status, atts)),
            _join(_local(p["poamItem"]) for p in poams),
        ])
    lines.extend(_md_table(
        ["Control", "Implementation", "Responsible party", "Evidence location",
         "Evidence hash", "Status", "Gap notes", "POA&M ref"],
        vcrm_rows,
    ))

    # -- 4. Per-control detail (adequacy/sufficiency from attestation GSN) ---
    lines.extend([
        "",
        "## 4. Per-control detail",
        "",
    ])
    attested_controls = [c for c in controls if att_by.get(c["controlId"])]
    if not attested_controls:
        lines.append("No controls have been attested yet.")
        lines.append("")
    for c in attested_controls:
        cid = c["controlId"]
        lines.extend([
            f"### {cid}",
            "",
            f"**Statement.** {_one_line(c['text'])}",
            "",
            f"- Family: {_local(c['family'])} · Weight: {c['weight'] or '-'} · "
            f"POA&M-eligible: {c['poamEligible'] or '-'}",
            f"- Implementation: {_join(i['moduleLabel'] for i in impl_by.get(cid, []) if i['moduleLabel'])}",
            f"- Verification method: {_join(_local(i['verification']) for i in impl_by.get(cid, []) if i['verification'])}",
            "",
        ])
        for a in sorted(att_by.get(cid, []), key=lambda r: r["att"]):
            status = _SHORT_TO_LABEL.get(a["outcomeShort"], a["outcomeShort"] or "?")
            lines.extend([
                f"- Attestation: {_local(a['att'])} — **{status}** by {a['official'] or '-'}",
                f"  - Timestamp: {a['timestamp'] or '-'}",
                f"  - Adequacy assumption: {_one_line(a['adequacy'])}",
                f"  - Sufficiency justification: {_one_line(a['sufficiency'])}",
            ])
            if a.get("override"):
                lines.append(f"  - Override justification: {_one_line(a['override'])}")
        lines.append("")

    # -- 5. Colophon --------------------------------------------------------
    lines.extend([
        "## 5. Colophon",
        "",
    ])
    lines.extend(_md_table(
        ["Layer", "Named graph", "Triples"],
        [[layer, f"`{iri}`", str(n)] for layer, iri, n in counts],
    ))

    # SPRS summary hook (U10-audit + U11-BOM).
    if sprs_summary is None:
        sprs_line = "SPRS summary: pending audit (U10/U11 integration)."
    else:
        s = sprs_summary
        sprs_line = (
            f"SPRS summary: score {s.score} ({s.status}); "
            f"{s.met_by_machine} MET-by-machine / {s.met_by_human_only} MET-by-human-only; "
            f"contradictions: {s.contradiction_count}."
        )

    # BOM artifact-hash hook: fall back to committed ce:contentHash values.
    if bom_artifact_hashes is not None:
        bom_hashes = sorted(set(bom_artifact_hashes))
        bom_source = "BOM"
    else:
        bom_hashes = sorted({r["contentHash"] for r in query_to_dicts(ds, EVIDENCE_HASHES)})
        bom_source = "committed ce:contentHash (BOM pending)"

    lines.extend([
        "",
        f"Dataset SHA-256: `{fingerprint}`",
        "",
        f"Document date (max prov:generatedAtTime): {doc_date}",
        "",
        sprs_line,
        "",
        f"Artifact hashes ({bom_source}): {len(bom_hashes)}",
        "",
    ])
    lines.extend(f"- `{h}`" for h in bom_hashes)
    if not bom_hashes:
        lines.append("- (none)")

    if mock_present:
        lines.extend([
            "",
            f"**NON-EVIDENTIARY stamp:** statuses present — {', '.join(mock_present)}. "
            "Not a submittable SSP (R12).",
        ])

    lines.extend([
        "",
        "Rebuild and drift-check:",
        "",
        "```bash",
        "uv run python -m documents.ssp build"
        + (f" --input {dataset_path.as_posix()}" if dataset_path else ""),
        "uv run python -m documents.ssp build --check",
        "```",
    ])
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Run integration — wire the colophon to the real audit (U10) + BOM (U11b)
# ---------------------------------------------------------------------------

def sprs_summary_from_audit(report: "AuditReport | None") -> SprsSummary | None:
    """Build the colophon SPRS summary from an audit report.

    ``score``/``status`` come from ``report.sprs`` (the U10-sprs ``SprsResult``);
    ``met_by_machine``/``met_by_human_only`` from ``report.proven`` (the
    proven-vs-attested split); ``contradiction_count`` = ``len(report.contradictions)``.
    Returns ``None`` when no report is given or the audit produced no SPRS score
    (so the colophon falls back to "pending").
    """
    if report is None or report.sprs is None:
        return None
    return SprsSummary(
        score=report.sprs.score,
        status=report.sprs.status,
        met_by_machine=report.proven.machine_count,
        met_by_human_only=report.proven.human_count,
        contradiction_count=len(report.contradictions),
    )


def compile_ssp_from_run(
    ds: Dataset,
    *,
    audit_report: "AuditReport | None" = None,
    bom: "BOM | None" = None,
    dataset_path: Path | None = None,
) -> str:
    """Compile the SSP with the real audit + BOM colophon when available.

    The entry point for ``cli.py`` (agent-1) and the U13 e2e run: derives
    ``sprs_summary`` from ``audit_report`` and ``bom_artifact_hashes`` from
    ``bom.artifact_hashes()``, then delegates to :func:`compile_ssp`. When both
    are ``None`` the output is identical to the U12a fallback ("pending" SPRS +
    committed ``ce:contentHash`` values); the R12 banner is unaffected either way.
    """
    return compile_ssp(
        ds,
        dataset_path=dataset_path,
        sprs_summary=sprs_summary_from_audit(audit_report),
        bom_artifact_hashes=(bom.artifact_hashes() if bom is not None else None),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _compile_with_optional_audit(ds: Dataset, input: Path, audit: bool) -> str:
    """Compile, deriving the real audit colophon from the dataset when asked.

    The audit (SPRS + contradictions) is derivable from the persisted dataset;
    the BOM object is not reconstructed here, so BOM hashes fall back to the
    committed ``ce:contentHash`` values. A dataset that cannot be audited (e.g.
    missing the control catalog) falls back cleanly to the "pending" colophon —
    the no-audit path and R12 banner are never broken.
    """
    if not audit:
        return compile_ssp(ds, dataset_path=input)
    try:
        from traceability.audit import audit as run_audit

        report = run_audit(ds)
    except Exception:
        return compile_ssp(ds, dataset_path=input)
    return compile_ssp_from_run(ds, audit_report=report, dataset_path=input)


app = typer.Typer(
    add_completion=False,
    help=f"Compile {DOC_ID} — a deterministic SSP + Traceability Matrix view.",
    no_args_is_help=True,
)


@app.callback()
def _main() -> None:
    """Compile the NV012 SSP + Traceability Matrix (Document 2).

    The callback keeps `build` a required subcommand (a single-command Typer app
    would otherwise collapse the name away).
    """


@app.command()
def build(
    input: Annotated[Path, typer.Option(
        "--input", help="TriG dataset to compile from.",
    )] = Path("output/engine.trig"),
    output: Annotated[Path, typer.Option(
        "--output", help="Markdown file to (re)build.",
    )] = Path("output/ssp.md"),
    check: Annotated[bool, typer.Option(
        "--check",
        help="Recompile and diff against --output without writing; "
             "exit 1 on drift, 2 if the output is missing.",
    )] = False,
    stdout: Annotated[bool, typer.Option(
        "--stdout", help="Print the document instead of writing --output.",
    )] = False,
    audit: Annotated[bool, typer.Option(
        "--audit/--no-audit",
        help="Derive the real SPRS/contradiction colophon from the dataset "
             "(falls back to 'pending' if the audit cannot run). --no-audit "
             "forces the pending colophon.",
    )] = True,
) -> None:
    """Build (or drift-check) the SSP document."""
    if not input.exists():
        typer.echo(f"Input not found: {input}.", err=True)
        raise typer.Exit(code=2)
    ds = Dataset(default_union=True)
    ds.parse(input, format="trig")
    doc = _compile_with_optional_audit(ds, input, audit)

    if check:
        if not output.exists():
            typer.echo(f"Output not found: {output}. Build it first.", err=True)
            raise typer.Exit(code=2)
        current = output.read_bytes()
        if current == doc.encode("utf-8"):
            typer.echo(f"{output} is up to date.")
            return
        diff = difflib.unified_diff(
            current.decode("utf-8", errors="replace").splitlines(),
            doc.splitlines(),
            fromfile=str(output), tofile="recompiled", lineterm="",
        )
        for line in list(diff)[:40]:
            typer.echo(line, err=True)
        typer.echo(f"{output} has drifted from the dataset.", err=True)
        raise typer.Exit(code=1)

    if stdout:
        typer.echo(doc, nl=False)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(doc.encode("utf-8"))
    typer.echo(f"Wrote {output} ({len(doc.encode('utf-8'))} bytes).")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
