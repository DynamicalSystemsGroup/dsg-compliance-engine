"""Compliance engine - end-to-end walkthrough (follow one contract through the line).

A reactive marimo notebook that runs the real engine and follows a single artifact
all the way down the assembly line: a signed contract becomes obligations, becomes a
required-control set, becomes a signed Order, is executed by the Runtime, is attested
by a human, and comes out the far end as an audit, an SPRS score, a BOM, and an SSP.

It is one continuous scroll, not a set of tabs. Each station shows what goes IN and
what comes OUT, in plain English on top and with the real engine payload underneath.
A sidebar rail tracks where the artifact currently is.

Pick a scenario in the sidebar and the whole chain re-executes on the real engine
code. Fixture evidence, terraform in preview with mock providers, nothing deployed -
every output stamped NON-EVIDENTIARY.

Run it (from the repo root):
    uv run --group notebook marimo edit notebooks/compliance_walkthrough.py
Read-only app:
    uv run --group notebook marimo run notebooks/compliance_walkthrough.py
"""

import marimo

__generated_with = "0.23.13"
app = marimo.App(width="full")


# ═══════════════════════════════════════════════════════════════════════════════
# Imports + engine setup
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell(hide_code=True)
def _():
    import sys as _sys
    from pathlib import Path as _Path

    try:
        _here = _Path(__file__).resolve().parent
    except NameError:
        _here = _Path.cwd()
        if _here.name != "notebooks" and (_here / "notebooks").is_dir():
            _here = _here / "notebooks"
    for _p in (str(_here), str(_here.parent)):
        if _p not in _sys.path:
            _sys.path.insert(0, _p)

    import marimo as mo
    import _engine as engine

    return engine, mo


# ═══════════════════════════════════════════════════════════════════════════════
# Presentation helpers
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell(hide_code=True)
def _(mo):
    def short(value, n=14):
        _s = str(value or "")
        return _s[:n] + "…" if len(_s) > n else _s

    def join(items, sep=", "):
        return sep.join(str(x) for x in items) if items else "—"

    def table(rows, page_size=None):
        """Read-only interactive data grid (not a markdown table)."""
        if not rows:
            return mo.md("_(none)_")
        _paginate = page_size is not None and len(rows) > page_size
        return mo.ui.table(
            rows,
            selection=None,
            pagination=_paginate,
            page_size=page_size or max(1, len(rows)),
            show_column_summaries=False,
        )

    def station(number, title, tagline):
        """A numbered station header with a one-line plain-English tagline."""
        return mo.md(
            f"## Station {number} — {title}\n\n"
            f"<span style='opacity:0.75'>{tagline}</span>"
        )

    def io_flow(in_label, in_body, out_label, out_body):
        """Side-by-side 'what goes in' -> 'what comes out' for one hop."""
        _in = mo.callout(mo.md(f"**IN · {in_label}**\n\n{in_body}"), kind="neutral")
        _out = mo.callout(mo.md(f"**OUT · {out_label}**\n\n{out_body}"), kind="info")
        return mo.hstack([_in, _out], widths=[1, 1], gap="1rem")

    def illustration(body_md):
        """A clearly-fenced illustrative panel (NOT engine output)."""
        return mo.callout(
            mo.md("**Illustration — not engine output**\n\n" + body_md),
            kind="neutral",
        )

    return illustration, io_flow, join, short, station, table


# ═══════════════════════════════════════════════════════════════════════════════
# The reactive spine - one scenario drives every cell below
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(engine, mo):
    scenario = mo.ui.dropdown(
        options=list(engine.SCENARIOS),
        value="all-covered",
        label="Scenario",
    )
    return (scenario,)


@app.cell(hide_code=True)
def _(mo, scenario):
    # The header: the scenario picker sits at the very top. Changing it re-executes
    # the whole chain on the real engine — the arc is the point.
    header = mo.vstack(
        [
            mo.md("# One contract, followed end to end"),
            mo.md(
                "<span style='font-size:1.05rem;opacity:0.85'>A signed defense contract "
                "enters at Station 1 and is followed down the whole assembly line until it "
                "comes out as the documents an assessor reads. Every number below is produced "
                "by running the <b>real engine</b>.</span>"
            ),
            scenario,
            mo.callout(
                mo.md(
                    "**Pick a scenario — the whole notebook re-executes.**  \n"
                    "- **`all-covered`** — the full chain proves out: SPRS 110, Final.  \n"
                    "- **`gap`** — Gate 1 refuses. Nothing is built, nothing is proven.  \n"
                    "- **`contradiction`** — a human signs MET over a failed machine check; "
                    "the audit surfaces it on its own line.  \n\n"
                    "The arc *is* the point: change the input, watch the line respond."
                ),
                kind="info",
            ),
        ],
        gap=0.6,
    )
    return (header,)


@app.cell
def _(engine, scenario):
    ds, obligations = engine.build_dataset(scenario.value)
    return ds, obligations


@app.cell
def _(engine, obligations):
    obl_rows = engine.obligation_rows(obligations)
    required, markers = engine.required_control_set(obligations)
    return markers, obl_rows, required


@app.cell
def _(ds, engine, obligations):
    cop_att = engine.attest_cop_step(ds, obligations)
    return (cop_att,)


@app.cell
def _(ds, engine, required):
    g1 = engine.gate1_preview(required, ds)
    return (g1,)


@app.cell
def _(cop_att, ds, engine, obligations):
    order, refusal = engine.compile_order_or_refusal(ds, obligations, cop_att)
    order_ok = order is not None
    return order, order_ok, refusal


@app.cell
def _(ds, engine, order, order_ok, scenario):
    if not order_ok:
        factory_ok, factory_state, outdir = False, None, None
    else:
        outdir = engine.new_output_dir()
        factory_state = engine.run_factory_step(ds, order, scenario.value, outdir)
        factory_ok = not factory_state.halted
    return factory_ok, factory_state, outdir


@app.cell
def _(ds, engine, factory_ok, factory_state):
    attested = 0 if not factory_ok else engine.attest_step(ds, factory_state)
    return (attested,)


@app.cell
def _(ds, engine, factory_ok, outdir):
    audit_report = None if not factory_ok else engine.audit_step(ds, outdir)
    return (audit_report,)


@app.cell
def _(ds, engine, factory_ok, factory_state, outdir):
    bom_result = None if not factory_ok else engine.bom_step(factory_state, ds, outdir)
    return (bom_result,)


@app.cell
def _(audit_report, bom_result, ds, engine, factory_ok, outdir):
    ssp_md = "" if not factory_ok else engine.ssp_step(ds, audit_report, bom_result, outdir)
    return (ssp_md,)


@app.cell
def _(ds, engine):
    graph_counts = engine.named_graph_counts(ds)
    return (graph_counts,)


@app.cell
def _(engine):
    # Static structural facts (independent of the scenario): how each of the 110
    # controls is verified, and the attested-reference records behind Track B.
    coverage = engine.get_coverage_data()
    reference_rows = engine.get_reference_data()
    sources = engine.authoritative_sources()
    return coverage, reference_rows, sources


# ═══════════════════════════════════════════════════════════════════════════════
# Figures - each chart is produced by a real _viz factory over the live run.
# The code that builds each figure is left visible on purpose (ADCS-style): the
# function call tells you exactly where the picture comes from.
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(factory_ok, factory_state, mo):
    import _viz  # noqa: PLC0415

    oracle_fig = None
    if factory_ok and factory_state is not None:
        oracle_fig = mo.as_html(_viz.oracle_outcomes_chart(factory_state.oracles.outcomes))
    return (oracle_fig,)


@app.cell
def _(audit_report, factory_ok, mo):
    import _viz  # noqa: PLC0415

    sprs_fig = None
    if factory_ok and audit_report is not None:
        sprs_fig = mo.as_html(_viz.sprs_gauge(audit_report.sprs.score, audit_report.sprs.status))
    return (sprs_fig,)


@app.cell
def _(audit_report, factory_ok, factory_state, mo, order, order_ok, required):
    import _viz  # noqa: PLC0415

    graph_fig = None
    if factory_ok and order_ok and audit_report is not None:
        graph_fig = mo.as_html(_viz.traceability_graph(
            list(required),
            factory_state.oracles.outcomes,
            list(order.included_modules),
            audit_report.contradictions,
        ))
    return (graph_fig,)


@app.cell
def _(coverage, mo):
    import _viz  # noqa: PLC0415

    coverage_fig = mo.as_html(_viz.coverage_family_chart(coverage))
    return (coverage_fig,)


# ═══════════════════════════════════════════════════════════════════════════════
# Sidebar - scenario selector + compact progress + SPRS badge + live indicators
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(
    audit_report,
    factory_ok,
    g1,
    mo,
    order,
    order_ok,
    required,
    scenario,
):
    # --- SPRS badge: the single headline number, colour-coded ---
    if factory_ok and audit_report is not None:
        _s = audit_report.sprs
        _bg = "#27ae60" if str(_s.status).lower().startswith("final") else (
            "#f39c12" if str(_s.status).lower().startswith("condition") else "#e74c3c")
        _badge_txt = f"SPRS {_s.score} &middot; {_s.status}"
    else:
        _bg, _badge_txt = "#e74c3c", "SPRS &mdash; &middot; REFUSED"
    _badge = mo.md(
        f"<div style='background:{_bg};color:white;font-weight:700;font-size:1.15rem;"
        f"text-align:center;padding:.5rem;border-radius:6px;letter-spacing:.02em'>"
        f"{_badge_txt}</div>"
    )

    # --- compact one-line progress (replaces the full rail; the stations ARE the rail) ---
    _progress = ("Contract &rarr; Controls &rarr; COP &rarr; **Gate 1 PASS** &rarr; Order "
                 "&rarr; Runtime &rarr; **Gate 2** &rarr; Proof") if (order_ok and factory_ok) \
        else "Contract &rarr; Controls &rarr; COP &rarr; **Gate 1 REFUSED** &mdash; line stops"

    # --- live indicators ---
    _stat_items = [
        mo.stat(value=str(len(required)), label="Controls required", caption="by this Order", bordered=True),
        mo.stat(
            value=str(len(order.included_modules)) if order_ok else "—",
            label="Modules claimed", caption="build blocks", bordered=True,
        ),
        mo.stat(
            value="PASS" if g1.passed else "REFUSED",
            label="Gate 1", caption="planning coverage", bordered=True,
        ),
    ]
    if factory_ok and audit_report is not None:
        _stat_items += [
            mo.stat(
                value=f"{audit_report.proven.machine_count} / {audit_report.proven.human_count}",
                label="Machine / human", caption="proven vs attested", bordered=True,
            ),
            mo.stat(
                value=str(len(audit_report.contradictions)),
                label="Contradictions", caption="MET over failed check", bordered=True,
            ),
        ]

    mo.sidebar(
        [
            mo.md("# Compliance engine"),
            mo.md("<span style='opacity:0.8'>Building the secure environment and "
                  "proving it is compliant are one action.</span>"),
            mo.md("---"),
            scenario,
            mo.md("---"),
            _badge,
            mo.md(f"<span style='font-size:0.82rem;opacity:0.8'>{_progress}</span>"),
            mo.md("---"),
            mo.md("### Live indicators"),
            mo.vstack(_stat_items, gap=0.4),
            mo.md("---"),
            mo.callout(
                mo.md("**NON-EVIDENTIARY.** Fixture evidence, mock providers, nothing "
                      "deployed. Not a real submission."),
                kind="warn",
            ),
        ]
    )
    return


# ═══════════════════════════════════════════════════════════════════════════════
# Prologue - how this notebook is built (design rationale)
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell(hide_code=True)
def _(graph_counts, mo):
    _total_triples = sum(int(r.get("triples", 0)) for r in graph_counts)
    prologue = mo.vstack(
        [
            mo.md("## How this notebook is built"),
            mo.accordion(
                {
                    "Why RDF, not a database": mo.md(
                        "Bidirectional audit requires graph traversal. SPARQL can ask "
                        "*\"what evidence addresses this control?\"* and "
                        "*\"what controls does this evidence support?\"* in the same "
                        "query over a single named graph. A relational database requires "
                        "two separate queries joined by a foreign key — and that join can "
                        "go stale if either side is updated independently. The RDF dataset "
                        "here is not a convenience; it is the mechanism that keeps the BOM "
                        "and the SSP byte-for-byte consistent with the attestation records "
                        "that produced them."
                    ),
                    "Why EARL outcomes, not pass/fail": mo.md(
                        "Every control resolves to a *concrete* outcome — the engine never "
                        "shrugs. A machine control returns `passed` / `failed` from its config "
                        "oracle. A policy control returns `passed` / `needsAction` / `failed` "
                        "from the attested-reference oracle: `needsAction` is *actionable* — a "
                        "registered reference is stale, unsigned, or unresolvable, and names the "
                        "concrete remediation. Binary pass/fail would collapse this and either "
                        "inflate the score (counting untested controls as passed) or deflate it "
                        "(counting them as failed); neither is honest. Every required control "
                        "lands on exactly one of `passed` / `failed` / `needsAction`."
                    ),
                    "Why SHACL shapes": mo.md(
                        "SHACL shapes are machine-enforceable closure rules that any "
                        "C3PAO can run independently. The shapes define what a "
                        "well-formed attestation looks like — required predicates, "
                        "allowed value ranges, mandatory signer roles — and running them "
                        "produces the same result regardless of who runs them or on whose "
                        "hardware. A prose policy document requires a human to decide "
                        "whether a given record conforms; a SHACL shape makes that "
                        "decision reproducible and auditable. The shapes live in "
                        "`ce:ontology` and are applied by `ce verify-package`."
                    ),
                }
            ),
            mo.md(
                "### The 8 named graphs in this dataset\n\n"
                "| Named graph | Content |\n"
                "|---|---|\n"
                "| `ce:ontology` | TBox — control catalog, shape definitions |\n"
                "| `ce:plan` | P-PLAN process model (one step per stage) |\n"
                "| `ce:structural` | SysML-style module + control claims |\n"
                "| `ce:order` | The signed Order for this run |\n"
                "| `ce:evidence` | Evidence artifacts with content hashes |\n"
                "| `ce:attestations` | EARL attestation records |\n"
                "| `ce:plan_execution` | P-PLAN Activity instances (per stage) |\n"
                "| `ce:audit` | Forward/backward audit summary |\n"
            ),
            mo.callout(
                mo.md(
                    f"**This run produced {_total_triples:,} triples across "
                    f"{len(graph_counts)} named graphs** — live, from the scenario selected "
                    "above. Every station below reads from this one dataset."
                ),
                kind="neutral",
            ),
        ],
        gap=1.0,
    )
    return (prologue,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 0 - the whole picture, the two ideas, the honest limits
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(mo):
    s0_open = mo.vstack(
        [
            mo.md(
                "## Station 0 — the whole picture\n\n"
                "This notebook takes a single artifact — a signed defense contract — "
                "and follows it down the whole assembly line, watching it change shape at "
                "each station until it comes out the far end as the documents an assessor "
                "reads. Every number and payload below is produced by running the **real "
                "engine**; nothing here is mocked-up narration."
            ),
            mo.callout(
                mo.md(
                    "**The two ideas that do the work.**\n\n"
                    "1. **Provisioning and proving are the same action.** The environment is "
                    "described by a signed Order, and the proof of compliance is produced "
                    "from that same description — not gathered afterward by inspection. "
                    "The description and the proof cannot drift apart because they are not "
                    "two separate things.\n\n"
                    "2. **The attested-reference model.** Every control — whether a "
                    "machine can measure it or only a person can vouch for it — points "
                    "at an *authoritative source* where its truth actually lives, and carries "
                    "a *reference* into that source. The engine runs one uniform check "
                    "(registered, resolves, fresh, signed by the right role); a human makes "
                    "the final MET call. Because that check does not depend on the control "
                    "being machine-measurable, coverage reaches all **110** controls, not "
                    "just the technical subset."
                ),
                kind="info",
            ),
        ]
    )
    return (s0_open,)


@app.cell
def _(mo):
    s0_map = mo.vstack(
        [
            mo.md("### The line, at a glance"),
            mo.md(
                "Two machines, one seam. The **Order Compiler** decides *what must be true* "
                "and emits a signed Order. The **Runtime** (the Factory) makes it true and "
                "proves it. The Order is the only thing that passes between them."
            ),
            mo.mermaid(
                """
                flowchart LR
                    C["Contract<br/>(NV012)"] --> O["Obligations"]
                    O --> R["Required<br/>controls"]
                    R --> COP["COP signed<br/>(Compliance Officer)"]
                    COP --> G1{{"Gate 1<br/>planning coverage"}}
                    G1 -->|pass| ORD["Signed Order<br/>hash-referenced"]
                    G1 -->|refuse| STOP["REFUSED<br/>names the gap"]
                    ORD ==>|the seam| RT["Runtime<br/>plan / evidence / oracles"]
                    RT --> G2{{"Gate 2<br/>human attests MET"}}
                    G2 --> P["Audit + SPRS<br/>+ BOM + SSP"]
                    P --> V["Reproduction<br/>C3PAO re-derives"]
                """
            ),
            mo.callout(
                mo.md(
                    "**Honest limits, stated up front.** Every run today is "
                    "**NON-EVIDENTIARY**: evidence is fixture-backed, terraform runs in "
                    "preview with mock providers, and references resolve against local files. "
                    "Attestation signing is real (Ed25519, fail-closed on tamper) but the demo "
                    "runs unsigned git-trust, and the production cosign+KMS path is deferred; "
                    "the Flexo append-only tier is wired but offline-simulated. The engine "
                    "records claims; it does not make an organization compliant. A false claim "
                    "still passes here — the human signer carries the accountability, and an "
                    "assessor catches it. None of this is hidden: the mechanism is wired end to "
                    "end and stamps its outputs so a practice run is never mistaken for a "
                    "submission."
                ),
                kind="warn",
            ),
        ]
    )
    return (s0_map,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 1 - the contract
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(io_flow, join, mo, obl_rows, order, order_ok, station, table):
    _rows = [
        {
            "Obligation": r["obligation"],
            "Type": r["type"],
            "Data marker": r["data_marker"] or "—",
            "Resolves to": join(r["controls"]),
            "Note": r["note"] or "",
        }
        for r in obl_rows
    ]
    _n_obl = len(obl_rows)
    _contract = order.contract if order_ok else "NV012"
    _il = getattr(order, "impact_level", "IL4") if order_ok else "IL4"

    s1 = mo.vstack(
        [
            station("1", "The contract",
                    "A signed contract enters. It carries security obligations that must "
                    "be satisfied and proven."),
            mo.md(
                f"The demonstration contract is **{_contract}**, a Tier-1 {_il} CUI enclave. "
                "One sentence in the contract body — *\"this work handles Controlled "
                "Unclassified Information; you must meet CMMC Level 2\"* — is the legal "
                "hook. It is carried by two DFARS clauses that appear in every CMMC-required "
                "DoD contract: **252.204-7012** (safeguard CUI, report incidents) and "
                "**252.204-7021** (comply with CMMC Level 2). Software drafts the specific "
                "obligations from that text; a human attests them at Station 3."
            ),
            io_flow(
                "contract text",
                "The NV012 solicitation, its Q&A clarifications, and the DFARS clauses in "
                "the contract body.",
                "obligations",
                "A structured list of what the contract requires, ready to resolve into "
                "controls.",
            ),
            mo.md(f"### The {_n_obl} obligations the engine extracted"),
            mo.md(
                "Each obligation names a type and, where relevant, the data marker that "
                "triggers it. A CUI or ITAR *deliverable* obligation trips a spillover guard "
                "so a requirement can never be dropped silently."
            ),
            table(_rows),
        ]
    )
    return (s1,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 2 - obligations become the required-control set
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(io_flow, mo, required, station):
    _ctrl_list = ", ".join(sorted(required)) if required else "—"
    s2 = mo.vstack(
        [
            station("2", "Obligations become controls",
                    "A rule library expands each obligation into the specific NIST "
                    "SP 800-171 controls it demands."),
            mo.md(
                "The Order Compiler runs the same resolver the production compiler uses "
                "(`rule_library.resolve`). The union of every obligation's controls is the "
                "**required set** — the exact list this Order must cover, end to end."
            ),
            io_flow(
                "obligations", "The structured obligations from Station 1.",
                "required controls", f"**{len(required)}** controls this Order must satisfy.",
            ),
            mo.md(
                f"### The {len(required)} controls required by this Order\n\n"
                f"<span style='font-family:monospace;font-size:0.9em'>{_ctrl_list}</span>"
            ),
            mo.callout(
                mo.md(
                    "**Scope, stated honestly.** The full catalog is **110** controls, and "
                    "the structural model claims all 110 (Station 12). This demonstration "
                    "Order exercises a runnable **slice** of that model. Everything scored "
                    "downstream — the SPRS number in particular — is computed over "
                    "*these* required controls, not all 110."
                ),
                kind="warn",
            ),
        ]
    )
    return (s2,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 3 - the Compliance Officer signs the COP (first human hop)
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(cop_att, io_flow, mo, station):
    _officer = getattr(cop_att, "officer", "—")
    _mode = getattr(cop_att, "mode", "—")
    _affirmations = getattr(cop_att, "affirmations", None)
    _n_aff = len(_affirmations) if _affirmations is not None else "—"
    _spillovers = getattr(cop_att, "acknowledged_spillovers", None)
    _n_spill = len(_spillovers) if _spillovers is not None else 0
    _attested = getattr(cop_att, "is_attested", True)

    s3 = mo.vstack(
        [
            station("3", "The Compliance Officer signs the COP",
                    "The first human judgment: someone reviews the machine-drafted "
                    "obligations against the real contract and signs."),
            mo.md(
                "This is the **only** human step inside the Order Compiler; everything "
                "downstream of it is automatic. The signed object is the Contract Obligation "
                "Profile (COP). Its real fields from this run:"
            ),
            mo.hstack(
                [
                    mo.stat(value=str(_officer), label="Officer", caption="signer of record", bordered=True),
                    mo.stat(value=str(_mode), label="Attestation mode", caption="how it was signed", bordered=True),
                    mo.stat(value=str(_n_aff), label="Affirmations", caption="obligations affirmed", bordered=True),
                    mo.stat(value=str(_n_spill), label="Spillovers ack'd", caption="deliverable guards", bordered=True),
                    mo.stat(value=str(_attested), label="Attested", caption="COP is signed", bordered=True),
                ],
                justify="center", gap="1.25rem",
            ),
            io_flow(
                "drafted obligations", "The machine's extraction from the contract text.",
                "signed COP", "A human's affirmation that the obligations are correct.",
            ),
            mo.callout(
                mo.md(
                    f"**Mode `{_mode}` in this demo.** `semiAuto` means an AI-assisted draft "
                    "was auto-affirmed so the chain runs unattended. A real run records "
                    "`manual`: a person signs, and that signature carries accountability "
                    "under the False Claims Act (31 U.S.C. § 3729) and 18 U.S.C. "
                    "§ 1001 for false statements to the government."
                ),
                kind="info",
            ),
        ]
    )
    return (s3,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 4 - Gate 1: planning coverage
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(g1, mo, station):
    _stats = mo.hstack(
        [
            mo.stat(value=g1.forward.summary(), label="Forward", caption="every control has a module", bordered=True),
            mo.stat(value=g1.backward.summary(), label="Backward", caption="every module traces to a control", bordered=True),
            mo.stat(value=g1.untestable.summary(), label="Testable", caption="every claim names a method", bordered=True),
        ],
        justify="center", gap="1.5rem",
    )

    if g1.passed:
        _verdict = mo.callout(
            mo.md(
                "**Gate 1 PASSES.** Every required control is covered by a module that "
                "names a verification method, and every included module traces back to a "
                "required control. The Order may be emitted."
            ),
            kind="success",
        )
    else:
        _gaps = ", ".join(g1.gap_controls())
        _verdict = mo.vstack([
            mo.md(
                f"<div style='background:#e74c3c;color:white;font-weight:700;font-size:1.2rem;"
                f"padding:.7rem 1rem;border-radius:6px'>GATE 1 REFUSES &mdash; the plan has a hole. "
                f"The assembly line stops here.</div>"
            ),
            mo.callout(
                mo.md(
                    f"**Uncovered control:** `{_gaps}`\n\n"
                    f"This control is required by the Order, but **no module claims it**. "
                    f"Nothing downstream runs: no Order is emitted, nothing is built, nothing "
                    f"is proven. The machine refuses to build something it cannot prove, and "
                    f"names the exact gap instead.\n\n"
                    f"Add a module that satisfies `{_gaps}` (or document a scope exclusion) and "
                    f"recompile &mdash; or switch the scenario above to **all-covered** / "
                    f"**contradiction** to watch the whole line run."
                ),
                kind="danger",
            ),
        ], gap=0.5)

    s4 = mo.vstack(
        [
            station("4", "Gate 1 — planning coverage",
                    "Before anything is built, the compiler refuses to proceed on an "
                    "incomplete plan."),
            mo.md(
                "Gate 1 enforces three things at once: **forward** (every required control "
                "has at least one claiming module), **backward** (every included module "
                "traces to a required control), and **no untestable claim** (every claiming "
                "module names how it will be verified). Its code is "
                "`src/compliance_engine/order_compiler/gate1.py`."
            ),
            _stats,
            _verdict,
        ]
    )
    return (s4,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 5 - the signed Order (the seam between the two machines)
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(io_flow, join, mo, order, order_ok, short, station):
    if not order_ok:
        s5 = mo.vstack(
            [
                station("5", "The signed Order",
                        "No Order was emitted — Gate 1 refused this scenario."),
                mo.callout(
                    mo.md("Switch to **all-covered** or **contradiction** in the sidebar to "
                          "watch a signed Order pass through the seam and drive the Runtime."),
                    kind="danger",
                ),
            ]
        )
    else:
        _mods = join(sorted(order.included_modules))
        s5 = mo.vstack(
            [
                station("5", "The signed Order",
                        "The one artifact that passes between the two machines. "
                        "Hash-referenced, so any later change is detectable."),
                mo.md(
                    "\"Signed\" here means **hash-referenced**: the Order is fixed to a "
                    "SHA-256 fingerprint (true cryptographic signing is deferred). The "
                    "Runtime does not care how the Order was written — it just executes "
                    "it. That clean seam is what lets each machine be audited on its own."
                ),
                mo.hstack(
                    [
                        mo.stat(value=short(order.order_hash, 12), label="Order hash", caption="SHA-256 fingerprint", bordered=True),
                        mo.stat(value=str(len(order.required_controls)), label="Required controls", caption="the Order's scope", bordered=True),
                        mo.stat(value=str(len(order.included_modules)), label="Included modules", caption="build blocks", bordered=True),
                        mo.stat(value=str(getattr(order, "impact_level", "—")), label="Impact level", caption="enclave tier", bordered=True),
                    ],
                    justify="center", gap="1.5rem",
                ),
                io_flow(
                    "signed COP + required set + modules",
                    "Everything Gate 1 just proved complete.",
                    "signed Order",
                    "A fingerprinted build order the Runtime can execute and re-verify.",
                ),
                mo.md(f"**Modules in this Order:** {_mods}"),
            ]
        )
    return (s5,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 6 - the Runtime (the Factory)
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(factory_ok, factory_state, join, mo, oracle_fig, order_ok, short, station, table):
    if not order_ok:
        s6 = mo.vstack(
            [
                station("6", "The Runtime",
                        "The Runtime never ran — Gate 1 refused, so there was no Order "
                        "to execute."),
                mo.callout(mo.md("Nothing was built. This is the point of Gate 1."), kind="danger"),
            ]
        )
    else:
        _st = factory_state
        _ev_rows = [
            {
                "Evidence": short(str(e["iri"]).rsplit("/", 1)[-1], 20),
                "Addresses controls": join(e["controls"]),
                "Summary keys": join(list(e["summary"].keys())[:4]),
            }
            for e in _st.evidence_index
        ]
        _or_rows = [
            {"Control": c, "Oracle outcome": o}
            for c, o in sorted(_st.oracles.outcomes.items())
        ]
        _mod_rows = [
            {"Module": m, "Content hash": short(h, 18)}
            for m, h in sorted(_st.fetch.module_hashes.items())
        ]

        s6 = mo.vstack(
            [
                station("6", "The Runtime executes the Order",
                        "An assembly line of seven stages that gathers facts and runs "
                        "automated checks. It never declares a control MET."),
                mo.mermaid(
                    """
                    flowchart LR
                        L["1. Load Order<br/>re-check hashes"] --> F["2. Fetch modules<br/>verify by hash"]
                        F --> P["3. Terraform plan<br/>mock providers"]
                        P --> PC["4. Policy check<br/>+ residency hard gate"]
                        PC --> A["5. Mock apply<br/>no cloud touched"]
                        A --> E["6. Collect evidence"]
                        E --> O["7. Run oracles<br/>config-check + attested-reference"]
                    """
                ),
                mo.hstack(
                    [
                        mo.stat(value=len(_st.fetch.module_hashes), label="Modules fetched", bordered=True),
                        mo.stat(value=len(_st.plan.resource_ids), label="Planned resources", bordered=True),
                        mo.stat(value="PASS" if _st.policy_check.passed else "FAIL", label="Pre-apply policy", bordered=True),
                        mo.stat(value=_st.evidence.evidence_node_count, label="Evidence nodes", bordered=True),
                        mo.stat(value=len(_st.oracles.outcomes), label="Oracle outcomes", bordered=True),
                    ],
                    justify="center", gap="1.25rem",
                ),
                mo.callout(
                    mo.md(
                        "**Terraform runs in preview only, with mock providers.** No cloud is "
                        "contacted, no credentials are used, nothing is deployed. The plan is "
                        "a genuine, detailed preview of what *would* be built. The evidence "
                        "the oracles read is fixture-backed, which is why every downstream "
                        "artifact is stamped NON-EVIDENTIARY."
                    ),
                    kind="warn",
                ),
                mo.md("### Oracle outcomes — what the machine found"),
                mo.md(
                    "The bars are the split at a glance: **passed** (green), **failed** (red), "
                    "**needsAction** (orange). This is the config oracle *and* the "
                    "attested-reference oracle over this run — every control resolves to a "
                    "concrete outcome."
                ),
                oracle_fig if oracle_fig is not None
                else mo.md("_(run a passing scenario to see the chart)_"),
                mo.md("### The full payload (collapsible detail)"),
                mo.accordion(
                    {
                        "Modules fetched by content hash": table(_mod_rows, page_size=10),
                        "Evidence artifacts (each addresses at least one control)": table(_ev_rows, page_size=10),
                        "Oracle outcomes (passed / failed / needsAction)": table(_or_rows, page_size=12),
                    }
                ),
                mo.callout(
                    mo.md(
                        "**The oracle never fakes a check, and never shrugs.** A machine control "
                        "returns `passed` / `failed` from its config check; a policy control "
                        "returns `passed` / `needsAction` / `failed` from the attested-reference "
                        "oracle — where a reference is missing, stale, or unsigned it returns "
                        "`needsAction` with the concrete reason. Neither is silently counted as "
                        "MET — that call belongs to a human at Station 8."
                    ),
                    kind="info",
                ),
            ]
        )
    return (s6,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 7 - the attested-reference model (the centerpiece)
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(mo, reference_rows, sources, station, table):
    _src_rows = [
        {"Authoritative source": s["source"], "Controls drawing on it": s["controls"], "What it owns": s["note"]}
        for s in sources
    ]
    _ref_rows = [
        {
            "Control": r["control"],
            "Authoritative source": r["source"],
            "Freshness": r["freshness"],
            "Last verified": (r["last_verified"] or "—")[:10],
            "Required role": r["role"],
            "Custodian": r["custodian"],
        }
        for r in reference_rows
    ]

    s7 = mo.vstack(
        [
            station("7", "The attested-reference model",
                    "The idea that lets one uniform check cover a firewall rule and a "
                    "written incident-response plan on equal footing."),
            mo.md(
                "Every control points at an **authoritative source** — the system that "
                "owns the ground truth for a whole class of evidence — and carries a "
                "**reference** into it. The reference is a resolvable pointer with a URI, a "
                "freshness window, a last-verified timestamp, a named custodian (\"where bob "
                "logs it\"), and a required signer role. At run time the engine runs this "
                "four-part check on every Track B (policy) control &mdash; the "
                "`attested-reference` oracle in `oracles/attested_reference.py`, now wired into "
                "the Runtime's oracle stage:"
            ),
            mo.hstack(
                [
                    mo.stat(value="1", label="Registered", caption="the reference exists", bordered=True),
                    mo.stat(value="2", label="Resolves", caption="the URI points at real content", bordered=True),
                    mo.stat(value="3", label="Fresh", caption="within its freshness window", bordered=True),
                    mo.stat(value="4", label="Signed by role", caption="right official attested it", bordered=True),
                ],
                justify="center", gap="1.25rem",
            ),
            mo.callout(
                mo.md(
                    "**Why this is the whole point.** A config-check oracle resolves a "
                    "**machine** control's reference into a cloud API and measures the "
                    "setting. The attested-reference oracle resolves a **human** control's "
                    "reference to the actual document, SHA-256 hashes it, captures the git "
                    "commit that produced it, signs an upload receipt, and confirms the "
                    "reference is fresh and role-signed. Both run in the Runtime's oracle "
                    "stage; only the source differs. That is how coverage reaches the policy "
                    "controls without pretending a machine measured a policy: the human still "
                    "signs, but the sign-off is now anchored to a specific, hashed, "
                    "git-tracked document version rather than a bare 'trust me'."
                ),
                kind="info",
            ),
            mo.md("### The authoritative sources behind the attested (Track B) controls"),
            table(_src_rows),
            mo.md(
                f"### The {len(reference_rows)} attested-reference records the oracle checks\n\n"
                "Each row is a real reference from `data/structural/references.ttl`: the "
                "control it backs, the system where its truth lives, how often it must be "
                "re-verified, when it last was, who must sign it, and who keeps it current."
            ),
            table(_ref_rows, page_size=12),
        ]
    )
    return (s7,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 8 - Gate 2: the human attests MET
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(attested, audit_report, bom_result, factory_ok, illustration, io_flow, mo, order_ok, required, station, table):
    if not order_ok or not factory_ok:
        s8 = mo.vstack(
            [
                station("8", "Gate 2 — the human attests MET",
                        "No attestations — the Runtime did not produce evidence to sign."),
                mo.callout(mo.md("Run a scenario that passes Gate 1 to reach the human sign-off."), kind="danger"),
            ]
        )
    else:
        _con = audit_report.contradictions if audit_report else []
        # Colour each row by how the human sign-off is backed (left border).
        _backing_color = {
            "machine": "#27ae60",              # green  — config oracle passed
            "attested-evidenced": "#16a085",   # teal   — human, machine-recorded doc
            "override": "#e74c3c",             # red    — MET over a failed check
            "human-only": "#f39c12",           # amber  — human judgment only
        }
        _th = ("<th style='text-align:left;padding:4px 10px;border-bottom:2px solid #1f3a5f'>"
               "{}</th>")
        _head = "".join(_th.format(h) for h in
                        ["Control", "Oracle", "Attestation", "Backing", "Evidence", "Status"])
        _body = ""
        for r in bom_result.control_mapping:
            _c = _backing_color.get(r.evidence_backing, "#95a5a6")
            _ev = (sorted(r.evidence_hashes)[0][:12] + "…") if r.evidence_hashes else "—"
            _cells = [r.control_id, r.oracle_outcome or "—", r.attestation_outcome or "—",
                      r.evidence_backing, _ev, r.status]
            _tds = "".join(
                f"<td style='padding:3px 10px;font-size:0.85rem'>{v}</td>" for v in _cells)
            _body += (f"<tr style='border-left:4px solid {_c}'>{_tds}</tr>")
        _map_html = (
            f"<div style='overflow-x:auto'><table style='border-collapse:collapse;width:100%'>"
            f"<thead><tr>{_head}</tr></thead><tbody>{_body}</tbody></table></div>"
        )
        _map_legend = (
            "<span style='font-size:0.8rem'>"
            "<b style='color:#27ae60'>&#9646; machine</b> &nbsp; "
            "<b style='color:#16a085'>&#9646; attested-evidenced</b> &nbsp; "
            "<b style='color:#f39c12'>&#9646; human-only</b> &nbsp; "
            "<b style='color:#e74c3c'>&#9646; override</b></span>"
        )

        if _con:
            _con_rows = [
                {"Control": c.control, "Oracle": c.oracle_outcome, "Written override": str(c.has_override)}
                for c in _con
            ]
            _con_block = mo.vstack(
                [
                    mo.callout(
                        mo.md(
                            "**Contradiction flagged.** A human attested MET while the machine "
                            "oracle failed, with no written override justification. The score "
                            "does not silently absorb this — it is surfaced on its own line "
                            "so an unexplained human-over-machine call cannot hide inside a "
                            "passing number."
                        ),
                        kind="danger",
                    ),
                    table(_con_rows),
                ]
            )
        else:
            _con_block = mo.callout(
                mo.md("**No contradictions.** Every human MET call agrees with its machine "
                      "check, or the control had no machine check to disagree with."),
                kind="success",
            )

        s8 = mo.vstack(
            [
                station("8", "Gate 2 — the human attests MET",
                        "A machine gathers evidence and runs checks. It can never declare a "
                        "control satisfied. Only a named human does that."),
                mo.md(
                    "A control is recorded MET only when its evidence passes its oracle "
                    "**and** the Affirming Official attests it in the required role. In the "
                    "data model, evidence *addresses* a control and only a human attestation "
                    "*attests* it — enforced in the graph, not merely by policy."
                ),
                mo.hstack(
                    [
                        mo.stat(value=f"{attested} / {len(required)}", label="Controls attested MET", caption="by the Affirming Official", bordered=True),
                        mo.stat(value=str(audit_report.proven.machine_count), label="Machine-proven", caption="oracle passed + attested", bordered=True),
                        mo.stat(value=str(audit_report.proven.human_count), label="Human-attested only", caption="no machine measurement", bordered=True),
                        mo.stat(value=str(len(_con)), label="Contradictions", caption="MET over failed check", bordered=True),
                    ],
                    justify="center", gap="1.25rem",
                ),
                io_flow(
                    "evidence + oracle outcomes",
                    "What the Runtime measured, plus the reference checks.",
                    "signed attestations",
                    "A human's MET call per control, carrying the oracle's real outcome.",
                ),
                illustration(
                    "When an oracle returns **failed** but the signer still judges the "
                    "control MET, a required **override justification** field appears: the "
                    "signer must explain why the control is satisfied another way. Leave it "
                    "blank and the audit flags a contradiction — even if the score reads "
                    "110. This is the exact case the **contradiction** scenario exercises."
                ),
                mo.callout(
                    mo.md(
                        "**Why no machine is allowed to sign.** The Affirming Official's "
                        "signature carries personal legal accountability under the False "
                        "Claims Act (31 U.S.C. § 3729) and 18 U.S.C. § 1001. "
                        "Knowingly certifying false information to the federal government is "
                        "an offense. Accountability cannot rest on a machine, so the machine "
                        "is not permitted to make the call."
                    ),
                    kind="warn",
                ),
                _con_block,
                mo.md(
                    "### Per-control result (real BOM mapping)\n\n"
                    "The **Evidence backing** column makes the proven-vs-attested split "
                    "concrete per control: **machine** means the sign-off is backed by a "
                    "passing config oracle over resolvable evidence (the **Evidence** "
                    "hash traces to the artifact); **attested-evidenced** means a human "
                    "sign-off backed by a *machine-recorded document* — the referenced file "
                    "was resolved, SHA-256 hashed, and carries the git commit that produced it "
                    "plus a signed upload receipt (this is how the policy controls, like "
                    "`CA.L2-3.12.4`, are anchored to a real document version); **human-only** "
                    "means no machine artifact exists, so the control rests on human judgment; "
                    "**override** means the human attested MET over a failed machine check "
                    "(which must carry a written justification and appended evidence)."
                ),
                mo.md(_map_legend),
                mo.md(_map_html),
            ]
        )
    return (s8,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 8b - control interrogation (ask: how do we know this is met?)
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(mo, required):
    _sorted = sorted(required) if required else []
    control_picker = mo.ui.dropdown(
        options=_sorted,
        value=_sorted[0] if _sorted else "",
        label="Control to interrogate",
    )
    return (control_picker,)


@app.cell
def _(audit_report, bom_result, control_picker, factory_ok, factory_state):
    import _interrogate  # noqa: PLC0415

    control_explanation = None
    if factory_ok and control_picker.value:
        control_explanation = _interrogate.explain_control(
            control_picker.value,
            factory_state,
            audit_report,
            bom_result,
        )
    return (control_explanation,)


@app.cell(hide_code=True)
def _(control_explanation, control_picker, factory_ok, mo, station):
    if factory_ok and control_explanation is not None:
        _body = mo.md("```\n" + control_explanation + "\n```")
    else:
        _body = mo.callout(
            mo.md("Run a passing scenario to see control interrogation."),
            kind="warn",
        )

    s8b = mo.vstack(
        [
            station(
                "8b",
                "Control interrogation",
                "Ask: how do we know this control is met?",
            ),
            control_picker,
            _body,
        ]
    )
    return (s8b,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 9 - the proof outputs
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(audit_report, bom_result, coverage, factory_ok, mo, order_ok, short, sprs_fig, ssp_md, station):
    if not order_ok or not factory_ok:
        s9 = mo.vstack(
            [
                station("9", "The proof outputs",
                        "No proof — the Runtime halted before producing artifacts."),
                mo.callout(mo.md("Run a passing scenario to see the audit, SPRS score, BOM, and SSP."), kind="danger"),
            ]
        )
    else:
        _sprs = audit_report.sprs
        _banner = "NON-EVIDENTIARY" in ssp_md
        _ssp_head = "\n".join(ssp_md.splitlines()[:24])

        # The arithmetic, spelled out: 110 minus the weight of each not-met control.
        _wt = {c["id"]: int(c.get("weight", 1) or 1) for c in coverage}
        _unmet = sorted(
            ((r.control_id, _wt.get(r.control_id, 1)) for r in bom_result.control_mapping
             if r.status != "MET"),
            key=lambda x: -x[1],
        )
        if _unmet:
            _terms = " ".join(f"− {w} ({cid})" for cid, w in _unmet[:8])
            _more = f" − … ({len(_unmet) - 8} more)" if len(_unmet) > 8 else ""
            _arith = f"SPRS = 110 {_terms}{_more} = {_sprs.score}"
        else:
            _arith = (f"SPRS = 110 − 0 = {_sprs.score}   "
                      "(every required control is MET — nothing is deducted)")

        s9 = mo.vstack(
            [
                station("9", "The proof outputs",
                        "Two checks and two documents, all compiled from one dataset, so "
                        "they cannot disagree."),
                mo.md("### The audit and the SPRS score"),
                sprs_fig if sprs_fig is not None else mo.md(""),
                mo.md(
                    "The **audit** walks the evidence chain forward and backward (Gate 2 at "
                    "BOM close), prints the proven-vs-attested split, and lists "
                    "contradictions separately. The **SPRS score** is "
                    "`110 - (weights of not-met controls)`, banded Final (110) / Conditional "
                    "(88–109, with a legal POA&M) / Ineligible (below 88), and computed "
                    "over *this Order's* required set. The subtraction, for this run:"
                ),
                mo.md(f"<div style='font-family:monospace;font-size:1.02rem;background:#f5f7f9;"
                      f"padding:.6rem .8rem;border-radius:6px'>{_arith}</div>"),
                mo.hstack(
                    [
                        mo.stat(value=str(_sprs.score), label="SPRS score", caption=_sprs.status, bordered=True),
                        mo.stat(value=str(_sprs.valid_submission), label="Valid submission", caption="POA&M rules satisfied", bordered=True),
                        mo.stat(value=f"{audit_report.proven.machine_count} / {audit_report.proven.human_count}", label="Machine / human", caption="proven vs attested", bordered=True),
                        mo.stat(value=str(len(audit_report.contradictions)), label="Contradictions", caption="read with the score", bordered=True),
                    ],
                    justify="center", gap="1.25rem",
                ),
                mo.callout(
                    mo.md(
                        "**Read both lines together.** A score of 110 / Final with a nonzero "
                        "contradiction count is **not** a clean result. The score and the "
                        "contradiction list are kept separate on purpose so a number can "
                        "never quietly absorb an unexplained human-over-machine override. "
                        "**POA&M legality:** only 1-point controls may be deferred; deferring "
                        "a 3- or 5-point control (or one of six excluded 1-pointers) sets "
                        "`valid_submission=False` regardless of the number."
                    ),
                    kind="info",
                ),
                mo.md("### The BOM and the SSP"),
                mo.hstack(
                    [
                        mo.stat(value=short(bom_result.bom_hash, 12), label="BOM hash", caption="SHA-256, write-once", bordered=True),
                        mo.stat(value=bom_result.evidentiary_status, label="Evidentiary status", caption="weakest input wins", bordered=True),
                        mo.stat(value=str(len(bom_result.control_mapping)), label="Controls mapped", caption="one row each", bordered=True),
                        mo.stat(value=str(_banner), label="NON-EVIDENTIARY banner", caption="structural, no off switch", bordered=True),
                    ],
                    justify="center", gap="1.25rem",
                ),
                mo.md(
                    "The **BOM** (`bom.json`) is the machine-readable, content-addressed "
                    "record: one row per control mapping resource → evidence hash "
                    "→ oracle outcome → attestation → status. It is stored "
                    "write-once under its own SHA-256 and inherits the weakest evidentiary "
                    "status present (`mock` here). The **SSP** (`ssp.md`) is the deterministic, "
                    "byte-stable government document compiled from the *same* dataset, so the "
                    "two cannot disagree; its NON-EVIDENTIARY banner is emitted structurally "
                    "whenever any input is mock."
                ),
                mo.accordion({"SSP preview (first 24 lines)": mo.md("```\n" + _ssp_head + "\n```")}),
            ]
        )
    return (s9,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 9b - per-control SPRS breakdown table
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(audit_report, factory_ok, required):
    import _interrogate  # noqa: PLC0415

    sprs_rows = None
    if factory_ok and audit_report is not None:
        sprs_rows = _interrogate.sprs_breakdown(audit_report, required)
    return (sprs_rows,)


@app.cell(hide_code=True)
def _(factory_ok, mo, sprs_rows, table):
    if factory_ok and sprs_rows:
        _content = table(sprs_rows, page_size=15)
    else:
        _content = mo.md(
            "_(Run a passing scenario to see the per-control SPRS breakdown.)_"
        )

    s9_breakdown = mo.vstack(
        [
            mo.md("### Per-control SPRS breakdown"),
            _content,
        ]
    )
    return (s9_breakdown,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 10 - proof by reproduction
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(factory_ok, illustration, mo, order_ok, station):
    _body = [
        station("10", "Proof by reproduction",
                "The reason this beats a folder of screenshots: an assessor does not have "
                "to trust the party that produced the delivery."),
        mo.md(
            "Given a delivered BOM, a C3PAO assessor can re-derive the whole record: "
            "**resolve** every artifact by its hash from the write-once registry, "
            "**re-hash** each one to confirm the fingerprint matches, and **re-run** the "
            "plan-level checks to confirm the oracle outcomes agree. If every fingerprint "
            "matches and every re-run agrees, the delivery is exactly what was signed and "
            "its checks reproduce. The operator command is `ce verify --output-dir <dir>`."
        ),
        illustration(
            "```\n"
            "$ ce verify --output-dir output/\n"
            "Re-hashing every evidence node in the audit dataset...\n"
            "Checking SHACL shapes for attestation completeness...\n"
            "Dataset intact. No tampering detected. SHACL shapes conform.\n"
            "```\n\n"
            "Change one byte — even a single character in a justification — and "
            "the SHA-256 no longer matches, and `verify` exits nonzero. The fingerprint is "
            "the proof of integrity."
        ),
        mo.callout(
            mo.md(
                "**What reproduction does and does not prove.** It confirms the delivered "
                "record is internally consistent and untampered, and that its automated "
                "checks re-run to the same outcomes. It does **not** by itself make an "
                "organization compliant — a false claim can still pass the engine. The "
                "human signer carries the accountability; the assessor's reproduction plus "
                "review is what catches a false claim."
            ),
            kind="info",
        ),
    ]
    if not order_ok or not factory_ok:
        _body.insert(1, mo.callout(
            mo.md("_This scenario produced no artifacts to reproduce; the mechanism is shown "
                  "for reference._"), kind="warn"))
    s10 = mo.vstack(_body)
    return (s10,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 10b - live hash-chain tamper demo
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(factory_ok, factory_state):
    import _interrogate  # noqa: PLC0415

    hash_demo = None
    if factory_ok:
        hash_demo = _interrogate.live_hash_demo(factory_state)
    return (hash_demo,)


@app.cell(hide_code=True)
def _(factory_ok, hash_demo, mo, station):
    if factory_ok and hash_demo is not None:
        s10b = mo.vstack(
            [
                station(
                    "10b",
                    "Hash chain demo",
                    "Watch the fingerprint break when one byte changes",
                ),
                mo.md(
                    f"**Evidence node:** `{hash_demo['ev_id']}`\n\n"
                    f"**Recorded hash:** `{hash_demo['original_hash'][:24]}...`\n\n"
                    f"**Tampered hash (one byte flipped):** "
                    f"`{hash_demo['tampered_hash'][:24]}...`"
                ),
                mo.callout(
                    mo.md(
                        "**TAMPERING DETECTED — hash mismatch.** "
                        "Changing a single byte in any evidence artifact produces a "
                        "completely different SHA-256 fingerprint. The two hashes above "
                        "diverge at the first character; `ce verify` would exit "
                        "nonzero and name this node."
                    ),
                    kind="danger",
                ),
            ]
        )
    else:
        s10b = mo.vstack(
            [
                station(
                    "10b",
                    "Hash chain demo",
                    "Watch the fingerprint break when one byte changes",
                ),
                mo.callout(
                    mo.md(
                        "Run a passing scenario (**all-covered** or **contradiction**) "
                        "to see the live hash-tamper demonstration."
                    ),
                    kind="warn",
                ),
            ]
        )
    return (s10b,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 11 - the substrate (one queryable knowledge graph)
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(graph_counts, graph_fig, mo, station, table):
    _rows = [
        {"Named graph": f"ce:{r['layer']}", "Triples": r["triples"]}
        for r in graph_counts
    ]
    s11 = mo.vstack(
        [
            station("11", "The substrate",
                    "Every station above wrote into one place: a single RDF dataset of "
                    "named graphs, separated by layer but queryable together."),
            mo.md(
                "Controls, the plan, the Order, evidence, attestations, the plan execution, "
                "and the audit each live in their own named graph inside one dataset. That "
                "is what makes the whole chain re-executable and tamper-evident — and "
                "what lets the BOM and SSP be compiled from the exact same triples."
            ),
            mo.md("### The traceability graph — Order &rarr; Modules &rarr; Controls"),
            mo.md(
                "Blue = the Order, purple = claiming modules, control nodes coloured by "
                "oracle outcome (green passed / red failed / amber needsAction / "
                "grey no result). Orange halos mark contradictions. This is the picture the "
                "audit walks, forward and backward."
            ),
            graph_fig if graph_fig is not None
            else mo.md("_(run a passing scenario to see the traceability graph)_"),
            mo.md("### Live triple counts (collapsible detail)"),
            table(_rows),
            mo.callout(
                mo.md(
                    "**The five roles on the line.** *Compliance Officer* — extracts "
                    "obligations, signs the COP (Station 3). *Order Compiler* (machine) "
                    "— obligations to controls to modules, runs Gate 1. *Runtime* "
                    "(machine) — executes the Order, gathers evidence, runs oracles. "
                    "*Affirming Official* (human) — signs each control MET, carries the "
                    "accountability (Station 8). *C3PAO assessor* (human) — re-verifies "
                    "the BOM by hash and re-runs the checks (Station 10)."
                ),
                kind="neutral",
            ),
        ]
    )
    return (s11,)


# ═══════════════════════════════════════════════════════════════════════════════
# Station 12 - full coverage of all 110 controls
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(coverage, mo):
    _families = ["All"] + sorted({r["family"] for r in coverage})
    cov_family = mo.ui.dropdown(options=_families, value="All", label="Family")
    cov_status = mo.ui.dropdown(
        options=["All", "machine", "attested", "inherited"],
        value="All", label="Verification kind",
    )
    return cov_family, cov_status


@app.cell
def _(coverage, cov_family, cov_status, coverage_fig, engine, mo, station, table):
    _KIND = engine.KIND_LABEL

    _n_mac = sum(1 for r in coverage if r["status"] == "machine")
    _n_att = sum(1 for r in coverage if r["status"] == "attested")
    _n_inh = sum(1 for r in coverage if r["status"] == "inherited")

    _filtered = [
        r for r in coverage
        if (cov_family.value == "All" or r["family"] == cov_family.value)
        and (cov_status.value == "All" or r["status"] == cov_status.value)
    ]
    _table_rows = [
        {
            "Control": r["id"],
            "Wt": r["weight"],
            "Verified by": _KIND[r["status"]],
            "No POA&M": "yes" if r["non_deferrable"] else "",
            "CSP": "inherited" if r["inherited"] else "",
            "Requirement": (r["text"][:96] + "…") if len(r["text"]) > 96 else r["text"],
        }
        for r in _filtered
    ]

    _fam_order = ["AC", "AT", "AU", "CA", "CM", "IA", "IR", "MA", "MP", "PE", "PS", "RA", "SC", "SI"]
    _score_rows = []
    for _fam in _fam_order:
        _fc = [r for r in coverage if r["family"] == _fam]
        if not _fc:
            continue
        _score_rows.append({
            "Family": _fam,
            "Total": len(_fc),
            "Machine": sum(1 for r in _fc if r["status"] == "machine"),
            "Attested": sum(1 for r in _fc if r["status"] == "attested"),
            "Inherited": sum(1 for r in _fc if r["status"] == "inherited"),
        })

    s12 = mo.vstack(
        [
            station("12", "Full coverage — all 110 controls",
                    "The demonstration Order ran a slice. The structural model claims the "
                    "whole catalog. Here is how each of the 110 is verified."),
            mo.callout(
                mo.md(
                    "**Three verification kinds, derived live from the graph.** "
                    "**Machine-verified** — a config-check oracle measures it from "
                    "configuration. **Attested-reference** — a registered, fresh, "
                    "role-signed reference into an authoritative source (Station 7). "
                    "**CSP-inherited** — satisfied by the cloud provider and inherited. "
                    "Every control below is classified by its claiming module's verification "
                    "method, not by a hand-maintained list."
                ),
                kind="info",
            ),
            mo.hstack(
                [
                    mo.stat(value=str(_n_mac), label="Machine-verified", caption="config-check oracle", bordered=True),
                    mo.stat(value=str(_n_att), label="Attested-reference", caption="reference + role sign-off", bordered=True),
                    mo.stat(value=str(_n_inh), label="CSP-inherited", caption="provider handles it", bordered=True),
                    mo.stat(value=str(len(coverage)), label="Total claimed", caption="every control has a module", bordered=True),
                ],
                justify="center", gap="1.25rem",
            ),
            mo.md("### Coverage by family — the whole catalog at a glance"),
            mo.md(
                "Fourteen families &times; three verification kinds (blue machine / orange "
                "attested-reference / teal CSP-inherited). The stacked bars show the "
                "structural coverage of all 110 controls before you drill into the table."
            ),
            coverage_fig,
            mo.hstack([cov_family, cov_status], gap="2rem"),
            mo.md(f"**{len(_filtered)} of {len(coverage)} controls** shown. "
                  "**Wt** is the SPRS weight deducted if the control is not met; "
                  "**No POA&M** marks controls that cannot be deferred."),
            table(_table_rows, page_size=15),
            mo.md("### Summary by control family"),
            table(_score_rows),
        ]
    )
    return (s12,)


# ═══════════════════════════════════════════════════════════════════════════════
# Footer - what is real vs mock
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(mo):
    footer = mo.callout(
        mo.md(
            "### What is real vs. mock right now\n\n"
            "The software spine is wired end to end, but every run is a practice run:\n\n"
            "- **Evidence is fixture-backed**, not pulled from a live cloud, so every "
            "artifact is `mock` and every BOM/SSP is **NON-EVIDENTIARY** (not submittable).\n"
            "- **Terraform runs in preview only, with mock providers** — nothing is "
            "deployed, no credentials are used.\n"
            "- **The attested-reference oracle is wired, over local documents.** For every "
            "Track B (policy) control the engine resolves the reference to the real document, "
            "SHA-256 hashes it, captures the git commit that produced it, signs an upload "
            "receipt, and checks freshness + signer role — a real gate (a stale or missing "
            "reference drops the control out of MET). The documents are the placeholder "
            "policies in the repo, not the live authoritative sources, and the signer is the "
            "local Ed25519 dev key.\n"
            "- **Attestation signing is real but the demo runs unsigned.** The engine signs "
            "and verifies attestation records with Ed25519 (fail-closed on tamper); the demo "
            "uses `sig_algo=none` git-trust, and the production cosign+KMS path is deferred.\n"
            "- **The Flexo append-only tier is wired, offline-simulated** (`--store-backend "
            "flexo`); the local registry is the cache/fallback. A live in-enclave server is "
            "deferred.\n"
            "- **The engine does not talk to SPRS**; a human files the computed score.\n"
            "- **The SPRS score covers this Order's required set**, not all 110 (Station 12 "
            "shows the full model).\n\n"
            "What is real end to end: full-chain provenance, signed attestations, the "
            "attested-reference oracle that gates Track B controls on a resolved + hashed + "
            "git-tracked + role-signed document (the **attested-evidenced** backing), the "
            "append-only tier, and a single signed **audit package** an assessor re-verifies "
            "offline (`ce package` / `ce verify-package`). None of this is hidden — the banner, "
            "the `mock` stamp, and the proven-vs-attested split keep the demonstration honest; "
            "only the evidence is stand-in."
        ),
        kind="neutral",
    )
    return (footer,)


# ═══════════════════════════════════════════════════════════════════════════════
# Assemble the single end-to-end scroll
# ═══════════════════════════════════════════════════════════════════════════════

@app.cell
def _(
    footer,
    header,
    mo,
    prologue,
    s0_map,
    s0_open,
    s1,
    s10,
    s10b,
    s11,
    s12,
    s2,
    s3,
    s4,
    s5,
    s6,
    s7,
    s8,
    s8b,
    s9,
    s9_breakdown,
):
    mo.vstack(
        [
            header,
            mo.md("---"), s0_open, s0_map,
            mo.md("---"), prologue,
            mo.md("---"), s1,
            mo.md("---"), s2,
            mo.md("---"), s3,
            mo.md("---"), s4,
            mo.md("---"), s5,
            mo.md("---"), s6,
            mo.md("---"), s7,
            mo.md("---"), s8,
            mo.md("---"), s8b,
            mo.md("---"), s9,
            mo.md("---"), s9_breakdown,
            mo.md("---"), s10,
            mo.md("---"), s10b,
            mo.md("---"), s11,
            mo.md("---"), s12,
            mo.md("---"), footer,
        ],
        gap=1.75,
    )
    return


if __name__ == "__main__":
    app.run()
