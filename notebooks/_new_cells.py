"""New marimo cells to weave into notebooks/compliance_walkthrough.py.

Each section below is delimited by a block comment marking the exact insertion
point.  Copy the @app.cell blocks (not this module-level docstring) into the
walkthrough at the line indicated.

These cells depend on a sibling module _interrogate.py (not yet written) that
must expose:
    live_hash_demo(factory_state)   -> dict with keys node_id, recorded_hash,
                                       tampered_hash
    explain_control(control_id, factory_state, audit_report, bom_result)
                                    -> str (multi-line explanation)
    sprs_breakdown(audit_report, required)
                                    -> list[dict] for mo.ui.table

ASSEMBLY NOTE: after weaving these cells into the walkthrough, update the final
mo.vstack assembly cell (currently the last @app.cell in the file) so its
argument list and body include the new names:
  - prologue  — add after s0_map in the vstack body
  - s8b       — add after s8 in the vstack body
  - s9_breakdown — add after s9 (or replace the stat boxes inside s9)
  - s10b      — add after s10 in the vstack body

The assembly cell signature also needs these new names as function arguments,
e.g.:
    def _(footer, mo, prologue, s0_map, s0_open, s1, s10, s10b, s11, s12,
          s2, s3, s4, s5, s6, s7, s8, s8b, s9, s9_breakdown, ...):
"""

# =============================================================================
# SECTION A: Prologue
# INSERT AFTER LINE ~300 (after the sidebar @app.cell block, before Station 0)
# =============================================================================
#
# This cell is purely display — it takes only `mo` and produces `prologue`,
# a self-contained vstack that explains the notebook's design decisions.
# It slots between the sidebar setup and s0_open in the final assembly.

@app.cell(hide_code=True)
def _(mo):
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
                        "`cantTell` is not the same as `failed`. A machine that cannot "
                        "measure a control should say so rather than return false assurance "
                        "in either direction. `needsAction` is *actionable*: the oracle "
                        "found a registered reference but it is stale, unsigned, or "
                        "unresolvable — a concrete remediation exists. `cantTell` is "
                        "*structural*: the control has no machine-checkable oracle at all, "
                        "and only a human attestation can establish MET. Binary pass/fail "
                        "collapses this distinction and either inflates the score (by "
                        "counting untestable controls as passed) or deflates it (by "
                        "counting them as failed). Neither is honest."
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
        ],
        gap=1.0,
    )
    return (prologue,)


# =============================================================================
# SECTION C: Control interrogation
# INSERT AFTER LINE ~924 (after the s8 @app.cell block, before Station 9)
# =============================================================================
#
# Three cells: the dropdown widget, the data-fetch cell, and the display cell.
# They produce `control_picker`, `control_explanation`, and `s8b`.
# In the final assembly add s8b after s8 and before s9.

# --- C.1: control picker dropdown -------------------------------------------

@app.cell
def _(mo, required):
    _sorted = sorted(required) if required else []
    control_picker = mo.ui.dropdown(
        options=_sorted,
        value=_sorted[0] if _sorted else "",
        label="Control to interrogate",
    )
    return (control_picker,)


# --- C.2: fetch the explanation (no hide_code) -------------------------------

@app.cell
def _(audit_report, bom_result, control_picker, factory_ok, factory_state):
    import _interrogate  # noqa: PLC0415 — sibling module in notebooks/

    control_explanation = None
    if factory_ok and control_picker.value:
        control_explanation = _interrogate.explain_control(
            control_picker.value,
            factory_state,
            audit_report,
            bom_result,
        )
    return (control_explanation,)


# --- C.3: render Station 8b --------------------------------------------------

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


# =============================================================================
# SECTION D: Per-control SPRS breakdown
# INSERT AFTER LINE ~1004 (after the s9 @app.cell block, before Station 10)
# Note: this is intended to complement Station 9. The stat boxes inside s9
# remain; this cell adds a per-row breakdown table as a separate panel.
# In the final assembly add s9_breakdown after s9.
# =============================================================================

# --- D.1: compute the breakdown rows ----------------------------------------

@app.cell
def _(audit_report, factory_ok, required):
    import _interrogate  # noqa: PLC0415

    sprs_rows = None
    if factory_ok and audit_report is not None:
        sprs_rows = _interrogate.sprs_breakdown(audit_report, required)
    return (sprs_rows,)


# --- D.2: render the breakdown panel ----------------------------------------

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


# =============================================================================
# SECTION B: Hash chain demo
# INSERT AFTER LINE ~1053 (after the s10 @app.cell block, before Station 11)
# =============================================================================
#
# Two cells: the data cell and the display cell.
# They produce `hash_demo` and `s10b`.
# In the final assembly add s10b after s10 and before s11.

# --- B.1: run the live hash demo (no hide_code) ------------------------------

@app.cell
def _(factory_ok, factory_state):
    import _interrogate  # noqa: PLC0415

    hash_demo = None
    if factory_ok:
        hash_demo = _interrogate.live_hash_demo(factory_state)
    return (hash_demo,)


# --- B.2: render Station 10b -------------------------------------------------

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
                    f"**Evidence node:** `{hash_demo['node_id']}`\n\n"
                    f"**Recorded hash:** `{hash_demo['recorded_hash'][:24]}...`\n\n"
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
