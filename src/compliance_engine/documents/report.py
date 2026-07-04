"""Audit-package report: render package/manifest.json into a human report.

The signed manifest (traceability/package.py) is the source of truth. This module
renders it into a clean, self-contained HTML report and, when the ``weasyprint``
binary is available, a paged PDF. The PDF is a human rendering of the signed
manifest, not a second source of truth: its cover and footer carry the manifest
hash and signature so a reader can re-verify the underlying package with
``uv run ce verify-package``.

Audience: this document is written to be read by two people at once. A contracting
officer or executive should be able to read the first three sections and know what
the package says and whether to trust it, without knowing what an "oracle" is. An
assessor or engineer should be able to keep reading into the appendices and re-derive
every claim. So every section leads with plain-language prose, then shows the
supporting detail; the dense per-control tables live in the appendices.

Design: minimal, government-report restraint. One serif body face, a single slate
accent, horizontal rules only, no color-coded chrome, no emoji. Print CSS sets a
running header, page numbers, and a repeated NON-EVIDENTIARY stamp on mock runs.

PDF engine: the ``weasyprint`` CLI is invoked via subprocess (its own native libs),
which avoids the Python-binding system-library issues. If the binary is absent, the
HTML is still written and the caller is told to install weasyprint or print the HTML.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]

# Plain-text labels (no emoji) for the coverage/verification kinds.
_KIND_LABEL = {
    "machine": "Machine-verified",
    "attested": "Attested-reference",
    "inherited": "CSP-inherited",
    "unclaimed": "Unclaimed",
}

# NIST SP 800-171 Rev. 2 control families, keyed by the "3.N" id prefix.
_FAMILY = {
    "3.1": "Access Control",
    "3.2": "Awareness and Training",
    "3.3": "Audit and Accountability",
    "3.4": "Configuration Management",
    "3.5": "Identification and Authentication",
    "3.6": "Incident Response",
    "3.7": "Maintenance",
    "3.8": "Media Protection",
    "3.9": "Personnel Security",
    "3.10": "Physical Protection",
    "3.11": "Risk Assessment",
    "3.12": "Security Assessment",
    "3.13": "System and Communications Protection",
    "3.14": "System and Information Integrity",
}


def _esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def _family_of(cid: str) -> str:
    """Return the '3.N' family prefix for a control id like '3.1.1' or 'AC.L2-3.1.1'."""
    match = re.search(r"3\.(\d+)", str(cid))
    return f"3.{match.group(1)}" if match else "other"


def _n(word: str, count: int) -> str:
    """'1 control' / '3 controls' — pluralize a noun for readable prose."""
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


# ---------------------------------------------------------------------------
# Full-catalog coverage (for the appendix) — read live from the graph
# ---------------------------------------------------------------------------

def _catalog_coverage() -> list[dict]:
    """All 110 controls with weight, requirement text, and verification kind
    (machine / attested / inherited), derived from the catalog + structural model."""
    from rdflib import RDF, Graph

    from compliance_engine.ontology.prefixes import CMMC

    catalog = Graph()
    catalog.parse(_REPO_ROOT / "data" / "ontology" / "cmmc-edit.ttl", format="turtle")
    struct = Graph()
    struct.parse(_REPO_ROOT / "data" / "structural" / "tier1.ttl", format="turtle")

    def _cid(node) -> str:
        return str(node).split("#")[-1].split("/")[-1]

    kinds: dict[str, set[str]] = {}
    for module, _p, ctrl in struct.triples((None, CMMC.controlsSatisfied, None)):
        vm = struct.value(module, CMMC.verificationMethod)
        vm_s = str(vm) if vm is not None else ""
        if vm_s.endswith("oracle-attested-reference"):
            kind = "attested"
        elif vm_s.startswith("inherited"):
            kind = "inherited"
        else:
            kind = "machine"
        kinds.setdefault(_cid(ctrl), set()).add(kind)

    def classify(cid: str) -> str:
        ks = kinds.get(cid)
        if not ks:
            return "unclaimed"
        if "attested" in ks:
            return "attested"
        if ks == {"inherited"}:
            return "inherited"
        return "machine"

    rows: list[dict] = []
    for ctrl in catalog.subjects(RDF.type, CMMC.Control):
        cid = str(catalog.value(ctrl, CMMC.controlId) or "")
        if not cid:
            continue
        text = str(catalog.value(ctrl, CMMC.text) or "")
        try:
            weight = int(str(catalog.value(ctrl, CMMC.weight) or "1"))
        except (ValueError, TypeError):
            weight = 1
        rows.append({"id": cid, "weight": weight, "kind": classify(cid), "text": text})
    rows.sort(key=lambda r: (r["id"].split(".")[0], r["id"]))
    return rows


# ---------------------------------------------------------------------------
# Derived, human-facing figures pulled from the manifest
# ---------------------------------------------------------------------------

@dataclass
class _Facts:
    contract: str
    score: object
    status: str
    valid: object
    n_total: int
    n_met: int
    n_notmet: int
    n_machine: int
    n_human: int
    n_override: int
    n_contra: int
    sop_ok: bool
    weak: bool


def _facts(m: dict) -> _Facts:
    sprs = m.get("sprs", {})
    controls = m.get("controls", [])
    pv = m.get("proven_vs_attested", {})
    prov = m.get("provenance", {})
    n_met = sum(1 for c in controls if c.get("status") == "MET")
    n_override = sum(1 for c in controls if c.get("evidence_backing") == "override")
    weak = m.get("evidentiary_status") in {
        "mock", "mock-plan", "attested-reference-mock", "auto", "automatic", "semiAuto",
    }
    return _Facts(
        contract=m.get("contract", ""),
        score=sprs.get("score"),
        status=sprs.get("status", ""),
        valid=sprs.get("valid_submission"),
        n_total=len(controls),
        n_met=n_met,
        n_notmet=len(controls) - n_met,
        n_machine=int(pv.get("machine", 0) or 0),
        n_human=int(pv.get("human_only", 0) or 0),
        n_override=n_override,
        n_contra=len(m.get("contradictions", [])),
        sop_ok=bool(prov.get("sop_adherence_ok")),
        weak=weak,
    )


# ---------------------------------------------------------------------------
# HTML / CSS
# ---------------------------------------------------------------------------

_CSS = """
:root { --ink:#1a1a1a; --slate:#1f3a5f; --muted:#5b6673; --rule:#c9d1da;
        --stamp:#8a1f1f; --wash:#f5f7f9; }
* { box-sizing: border-box; }
html { font-size: 10.5pt; }
body { font-family: Georgia, "Times New Roman", serif; color: var(--ink);
       line-height: 1.5; margin: 0; }
h1,h2,h3 { font-family: Georgia, serif; color: var(--slate); font-weight: 600;
           line-height: 1.25; }
h1 { font-size: 23pt; margin: 0 0 .2em; letter-spacing: -.01em; }
h2 { font-size: 14pt; margin: 1.7em 0 .5em; padding-bottom: .2em;
     border-bottom: 2px solid var(--slate); page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 1.1em 0 .3em; page-break-after: avoid; }
p { margin: .55em 0; }
a { color: var(--slate); }
code, .mono { font-family: "SFMono-Regular", Menlo, Consolas, monospace; font-size: 9pt;
              word-break: break-all; }
.muted { color: var(--muted); }
.small { font-size: 9pt; }
.lede { font-size: 12pt; line-height: 1.6; }
strong, b { color: var(--slate); font-weight: 600; }
table { width: 100%; border-collapse: collapse; margin: .6em 0; font-size: 9pt; }
th { text-align: left; border-bottom: 1.5px solid var(--slate); padding: 4px 8px 4px 0;
     color: var(--slate); font-weight: 600; }
td { border-bottom: .5px solid var(--rule); padding: 4px 8px 4px 0; vertical-align: top; }
tr { page-break-inside: avoid; }
td.num, th.num { text-align: right; padding-right: 1.2em; }
.stat-row { display: flex; gap: 1em; margin: 1em 0; flex-wrap: wrap; }
.stat { border: .5px solid var(--rule); border-top: 2px solid var(--slate);
        padding: .5em .8em; min-width: 7.5em; flex: 1; }
.stat .n { font-size: 16pt; color: var(--slate); font-weight: 600; }
.stat .l { font-size: 8pt; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
.banner { border: 1.5px solid var(--stamp); color: var(--stamp); padding: .7em 1em;
          margin: 1.1em 0; }
.banner .h { font-weight: 700; text-transform: uppercase; letter-spacing: .06em;
             font-size: 9pt; display: block; margin-bottom: .25em; }
.callout { border-left: 3px solid var(--slate); background: var(--wash);
           padding: .6em .9em; margin: 1em 0; }
.callout .h { font-weight: 600; color: var(--slate); text-transform: uppercase;
              letter-spacing: .05em; font-size: 8pt; display: block; margin-bottom: .25em; }
.verdict { font-size: 13.5pt; color: var(--slate); font-weight: 600; line-height: 1.4;
           margin: .8em 0; }
dl.gloss { margin: .6em 0; }
dl.gloss dt { font-weight: 600; color: var(--slate); margin-top: .7em; }
dl.gloss dd { margin: .1em 0 0; }
.kv { margin: .2em 0; }
.kv b { color: var(--slate); font-weight: 600; }
.cover { height: 91vh; display: flex; flex-direction: column; justify-content: center;
         page-break-after: always; }
.cover .sub { font-size: 13pt; color: var(--muted); margin-top: .3em; }
.cover .meta { margin-top: 2.2em; }
.cover .rule { border: none; border-top: 1px solid var(--slate); margin: 1.6em 0; }
hr.soft { border: none; border-top: .5px solid var(--rule); margin: 1.2em 0; }
"""

_PAGE_CSS = """
@page {
  size: Letter; margin: 2.2cm 2cm 2cm 2cm;
  @top-center { content: "%(header)s"; font-family: Georgia, serif; font-size: 8pt;
                color: #5b6673; }
  @bottom-right { content: "Page " counter(page) " of " counter(pages);
                  font-family: Georgia, serif; font-size: 8pt; color: #5b6673; }
  @bottom-left { content: "%(stamp)s"; font-family: Georgia, serif; font-size: 8pt;
                 color: #8a1f1f; }
}
@page :first { @top-center { content: ""; } }
"""


def _stat(n, label) -> str:
    return f'<div class="stat"><div class="n">{_esc(n)}</div><div class="l">{_esc(label)}</div></div>'


# ---------------------------------------------------------------------------
# Sections — each leads with prose, then shows supporting detail
# ---------------------------------------------------------------------------

def _cover(m: dict, sig: dict, manifest_sha: str, f: _Facts) -> str:
    banner = ""
    if f.weak:
        banner = (
            '<div class="banner"><span class="h">Non-evidentiary</span>'
            "This package was produced from mock, demonstration data. It shows exactly what "
            "a real submission looks like end to end, but it is not itself a submittable "
            "government package.</div>"
        )
    return f"""
    <section class="cover">
      <div class="small muted">CMMC Level 2 &middot; NIST SP 800-171 Rev. 2</div>
      <h1>Audit Package</h1>
      <div class="sub">System Security Plan, Bill of Materials, and traceability of record<br>
        for contract <b>{_esc(f.contract)}</b></div>
      <hr class="rule">
      {banner}
      <div class="meta small">
        <div class="kv"><b>SPRS score</b> &nbsp; {_esc(f.score)} &middot; {_esc(f.status)} &middot; valid submission: {_esc(f.valid)}</div>
        <div class="kv"><b>Controls</b> &nbsp; {f.n_met} of {f.n_total} met</div>
        <div class="kv"><b>Signature</b> &nbsp; {_esc(sig.get('sig_algo') or 'unsigned')} &middot; key {_esc(sig.get('key_id') or 'none')}</div>
        <div class="kv"><b>Manifest hash</b> &nbsp; <span class="mono">{_esc(manifest_sha)}</span></div>
        <div class="kv muted" style="margin-top:.8em">Re-verify offline with
          <code>uv run ce verify-package</code>.</div>
      </div>
    </section>
    """


def _overview(m: dict, f: _Facts) -> str:
    """Plain-language summary: the whole story in one screen, no jargon."""
    # Verdict line.
    if f.valid and str(f.status).lower().startswith("final"):
        verdict = (f"This self-assessment is complete and structurally valid. The contractor "
                   f"scores {f.score} on the SPRS scale and met {f.n_met} of the {f.n_total} "
                   f"controls required by this contract.")
    elif str(f.status).lower().startswith("condition"):
        verdict = (f"This self-assessment is conditional: the contractor scores {f.score} and "
                   f"met {f.n_met} of {f.n_total} controls, with the remainder carried on an "
                   f"approved plan of action.")
    else:
        verdict = (f"The contractor scores {f.score} ({f.status}) and met {f.n_met} of "
                   f"{f.n_total} controls required by this contract.")

    # How the coverage breaks down, in plain terms.
    breakdown = (
        f"Of the {_n('control', f.n_total)}, <b>{f.n_machine}</b> are backed by an automated "
        f"technical check that an assessor can re-run for themselves, and <b>{f.n_human}</b> "
        f"rest on documented human judgment &mdash; policy, training, personnel and physical "
        f"controls that no software can measure. That split is expected: roughly a third of "
        f"NIST 800-171 is inherently a matter of process, not configuration."
    )

    # Red-flag sentence.
    if f.n_contra:
        flags = (f"<b>Attention:</b> {_n('control', f.n_contra)} were signed off as met even "
                 f"though the automated check disagreed. Each of those is an override and must "
                 f"carry a written justification; they are listed in the Contradictions section.")
    else:
        flags = ("No control was signed off as met while its automated check said otherwise, "
                 "so there are no unexplained overrides to review.")

    sop = ("The run also followed its documented standard operating procedure with no deviations."
           if f.sop_ok else
           "<b>Note:</b> the run deviated from its documented standard operating procedure; "
           "see the Provenance section.")

    nonev = ""
    if f.weak:
        nonev = (
            '<div class="callout"><span class="h">What "non-evidentiary" means</span>'
            "This particular package was built from mock demonstration data, so it cannot be "
            "submitted to the government. Everything below is real in structure &mdash; the "
            "scoring, the signatures, the verification steps all work exactly as they would on "
            "a live package &mdash; but the underlying evidence is fixtures, not a real system."
            "</div>"
        )

    return f"""
    <h2>What this report says</h2>
    <p class="verdict">{verdict}</p>
    <p class="lede">{breakdown}</p>
    <p class="lede">{flags} {sop}</p>
    {nonev}
    <div class="callout"><span class="h">In one line</span>
    This document is a plain-language rendering of a cryptographically signed package. Nothing
    here has to be taken on trust: the last section shows how any reader can re-check every
    number offline with a single command.</div>
    """


def _how_to_read() -> str:
    """A short glossary so a non-technical reader can follow the rest."""
    return """
    <h2>How to read this report</h2>
    <p>A few terms recur throughout. In plain language:</p>
    <dl class="gloss">
      <dt>Control</dt>
      <dd>One specific security requirement from NIST SP 800-171 &mdash; for example,
          "lock the screen after inactivity" or "keep audit logs." There are 110 in all;
          this contract requires a defined subset.</dd>
      <dt>SPRS score</dt>
      <dd>The single number the Department of Defense uses to summarize a self-assessment.
          It starts at 110 and subtracts a weight (1, 3, or 5) for each control not met.
          A higher number is better; 110 is a perfect score.</dd>
      <dt>Met / not met</dt>
      <dd>A control is recorded as <em>met</em> only when its evidence passed the check for
          it <em>and</em> a named, authorized person signed off. Anything short of both is
          <em>not met</em>.</dd>
      <dt>Machine-verified vs. human-attested</dt>
      <dd>Some controls can be proven by software re-reading system configuration
          (machine-verified). Others &mdash; training, policy, personnel &mdash; can only be
          confirmed by a person reviewing documents (human-attested). Both are legitimate;
          they differ in how an assessor re-checks them.</dd>
      <dt>Override</dt>
      <dd>A control marked met even though its automated check failed. This is allowed, but
          it must carry a written justification and supporting evidence, and it is flagged
          for review.</dd>
      <dt>Signed / verifiable</dt>
      <dd>The whole package is sealed with a digital signature and every file is fingerprinted.
          If anyone changes a single character after signing, re-verification fails. That is
          what lets a reader trust this report without trusting whoever produced it.</dd>
    </dl>
    """


def _score(m: dict, f: _Facts) -> str:
    rows = "".join(_stat(x, l) for x, l in [
        (f"{f.score}", "SPRS score"),
        (f"{f.status}", "Submission status"),
        (str(f.valid), "Structurally valid"),
        (f"{f.n_met} / {f.n_total}", "Controls met"),
        (f"{f.n_machine} / {f.n_human}", "Machine / human"),
        (str(f.n_contra), "Overrides to review"),
    ])
    return f"""
    <h2>The score</h2>
    <p>The SPRS score is computed over the {_n('control', f.n_total)} this contract requires.
    Each control carries a weight of 1, 3, or 5 reflecting how much it matters to protecting
    controlled information; the score is 110 minus the weights of the controls not met. A valid
    submission additionally means no high-weight control was left open on a plan of action where
    the rules forbid it.</p>
    <div class="stat-row">{rows}</div>
    <p class="small muted">These figures are read directly from the signed manifest and are
    reproduced, control by control, in Appendix A.</p>
    """


def _coverage(m: dict, f: _Facts) -> str:
    """Family rollup: the digestible middle layer between the summary and the raw matrix."""
    controls = m.get("controls", [])
    fam: dict[str, dict] = {}
    for c in controls:
        key = _family_of(c.get("control", ""))
        agg = fam.setdefault(key, {"total": 0, "met": 0, "machine": 0, "human": 0, "override": 0})
        agg["total"] += 1
        if c.get("status") == "MET":
            agg["met"] += 1
        backing = c.get("evidence_backing")
        if backing == "machine":
            agg["machine"] += 1
        elif backing == "override":
            agg["override"] += 1
        else:
            agg["human"] += 1

    def _sort_key(k: str):
        mo = re.match(r"3\.(\d+)", k)
        return (0, int(mo.group(1))) if mo else (1, 0)

    rows = ""
    for key in sorted(fam, key=_sort_key):
        agg = fam[key]
        name = _FAMILY.get(key, "Other")
        ov = f" &middot; {agg['override']} override" if agg["override"] else ""
        rows += (
            f"<tr><td><b>{_esc(key)}</b> &nbsp; {_esc(name)}</td>"
            f"<td class='num'>{agg['total']}</td>"
            f"<td class='num'>{agg['met']}</td>"
            f"<td class='num'>{agg['machine']}</td>"
            f"<td class='num'>{agg['human']}{ov}</td></tr>"
        )
    return f"""
    <h2>How each control was verified</h2>
    <p>NIST 800-171 groups its controls into fourteen families &mdash; access control, audit,
    incident response, and so on. The table below rolls the required controls up by family so a
    reader can see, at a glance, where coverage is proven automatically and where it rests on
    human attestation. The full control-by-control detail is in Appendix A.</p>
    <table>
      <thead><tr><th>Family</th><th class="num">Controls</th><th class="num">Met</th>
      <th class="num">Machine</th><th class="num">Human-attested</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """


def _integrity(m: dict, sig: dict, manifest_sha: str) -> str:
    arts = "".join(
        f"<tr><td>{_esc(a.get('name'))}</td><td class='mono'>{_esc(a.get('sha256'))}</td></tr>"
        for a in m.get("artifacts", [])
    )
    return f"""
    <h2>Integrity and verification</h2>
    <p>Nothing in this report has to be taken on faith. Every file in the package is
    fingerprinted with a SHA-256 hash, and the manifest that lists those fingerprints is sealed
    with a digital signature. To re-check the record, an assessor does not have to trust whoever
    produced it &mdash; they re-hash each file, confirm it matches the manifest, and verify the
    signature. If a single byte changed after signing, that check fails.</p>
    <div class="callout"><span class="h">Verify it yourself</span>
    Run <code>uv run ce verify-package</code> against this package. It re-hashes every artifact,
    checks the manifest signature, and walks the chain from each control to the signed policy
    behind it &mdash; entirely offline.</div>
    <div class="kv small"><b>Manifest signature:</b> {_esc(sig.get('sig_algo') or 'unsigned')}, key {_esc(sig.get('key_id') or 'none')}</div>
    <div class="kv small"><b>Manifest hash (SHA-256):</b> <span class="mono">{_esc(manifest_sha)}</span></div>
    <h3>Bundled artifacts</h3>
    <p class="small">The files sealed in this package, each addressable by its hash:</p>
    <table><thead><tr><th>Artifact</th><th>SHA-256 fingerprint</th></tr></thead><tbody>{arts}</tbody></table>
    """


def _provenance(m: dict, f: _Facts) -> str:
    prov = m.get("provenance", {})
    steps = ", ".join(prov.get("executed_steps", []))
    dev = prov.get("deviations", [])
    dev_html = (
        "<p><b>Deviations found:</b> " + _esc("; ".join(dev)) + ". Each deviation is a place "
        "where the run departed from its written procedure and should be reviewed.</p>"
        if dev else
        "<p>The run followed its documented procedure with no deviations.</p>"
    )
    return f"""
    <h2>Provenance</h2>
    <p>Beyond the final numbers, the package records <em>how</em> it was produced. The whole
    lineage &mdash; from the contract, to the obligations it imposes, to the required controls,
    the signed order, the evidence collected, the automated checks, the human sign-offs, and the
    resulting plan and bill of materials &mdash; is captured as a provenance graph and checked
    against the standard operating procedure. This is what lets an assessor confirm the record
    was assembled the way it was supposed to be, not just that the end state looks right.</p>
    <div class="kv"><b>Standard-operating-procedure check:</b> {'passed' if f.sop_ok else 'DEVIATION &mdash; see below'}</div>
    <p class="small"><b>Steps executed:</b> {_esc(steps)}</p>
    {dev_html}
    """


def _contradictions(m: dict, f: _Facts) -> str:
    con = m.get("contradictions", [])
    if not con:
        return ("<h2>Contradictions and overrides</h2><p>There are none. Every control recorded "
                "as met either passed its automated check or had no automated check to disagree "
                "with, so no human sign-off contradicts the machine evidence.</p>")
    rows = "".join(
        f"<tr><td class='mono'>{_esc(c.get('control'))}</td><td>{_esc(c.get('oracle_outcome'))}</td></tr>"
        for c in con
    )
    return f"""
    <h2>Contradictions and overrides</h2>
    <p>The controls below were signed off as met even though the automated check for them did not
    pass. This is permitted &mdash; a person may have evidence the software cannot see &mdash; but
    each one is an override that must carry a written justification and appended evidence, and each
    should be reviewed before the package is relied upon.</p>
    <div class="banner"><span class="h">Review required</span>
    {_n('control', len(con))} attested met over a failed machine check.</div>
    <table><thead><tr><th>Control</th><th>What the automated check found</th></tr></thead>
    <tbody>{rows}</tbody></table>
    """


def _appendix_matrix(m: dict) -> str:
    """The full per-control detail, moved to an appendix where the density belongs."""
    controls = sorted(m.get("controls", []), key=lambda c: _family_of(c.get("control", "")))
    body = ""
    current = None
    for c in controls:
        fam = _family_of(c.get("control", ""))
        if fam != current:
            current = fam
            name = _FAMILY.get(fam, "Other")
            body += (f"<tr><td colspan='6' style='padding-top:.8em;border-bottom:1px solid #1f3a5f;'>"
                     f"<b>{_esc(fam)} &nbsp; {_esc(name)}</b></td></tr>")
        att = c.get("attestation", {})
        refs = ", ".join(r.get("ref", "") for r in c.get("policy_references", [])) or "—"
        body += (
            f"<tr><td class='mono'>{_esc(c.get('control'))}</td>"
            f"<td>{_esc(c.get('status'))}</td>"
            f"<td>{_esc(c.get('evidence_backing'))}</td>"
            f"<td>{_esc(c.get('oracle_outcome') or '—')}</td>"
            f"<td>{_esc(att.get('outcome') or '—')}</td>"
            f"<td class='small'>{_esc(refs)}</td></tr>"
        )
    return f"""
    <h2>Appendix A &mdash; Control-by-control detail</h2>
    <p class="small muted">Evidence backing: <b>machine</b> = sign-off backed by a passing check
    over resolvable evidence; <b>override</b> = met over a failed check (requires written
    justification and appended evidence); <b>human-only</b> = no automated measurement, rests on
    human judgment.</p>
    <table><thead><tr><th>Control</th><th>Status</th><th>Backing</th>
    <th>Automated check</th><th>Attestation</th><th>Policy ref</th></tr></thead>
    <tbody>{body}</tbody></table>
    """


def _appendix_policies(m: dict) -> str:
    pol = m.get("policies", [])
    if not pol:
        return ""
    rows = "".join(
        f"<tr><td class='mono'>{_esc(p.get('ref'))}</td><td class='small'>{_esc(p.get('source'))}</td>"
        f"<td class='small'>{_esc(p.get('version') or '—')}</td>"
        f"<td class='small'>{'signed' if p.get('signature') else '—'}</td></tr>"
        for p in pol
    )
    return f"""
    <h2>Appendix B &mdash; Signed-policy inventory</h2>
    <p class="small">The authoritative source documents behind the attested (policy) controls.
    Each resolves to a version-pinned artifact and is checked for freshness and a
    role-appropriate signature.</p>
    <table><thead><tr><th>Reference</th><th>Source</th><th>Version</th><th>Signature</th></tr></thead>
    <tbody>{rows}</tbody></table>
    """


def _appendix_catalog(m: dict) -> str:
    try:
        catalog = _catalog_coverage()
    except Exception:
        return ""
    in_scope = {c.get("control") for c in m.get("controls", [])}
    rows = "".join(
        f"<tr><td class='mono'>{_esc(r['id'])}</td><td class='num'>{_esc(r['weight'])}</td>"
        f"<td class='small'>{_esc(_KIND_LABEL.get(r['kind'], r['kind']))}</td>"
        f"<td>{'yes' if r['id'] in in_scope else '—'}</td>"
        f"<td class='small'>{_esc(r['text'][:80] + ('…' if len(r['text']) > 80 else ''))}</td></tr>"
        for r in catalog
    )
    n_mac = sum(1 for r in catalog if r["kind"] == "machine")
    n_att = sum(1 for r in catalog if r["kind"] == "attested")
    n_inh = sum(1 for r in catalog if r["kind"] == "inherited")
    return f"""
    <h2>Appendix C &mdash; Full control catalog (all 110)</h2>
    <p class="small">The complete NIST SP 800-171 Rev. 2 catalog and how each control is verified
    in the model: {n_mac} machine-verified, {n_att} attested-reference, {n_inh} CSP-inherited.
    "In this order" marks the controls this contract requires and scores above; the rest are out
    of scope for this order.</p>
    <table><thead><tr><th>Control</th><th class="num">Wt</th><th>Verified by</th>
    <th>In this order</th><th>Requirement</th></tr></thead><tbody>{rows}</tbody></table>
    """


def build_report_html(manifest: dict, sig: dict) -> str:
    """Render the manifest + signature into a self-contained HTML report string."""
    manifest_sha = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    f = _facts(manifest)
    header = f"{manifest.get('contract', '')} · CMMC L2 Audit Package"
    stamp = "NON-EVIDENTIARY" if f.weak else ""
    page_css = _PAGE_CSS % {"header": _esc(header), "stamp": stamp}
    body = "".join([
        _cover(manifest, sig, manifest_sha, f),
        _overview(manifest, f),
        _how_to_read(),
        _score(manifest, f),
        _coverage(manifest, f),
        _integrity(manifest, sig, manifest_sha),
        _provenance(manifest, f),
        _contradictions(manifest, f),
        _appendix_matrix(manifest),
        _appendix_policies(manifest),
        _appendix_catalog(manifest),
        '<hr class="soft"><p class="small muted">This report renders the signed audit-package '
        'manifest. The manifest is the source of truth; this document is a human rendering of it. '
        'Re-verify with <code>uv run ce verify-package</code>.</p>',
    ])
    return (f"<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
            f"<title>{_esc(header)}</title><style>{_CSS}{page_css}</style></head>"
            f"<body>{body}</body></html>")


# ---------------------------------------------------------------------------
# Render (HTML + PDF)
# ---------------------------------------------------------------------------

@dataclass
class ReportResult:
    html_path: Path
    pdf_path: Path | None
    pdf_engine: str | None      # "weasyprint" or None
    note: str = ""


def weasyprint_available() -> bool:
    return shutil.which("weasyprint") is not None


def render_report(package_dir: Path, *, out_dir: Path | None = None) -> ReportResult:
    """Read package/manifest.json (+ manifest.sig), write report.html, and produce
    report.pdf via the weasyprint CLI when available. Degrades to HTML-only otherwise.

    By default the report is written into ``package_dir`` itself, so a built package
    always carries its own human-readable rendering alongside the signed manifest."""
    package_dir = Path(package_dir)
    out_dir = Path(out_dir) if out_dir else package_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = package_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"no manifest.json in {package_dir}; build the package first "
            f"(uv run ce package)."
        )
    manifest = json.loads(manifest_path.read_text())
    sig_path = package_dir / "manifest.sig"
    sig = json.loads(sig_path.read_text()) if sig_path.exists() else {}

    html_str = build_report_html(manifest, sig)
    html_path = out_dir / "report.html"
    html_path.write_text(html_str, encoding="utf-8")

    if not weasyprint_available():
        return ReportResult(
            html_path=html_path, pdf_path=None, pdf_engine=None,
            note=("weasyprint not found; wrote HTML only. Install weasyprint "
                  "(https://weasyprint.org) or open report.html and print to PDF."),
        )
    pdf_path = out_dir / "report.pdf"
    try:
        subprocess.run(
            ["weasyprint", str(html_path), str(pdf_path)],
            check=True, capture_output=True, timeout=120,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        detail = getattr(exc, "stderr", b"")
        detail = detail.decode("utf-8", "replace")[:200] if isinstance(detail, bytes) else str(exc)
        return ReportResult(
            html_path=html_path, pdf_path=None, pdf_engine=None,
            note=f"weasyprint failed ({detail}); wrote HTML only.",
        )
    return ReportResult(html_path=html_path, pdf_path=pdf_path, pdf_engine="weasyprint")
