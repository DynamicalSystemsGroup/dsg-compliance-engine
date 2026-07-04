"""Interrogation utilities for the CMMC compliance notebook.

Provides three functions for the walkthrough notebook:

  explain_control(control_id, factory_state, audit_report, bom_result) -> str
      Multi-line plain-text answer to "How do we know {control_id} is met?",
      covering oracle outcome, attestation, evidence nodes, backing, and SPRS weight.

  live_hash_demo(factory_state) -> dict
      Picks the first evidence node and demonstrates hash tamper-detection by
      computing sha256(original_hash + "TAMPERED") and confirming mismatch.

  sprs_breakdown(audit_report, required) -> list[dict]
      One row per required control, suitable for a marimo table: weight, oracle,
      attestation, backing, SPRS impact, and pass/fail status.

No marimo imports. All three functions are defensive: exceptions return sensible
fallbacks rather than raising.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Lazy coverage lookup  (text, weight, non_deferrable)
# Reads tier1.ttl + cmmc-edit.ttl via _engine.get_coverage_data() from the
# same notebooks/ directory. Cached after the first call.
# ---------------------------------------------------------------------------

_COVERAGE_CACHE: dict[str, dict] | None = None


def _coverage_lookup() -> dict[str, dict]:
    """Return {control_id: row_dict} from the CMMC catalog, cached after first call."""
    global _COVERAGE_CACHE
    if _COVERAGE_CACHE is not None:
        return _COVERAGE_CACHE
    try:
        _nb = str(Path(__file__).parent)
        if _nb not in sys.path:
            sys.path.insert(0, _nb)
        import _engine  # type: ignore[import]
        _COVERAGE_CACHE = {row["id"]: row for row in _engine.get_coverage_data()}
    except Exception:
        _COVERAGE_CACHE = {}
    return _COVERAGE_CACHE


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _short_iri(iri: Any) -> str:
    """Return the local name of an IRI (after the last / or #)."""
    s = str(iri)
    return s.rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def _safe_get(obj: Any, attr: str, default: Any = None) -> Any:
    """getattr with a default; never raises."""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


# ---------------------------------------------------------------------------
# 1. explain_control
# ---------------------------------------------------------------------------

def explain_control(
    control_id: str,
    factory_state: Any,
    audit_report: Any,
    bom_result: Any,
) -> str:
    """Return a multi-line plain-text string explaining how control_id is met.

    Format::

        {control_id} — {short requirement text}
          Oracle outcome : {passed/failed/cantTell/not run}
          Attestation    : {MET/NOT MET/not attested}
          Evidence nodes : {count}
            {ev_hash[:16]}... -> {summary key preview}
          Backing        : {machine/human-only/override/unattested}
          SPRS weight    : {weight}
          Non-deferrable : {yes/no/?}

    Returns a sentinel string if the control was not in scope for this run.
    """
    try:
        # --- Locate this control in the BOM control_mapping ---
        bom_row = None
        if bom_result is not None:
            mapping = _safe_get(bom_result, "control_mapping", ()) or ()
            for row in mapping:
                if _safe_get(row, "control_id") == control_id:
                    bom_row = row
                    break

        # --- Guard: was this control in scope at all? ---
        audit_required: list[str] = list(_safe_get(audit_report, "required_controls", []) or [])
        if bom_row is None and control_id not in audit_required:
            return f"— no data for {control_id} in this run —"

        # --- Oracle outcome ---
        oracle_str = "not run"
        oracles = _safe_get(factory_state, "oracles")
        if oracles is not None:
            outcomes: dict[str, str] = _safe_get(oracles, "outcomes", {}) or {}
            oracle_str = outcomes.get(control_id, "not run")
        # Fallback: bom_result.oracle_outcomes (same data, different surface)
        if oracle_str == "not run" and bom_result is not None:
            bom_outcomes: dict[str, str] = _safe_get(bom_result, "oracle_outcomes", {}) or {}
            oracle_str = bom_outcomes.get(control_id, "not run")

        # --- Attestation outcome (human Gate-2 sign-off) ---
        if bom_row is not None:
            # BOM status is already the human-readable determination label
            attestation_str = _safe_get(bom_row, "status", "not attested") or "not attested"
        else:
            met_ids: list[str] = list(_safe_get(audit_report, "met_control_ids", []) or [])
            attestation_str = "MET" if control_id in met_ids else "NOT MET"

        # --- Evidence nodes ---
        # Primary source: BOM row evidence_hashes (SHA-256 hex strings)
        ev_hashes: tuple[str, ...] = ()
        if bom_row is not None:
            ev_hashes = _safe_get(bom_row, "evidence_hashes", ()) or ()

        # Summaries: evidence_index entries filtered by this control.
        # Runner populates evidence_index in the same order as evidence_hashes,
        # so we can pair by index for summary previews.
        ev_index: list[dict] = list(_safe_get(factory_state, "evidence_index", []) or [])
        ev_entries_for_control = [
            e for e in ev_index if control_id in (e.get("controls") or [])
        ]

        ev_count = len(ev_hashes) if ev_hashes else len(ev_entries_for_control)
        ev_lines: list[str] = []

        if ev_hashes:
            for i, h in enumerate(ev_hashes[:3]):
                summary_preview = "—"
                if i < len(ev_entries_for_control):
                    summary = ev_entries_for_control[i].get("summary") or {}
                    if summary:
                        keys = list(summary.keys())[:2]
                        summary_preview = ", ".join(
                            f"{k}={str(summary[k])!r}" for k in keys
                        )
                ev_lines.append(f"    {h[:16]}... -> {summary_preview}")
            if len(ev_hashes) > 3:
                ev_lines.append(f"    ... ({len(ev_hashes) - 3} more)")
        elif ev_entries_for_control:
            # No BOM row but have evidence_index entries (e.g. halted pipeline)
            for entry in ev_entries_for_control[:3]:
                iri_short = _short_iri(entry.get("iri", "?"))
                summary = entry.get("summary") or {}
                if summary:
                    keys = list(summary.keys())[:2]
                    summary_preview = ", ".join(
                        f"{k}={str(summary[k])!r}" for k in keys
                    )
                else:
                    summary_preview = "—"
                ev_lines.append(f"    {iri_short[:16]}... -> {summary_preview}")

        # --- Backing (machine / human-only / override / unattested) ---
        backing_str = "unattested"
        if bom_row is not None:
            try:
                backing_str = bom_row.evidence_backing  # property on ControlMappingRow
            except Exception:
                backing_str = _safe_get(bom_row, "evidence_backing", "unattested") or "unattested"

        # --- SPRS weight + non-deferrable from catalog ---
        coverage = _coverage_lookup()
        ctrl_info = coverage.get(control_id, {})
        weight = ctrl_info.get("weight", "?")
        non_def = ctrl_info.get("non_deferrable", None)
        non_def_str = "yes" if non_def is True else ("no" if non_def is False else "?")

        # --- Short requirement text (first 80 chars of catalog text) ---
        text: str = ctrl_info.get("text", "") or ""
        if text:
            header_suffix = f" — {text[:80]}{'...' if len(text) > 80 else ''}"
        else:
            header_suffix = ""

        lines = [
            f"{control_id}{header_suffix}",
            f"  Oracle outcome : {oracle_str}",
            f"  Attestation    : {attestation_str}",
            f"  Evidence nodes : {ev_count}",
            *ev_lines,
            f"  Backing        : {backing_str}",
            f"  SPRS weight    : {weight}",
            f"  Non-deferrable : {non_def_str}",
        ]
        return "\n".join(lines)

    except Exception as exc:
        return f"— explain_control error for {control_id}: {exc} —"


# ---------------------------------------------------------------------------
# 2. live_hash_demo
# ---------------------------------------------------------------------------

def live_hash_demo(factory_state: Any) -> dict:
    """Demonstrate hash tamper-detection on the first evidence node.

    Picks factory_state.evidence_index[0], retrieves the recorded content hash,
    then computes sha256(original_hash + "TAMPERED") to simulate a tampered read.
    The two hashes always differ, so match is always False.

    Returns:
        ev_id           -- short IRI of the chosen evidence node
        original_hash   -- the content hash recorded in the pipeline
        controls        -- which controls this node addresses
        tampered_hash   -- sha256 of original_hash + "TAMPERED"
        match           -- always False
        message         -- "TAMPERING DETECTED: hash mismatch on {ev_id}"
    """
    try:
        ev_index: list[dict] = list(_safe_get(factory_state, "evidence_index", []) or [])
        if not ev_index:
            return {
                "ev_id": "—",
                "original_hash": "",
                "controls": [],
                "tampered_hash": hashlib.sha256(b"TAMPERED").hexdigest(),
                "match": False,
                "message": "TAMPERING DETECTED: no evidence nodes recorded in this run",
            }

        entry = ev_index[0]
        ev_iri = entry.get("iri", "?")
        ev_id = _short_iri(ev_iri)
        controls: list[str] = list(entry.get("controls") or [])

        # --- Retrieve the recorded content hash ---
        # Primary path: pair evidence_index[0] with evidence.evidence_hashes[0].
        # Runner appends hashes in the same loop order as evidence_index entries,
        # so index-based pairing is safe for the first element.
        original_hash = ""
        ev_stage = _safe_get(factory_state, "evidence")
        if ev_stage is not None:
            all_hashes = _safe_get(ev_stage, "evidence_hashes", ()) or ()
            if all_hashes:
                original_hash = str(all_hashes[0])

        # Fallback: query the RDF Dataset for CE.contentHash on the evidence IRI.
        if not original_hash:
            try:
                from compliance_engine.ontology.prefixes import CE  # noqa: PLC0415
                ds = _safe_get(factory_state, "ds")
                if ds is not None:
                    ch = ds.value(ev_iri, CE.contentHash)
                    if ch is not None:
                        original_hash = str(ch)
            except Exception:
                pass

        # Simulate tampering: append "TAMPERED" suffix and re-hash.
        tampered_hash = hashlib.sha256(
            (original_hash + "TAMPERED").encode("utf-8")
        ).hexdigest()

        return {
            "ev_id": ev_id,
            "original_hash": original_hash,
            "controls": controls,
            "tampered_hash": tampered_hash,
            "match": False,
            "message": f"TAMPERING DETECTED: hash mismatch on {ev_id}",
        }

    except Exception as exc:
        return {
            "ev_id": "—",
            "original_hash": "",
            "controls": [],
            "tampered_hash": hashlib.sha256(b"error").hexdigest(),
            "match": False,
            "message": f"TAMPERING DETECTED: live_hash_demo error: {exc}",
        }


# ---------------------------------------------------------------------------
# 3. sprs_breakdown
# ---------------------------------------------------------------------------

def sprs_breakdown(audit_report: Any, required: list[str]) -> list[dict]:
    """Return a list of row dicts, one per required control, for a marimo table.

    Columns:
        Control      -- control id
        Wt           -- SPRS weight (int, from catalog; 1 if unknown)
        Oracle       -- oracle outcome derived from audit_report or "—"
        Attestation  -- "MET" | "NOT MET"
        Backing      -- "machine" | "human-only" | "override" | "—"
        SPRS impact  -- "-{weight}" if not MET, "0" if MET, "?" if no catalog entry
        Status       -- "PASS" | "FAIL" | "UNRESOLVED"

    Oracle and backing are derived from audit_report.proven (met_by_machine /
    met_by_human_only) and audit_report.contradictions. Controls that are MET
    and backed by a passing machine oracle appear in met_by_machine; those MET
    by human judgement only appear in met_by_human_only; contradictions carry
    the oracle outcome that contradicts the MET attestation.
    """
    try:
        coverage = _coverage_lookup()

        # Build per-control lookup structures from audit_report
        met_ids: set[str] = set(_safe_get(audit_report, "met_control_ids", []) or [])
        ar_required: set[str] = set(_safe_get(audit_report, "required_controls", []) or [])

        proven = _safe_get(audit_report, "proven")
        met_by_machine: set[str] = set(_safe_get(proven, "met_by_machine", []) or [])
        met_by_human: set[str] = set(_safe_get(proven, "met_by_human_only", []) or [])

        # Contradiction map: control_id -> oracle_outcome ("failed" | "absent")
        contradiction_oracle: dict[str, str] = {}
        for c in (_safe_get(audit_report, "contradictions", []) or []):
            cid = _safe_get(c, "control", "")
            if cid:
                contradiction_oracle[cid] = _safe_get(c, "oracle_outcome", "failed") or "failed"

        rows: list[dict] = []
        for cid in required:
            ctrl_info = coverage.get(cid, {})
            weight_raw = ctrl_info.get("weight", None)
            try:
                weight: int = int(weight_raw) if weight_raw is not None else 1
            except (TypeError, ValueError):
                weight = 1

            # Oracle outcome (inferred from audit_report)
            if cid in met_by_machine:
                oracle = "passed"
            elif cid in contradiction_oracle:
                oracle = contradiction_oracle[cid]     # "failed" or "absent"
            elif cid in met_by_human:
                oracle = "cantTell"
            else:
                oracle = "—"

            # Attestation
            attestation = "MET" if cid in met_ids else "NOT MET"

            # Backing
            if cid in met_by_machine:
                backing = "machine"
            elif cid in contradiction_oracle and cid in met_ids:
                # Attested MET despite failing oracle — treated as override attempt
                backing = "override"
            elif cid in met_by_human or cid in met_ids:
                backing = "human-only"
            else:
                backing = "—"

            # SPRS impact
            if cid in met_ids:
                sprs_impact = "0"
            elif ctrl_info:
                sprs_impact = f"-{weight}"
            else:
                sprs_impact = "?"

            # Status
            if cid in met_ids:
                status = "PASS"
            elif cid in ar_required or oracle != "—":
                status = "FAIL"
            else:
                status = "UNRESOLVED"

            rows.append({
                "Control": cid,
                "Wt": weight,
                "Oracle": oracle,
                "Attestation": attestation,
                "Backing": backing,
                "SPRS impact": sprs_impact,
                "Status": status,
            })

        return rows

    except Exception as exc:
        return [{
            "Control": f"error: {exc}",
            "Wt": 0,
            "Oracle": "—",
            "Attestation": "—",
            "Backing": "—",
            "SPRS impact": "?",
            "Status": "UNRESOLVED",
        }]
