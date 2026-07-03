"""Operator CLI — the one-command NV012 compliance demo.

Chains the whole system end-to-end:

    compile-order → run-factory → attest → audit → bom (→ ssp)

`demo` runs the full chain in one process over a shared `<ce:*>` Dataset (the way
the Factory wires its named graphs). Each stage is also exposed as its own
subcommand that persists/reloads the dataset (`engine.trig`) + a small run-state
(`run_state.json`) under `--output-dir`, so an operator can step through it.

Times are pulled from the graph/state (the Order's `ce:generatedAtTime`, threaded
via a fixed run seed) — no `datetime.now()` reaches the written artifacts.

The `ssp` step renders the SSP via `documents/ssp.py`; if that module is
unavailable it prints "SSP: skipped" and continues (exit 0).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

# Deterministic run seed threaded through compile/attest/oracles so outputs are
# reproducible. The audit timestamp is pulled back out of the Order graph.
RUN_SEED_TS = "2026-07-02T00:00:00+00:00"
CONTRACT_ID = "NV012"
EVIDENCE_SETS = ("all-covered", "gap", "contradiction")
# A required-but-unclaimed 5-point control used to force the Gate-1 gap scenario
# (there is no tier1.ttl module for it — see Round 5 coverage surface).
# The gap demo cites a syntactically-valid but non-catalog control ID so the
# rule_library's control-id validator refuses the COP before Gate 1 even runs.
# (Track A + B now cover all 110 real catalog controls, so a real "unclaimed
# but required" gap is impossible; a fake control ID is the equivalent
# educational refusal path.)
_GAP_CONTROL = "XX.L2-3.99.99"

app = typer.Typer(add_completion=False, help="NV012 compliance engine — operator CLI.")


# ---------------------------------------------------------------------------
# Dataset / run-state persistence (for step-by-step subcommands)
# ---------------------------------------------------------------------------


def _engine_trig(out: Path) -> Path:
    return out / "engine.trig"


def _run_state_path(out: Path) -> Path:
    return out / "run_state.json"


def _save_ds(ds, out: Path) -> None:
    from compliance_engine.pipeline.dataset import export_trig

    export_trig(ds, _engine_trig(out))


def _load_ds(out: Path):
    from compliance_engine.pipeline.dataset import create_dataset

    ds = create_dataset()
    trig = _engine_trig(out)
    if trig.exists():
        ds.parse(str(trig), format="trig")
    return ds


def _dump_run_state(state, out: Path) -> None:
    lo = state.load_order
    plan_resources = [
        {"resource_id": r.resource_id, "controls": list(r.controls)}
        for r in (state.plan.plan_result.resources if state.plan else ())
    ]
    payload = {
        "order_iri": state.order_iri,
        "order_hash": lo.order_hash if lo else None,
        "contract": lo.contract if lo else CONTRACT_ID,
        "tier": lo.tier if lo else "Tier1",
        "impact_level": lo.impact_level if lo else "IL4",
        "standard": lo.standard if lo else "NIST SP 800-171 Rev 2",
        "required_controls": list(lo.required_controls) if lo else [],
        "included_modules": list(lo.included_modules) if lo else [],
        "module_hashes": dict(state.fetch.module_hashes) if state.fetch else {},
        "resource_ids": list(state.plan.resource_ids) if state.plan else [],
        "plan_controls": list(state.plan.plan_controls) if state.plan else [],
        "plan_resources": plan_resources,
        "state_hash": state.apply.state_hash if state.apply else None,
        "evidence_hashes": list(state.evidence.evidence_hashes)
        if state.evidence
        else [],
        "evidence_controls": list(state.evidence.controls_addressed)
        if state.evidence
        else [],
        "oracle_outcomes": dict(state.oracles.outcomes) if state.oracles else {},
        "policy_passed": state.policy_check.passed if state.policy_check else False,
        "policy_findings": [f.reason for f in state.policy_check.findings]
        if state.policy_check
        else [],
        "halted": state.halted,
        "halted_at": state.halted_at,
    }
    _run_state_path(out).write_text(json.dumps(payload, indent=2, sort_keys=True))


def _load_run_state(ds, out: Path):
    """Reconstruct a PipelineState from run_state.json (enough for bom/audit)."""
    from compliance_engine.pipeline.provision.base import PlannedResource, PlanResult
    from compliance_engine.pipeline.state import (
        ApplyStageResult,
        EvidenceStageResult,
        FetchResult,
        LoadOrderResult,
        OracleStageResult,
        PipelineState,
        PlanStageResult,
        PolicyCheckResult,
        PolicyFinding,
    )

    d = json.loads(_run_state_path(out).read_text())
    state = PipelineState(
        ds=ds,
        provision_backend=None,
        store_backend=None,
        order_iri=d["order_iri"],
        contract=d["contract"],
    )
    state.load_order = LoadOrderResult(
        order_iri=d["order_iri"],
        order_hash=d["order_hash"],
        verified=True,
        contract=d["contract"],
        tier=d["tier"],
        impact_level=d["impact_level"],
        standard=d["standard"],
        required_controls=tuple(d["required_controls"]),
        included_modules=tuple(d["included_modules"]),
    )
    state.fetch = FetchResult(
        modules_verified=True, module_hashes=dict(d["module_hashes"])
    )
    resources = tuple(
        PlannedResource(
            resource_id=r["resource_id"],
            address="",
            type="",
            controls=tuple(r["controls"]),
            values={},
            region=None,
        )
        for r in d["plan_resources"]
    )
    state.plan = PlanStageResult(
        plan_result=PlanResult(plan_json={}, resources=resources),
        resource_ids=tuple(d["resource_ids"]),
        plan_controls=tuple(d["plan_controls"]),
    )
    if d.get("state_hash"):
        state.apply = ApplyStageResult(
            state_hash=d["state_hash"], applied=True, resource_count=len(resources)
        )
    state.evidence = EvidenceStageResult(
        evidence_node_count=len(d["evidence_hashes"]),
        evidence_hashes=tuple(d["evidence_hashes"]),
        controls_addressed=tuple(d["evidence_controls"]),
    )
    state.oracles = OracleStageResult(
        outcomes=dict(d["oracle_outcomes"]), assertion_iris=()
    )
    state.policy_check = PolicyCheckResult(
        passed=d["policy_passed"],
        findings=tuple(
            PolicyFinding(resource_id="", reason=r) for r in d["policy_findings"]
        ),
        oracle_outcomes={},
    )
    state.halted = d["halted"]
    state.halted_at = d["halted_at"]
    return state


# ---------------------------------------------------------------------------
# Stage helpers (used by both `demo` and the standalone subcommands)
# ---------------------------------------------------------------------------


def _gap_message(report_or_str) -> str:
    """Format either a Gate1Report or an UnknownControlError string uniformly."""
    if isinstance(report_or_str, str):
        return report_or_str
    return f"Missing module for required control(s): {', '.join(report_or_str.gap_controls())}"


class _GapRefused(Exception):
    """Gate 1 refused the Order — carries the report for a clean CLI message."""

    def __init__(self, report):
        self.report = report
        super().__init__("Gate 1 refused the Order")


def _do_compile(ds, obligations, evidence_set: str, now: str):
    """Compile + attest the COP → Order. For the `gap` scenario, inject a
    required-but-unclaimed control so Gate 1 refuses (Factory never runs)."""
    from compliance_engine.order_compiler import compiler, cop
    from compliance_engine.order_compiler import rule_library as rl

    obligations = dict(obligations)
    if evidence_set == "gap":
        obligations["OBL-DEMO-GAP"] = rl.Obligation(
            "OBL-DEMO-GAP", rl.DATA, derives=frozenset({_GAP_CONTROL})
        )
    att = cop.attest_cop(ds, obligations, auto=True, now=now)
    try:
        return compiler.compile_order(ds, obligations, att, now=now)
    except compiler.Gate1Failed as exc:
        raise _GapRefused(exc.report) from exc
    except rl.UnknownControlError as exc:
        # The gap demo cites a fake control ID that fails catalog validation
        # before Gate 1 runs. Surface it via the same _GapRefused path so the
        # CLI message + exit code stay consistent with a real coverage gap.
        raise _GapRefused(str(exc)) from exc


def _do_run_factory(ds, order_iri, evidence_set: str, backend: str, output_dir: Path):
    from compliance_engine.pipeline.backends.local import LocalBackend
    from compliance_engine.pipeline.provision import (
        FakeProvisionBackend,
        TerraformBackend,
    )
    from compliance_engine.pipeline.runner import run_factory

    provision = TerraformBackend() if backend == "terraform" else FakeProvisionBackend()
    return run_factory(
        ds,
        order_iri,
        provision_backend=provision,
        store_backend=LocalBackend(),
        evidence_set=evidence_set,
        now=RUN_SEED_TS,
        run_preflight=True,
        output_dir=output_dir,
    )


def _do_attest(ds, state) -> int:
    """Auto-attest MET for the FULL Order-required control set (Gate 2).

    A machine-checked control carries its real oracle outcome (`ce:oracleOutcome`)
    so R13 still fires in the `contradiction` scenario (a failed oracle + a MET
    attestation without override → contradiction). A required control with no
    machine oracle is attested MET as human/inherited (no `ce:oracleOutcome`),
    so `all-covered` reaches full coverage over the required set → SPRS 110/Final.
    """
    from compliance_engine.ontology.prefixes import CE, EARL
    from compliance_engine.traceability.attestation import (
        OUTCOME_PASSED,
        request_attestation,
    )

    outcome_iri = {
        "passed": EARL.passed,
        "failed": EARL.failed,
        "cantTell": EARL.cantTell,
        "needsAction": CE.needsAction,
    }
    required = state.load_order.required_controls if state.load_order else ()
    outcomes = state.oracles.outcomes if state.oracles else {}
    n = 0
    for control_id in sorted(required):
        oracle_outcome = outcomes.get(control_id)
        if oracle_outcome is not None:
            adequacy = "Implementation reviewed against the provisioned configuration."
            sufficiency = (
                "Machine oracle + config evidence sufficient for the Phase-I mock run."
            )
        else:
            adequacy = (
                "Implementation reviewed; control met by human/inherited determination."
            )
            sufficiency = "No machine oracle for this control; attested MET on documentary/CSP basis."
        request_attestation(
            ds,
            control_id,
            "NV012 Affirming Official",
            auto_attest=True,
            adequacy=adequacy,
            sufficiency=sufficiency,
            outcome=OUTCOME_PASSED,
            oracle_outcome=outcome_iri.get(oracle_outcome) if oracle_outcome else None,
        )
        n += 1
    return n


def _run_timestamp(ds) -> str:
    """Pull the run timestamp from the Order graph (no datetime.now)."""
    from rdflib import URIRef

    from compliance_engine.ontology.prefixes import CE, G_ORDER

    g = ds.graph(URIRef(G_ORDER))
    for _s, _p, o in g.triples((None, CE.generatedAtTime, None)):
        return str(o)
    return RUN_SEED_TS


def _do_audit(ds, output_dir: Path):
    from compliance_engine.traceability.audit import (
        audit,
        emit_audit_graph,
        render_report,
    )

    report = audit(ds, timestamp=_run_timestamp(ds))
    emit_audit_graph(ds, report)
    (output_dir / "audit.md").write_text(render_report(report, "md"))
    (output_dir / "audit.json").write_text(render_report(report, "json"))
    return report


def _do_bom(state, ds, output_dir: Path):
    from compliance_engine.pipeline.registry import Registry
    from compliance_engine.traceability.bom import build_bom, store_bom

    bom = build_bom(state, ds, contract_id=CONTRACT_ID)
    registry = Registry(output_dir / "registry")
    store_bom(bom, registry, CONTRACT_ID)
    (output_dir / "bom.json").write_text(bom.to_canonical_json())
    return bom


def _ssp_hook(output_dir: Path, *, ds=None, audit_report=None, bom=None) -> None:
    """Render the SSP (documents/ssp.py) into `<output-dir>/ssp.md`.

    In the demo, `ds`/`audit_report`/`bom` come live from the run so the colophon
    carries the real SPRS line + BOM artifact hashes. Standalone (`ds is None`)
    renders from the persisted `engine.trig` with the fallback colophon. The
    ImportError guard keeps the command from ever hard-crashing if the module is
    somehow absent.
    """
    try:
        from compliance_engine.documents.ssp import compile_ssp_from_run
    except ImportError:
        typer.echo("SSP: skipped (documents/ssp.py not available)")
        return

    dataset_path = _engine_trig(output_dir)
    if ds is None:
        ds = _load_ds(output_dir)  # standalone: reload the persisted dataset

    md = compile_ssp_from_run(
        ds, audit_report=audit_report, bom=bom, dataset_path=dataset_path
    )
    ssp_path = output_dir / "ssp.md"
    ssp_path.write_text(md)
    has_banner = "NON-EVIDENTIARY" in md
    typer.echo(
        f"SSP: wrote {ssp_path} "
        f"(NON-EVIDENTIARY banner: {'present' if has_banner else 'absent'})"
    )


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

_OUT = Annotated[str, typer.Option("--output-dir", help="Artifact output directory.")]
_EVSET = Annotated[
    str, typer.Option("--evidence-set", help="all-covered | gap | contradiction.")
]


def _ensure_out(output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    return out


@app.command("compile-order")
def compile_order_cmd(
    output_dir: _OUT = "output",
    evidence_set: _EVSET = "all-covered",
    auto: Annotated[bool, typer.Option("--auto", help="Auto-attest the COP.")] = True,
) -> None:
    """Compile + attest the NV012 COP → hash-referenced Order (Gate 1 gated)."""
    from compliance_engine.order_compiler import compiler

    out = _ensure_out(output_dir)
    ds, obligations = compiler.load_pipeline_dataset()
    try:
        order = _do_compile(ds, obligations, evidence_set, RUN_SEED_TS)
    except _GapRefused as gap:
        typer.echo(f"Gate 1 REFUSED — Order not emitted. {_gap_message(gap.report)}")
        raise typer.Exit(2)
    _save_ds(ds, out)
    typer.echo(
        f"Order compiled: {order.order_hash} "
        f"({len(order.required_controls)} controls, {len(order.included_modules)} modules)"
    )


@app.command("run-factory")
def run_factory_cmd(
    output_dir: _OUT = "artifacts",
    evidence_set: _EVSET = "all-covered",
    backend: Annotated[
        str, typer.Option("--backend", help="fake | terraform.")
    ] = "fake",
) -> None:
    """Run the Factory over the compiled Order."""
    from rdflib import URIRef

    from compliance_engine.ontology.prefixes import CE, G_ORDER

    out = _ensure_out(output_dir)
    ds = _load_ds(out)
    order_iri = next(ds.graph(URIRef(G_ORDER)).subjects(CE.orderHash), None)
    if order_iri is None:
        typer.echo("No Order found — run compile-order first.")
        raise typer.Exit(2)
    state = _do_run_factory(ds, order_iri, evidence_set, backend, out)
    _save_ds(ds, out)
    _dump_run_state(state, out)
    if state.halted:
        typer.echo(
            f"Factory HALTED at {state.halted_at}: {[f.reason for f in state.failures]}"
        )
        raise typer.Exit(1)
    typer.echo(
        f"Factory complete: {len(state.oracles.outcomes)} oracle outcomes, "
        f"{state.evidence.evidence_node_count} evidence nodes"
    )


@app.command("attest")
def attest_cmd(output_dir: _OUT = "output") -> None:
    """Auto-attest each control the Factory produced an oracle outcome for."""
    out = _ensure_out(output_dir)
    ds = _load_ds(out)
    state = _load_run_state(ds, out)
    n = _do_attest(ds, state)
    _save_ds(ds, out)
    typer.echo(f"Attested {n} control(s) (Gate 2).")


@app.command("audit")
def audit_cmd(output_dir: _OUT = "output") -> None:
    """Run the bidirectional audit + SPRS; write audit.md/json."""
    out = _ensure_out(output_dir)
    ds = _load_ds(out)
    report = _do_audit(ds, out)
    _save_ds(ds, out)
    _print_audit_summary(report)


@app.command("bom")
def bom_cmd(output_dir: _OUT = "output") -> None:
    """Assemble + store the BOM; write bom.json."""
    out = _ensure_out(output_dir)
    ds = _load_ds(out)
    state = _load_run_state(ds, out)
    bom = _do_bom(state, ds, out)
    typer.echo(f"BOM: {bom.bom_hash} (evidentiary_status={bom.evidentiary_status})")


@app.command("verify")
def verify_cmd(output_dir: _OUT = "output") -> None:
    """Re-verify the output dataset: re-hash evidence nodes and check SHACL shapes for tampering."""
    import traceability.verification

    out = _ensure_out(output_dir)
    ds = _load_ds(out)
    report = traceability.verification.verify(ds)
    if report.reverification_mismatches:
        for m in report.reverification_mismatches:
            iri_seg = str(m.evidence_iri).rsplit("/", 1)[-1]
            typer.echo(
                f"{iri_seg}  expected={m.expected_hash[:12]}  actual={m.actual_hash[:12]}"
            )
        raise typer.Exit(code=1)
    if not report.conforms:
        for line in report.summary_lines():
            typer.echo(line)
        raise typer.Exit(code=1)
    typer.echo("Dataset intact. No tampering detected. SHACL shapes conform.")


@app.command("ssp")
def ssp_cmd(output_dir: _OUT = "output") -> None:
    """Render the SSP from the persisted dataset (skipped if the SSP compiler is unavailable)."""
    out = _ensure_out(output_dir)
    _ssp_hook(out)


def _print_audit_summary(report) -> None:
    if report.sprs is not None:
        typer.echo(
            f"SPRS: score={report.sprs.score} status={report.sprs.status} "
            f"valid_submission={report.sprs.valid_submission}"
        )
    else:
        typer.echo("SPRS: n/a (no scorable controls)")
    typer.echo(f"Proven vs attested: {report.proven.summary()}")
    typer.echo(
        f"Contradictions (attested MET over failed machine check): {len(report.contradictions)}"
    )


# ---------------------------------------------------------------------------
# The one command
# ---------------------------------------------------------------------------


@app.command("demo")
def demo(
    output_dir: _OUT = "output",
    evidence_set: _EVSET = "all-covered",
    auto: Annotated[
        bool, typer.Option("--auto", help="Auto-attest COP + controls.")
    ] = True,
    backend: Annotated[
        str, typer.Option("--backend", help="fake | terraform.")
    ] = "fake",
) -> None:
    """Run the full NV012 chain: compile-order → run-factory → attest → audit → bom → ssp."""
    from compliance_engine.order_compiler import compiler

    if evidence_set not in EVIDENCE_SETS:
        typer.echo(f"--evidence-set must be one of {EVIDENCE_SETS}")
        raise typer.Exit(2)
    out = _ensure_out(output_dir)

    # 1. compile + attest Order (shared ds threaded through every stage).
    ds, obligations = compiler.load_pipeline_dataset()
    typer.echo(f"[demo] evidence-set={evidence_set}")
    try:
        order = _do_compile(ds, obligations, evidence_set, RUN_SEED_TS)
    except _GapRefused as gap:
        typer.echo(
            f"[1/6 compile-order] Gate 1 REFUSED — Order NOT emitted. "
            f"{_gap_message(gap.report)}"
        )
        raise typer.Exit(2)
    typer.echo(
        f"[1/6 compile-order] Order {order.order_hash} "
        f"({len(order.required_controls)} controls)"
    )

    # 2. run Factory.
    state = _do_run_factory(ds, order.iri, evidence_set, backend, out)
    if state.halted:
        typer.echo(
            f"[2/6 run-factory] HALTED at {state.halted_at} "
            f"(safety valve): {[f.reason for f in state.failures]}"
        )
        raise typer.Exit(1)
    typer.echo(
        f"[2/6 run-factory] {state.evidence.evidence_node_count} evidence nodes, "
        f"{len(state.oracles.outcomes)} oracle outcomes"
    )

    # 3. attest.
    n = _do_attest(ds, state)
    typer.echo(f"[3/6 attest] {n} control(s) attested (Gate 2)")

    # 4. audit + SPRS.
    report = _do_audit(ds, out)
    typer.echo("[4/6 audit]")
    _print_audit_summary(report)

    # 5. BOM.
    bom = _do_bom(state, ds, out)
    typer.echo(
        f"[5/6 bom] {bom.bom_hash} evidentiary_status={bom.evidentiary_status} "
        f"-> {out / 'bom.json'}"
    )

    # 6. SSP — render the real document from this run's audit + BOM.
    typer.echo("[6/6 ssp]")
    _save_ds(ds, out)  # persist first so ssp's dataset path resolves
    _ssp_hook(out, ds=ds, audit_report=report, bom=bom)

    _dump_run_state(state, out)


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
