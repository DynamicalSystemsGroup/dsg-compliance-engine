"""Factory orchestrator — execute a verified Order, plan-level, into raw results.

Structural pattern ported from ADCS `pipeline/runner.py`: stage-level free
functions threaded by a `PipelineState`, a fail-fast preflight, and a Typer
shell. Retargeted to the compliance Factory:

  LoadOrder      verify the signed Order (independent hash recompute + attestation)
  FetchByHash    re-derive each included module's CBD hash, compare to the Order
  Plan           real `terraform plan` → `show -json` via the ProvisionBackend
  PolicyCheck    region/policy gate + oracles on the plan — FAIL HALTS before Apply
  Apply          mock-provider apply (live deferred)
  CollectEvidence  evidence generators bind ce:Evidence (addresses controls)
  Oracles        oracles evaluate + emit ce:ControlCheckAssertion

Every stage emits a p-plan:Activity. The Factory collects RAW results into
`PipelineState` — it does NOT build the BOM or run Attestation/Audit.
Order verification is deliberately independent of the Order Compiler: the
Factory re-derives the hashes itself so a tampered Order is caught.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from rdflib import BNode, Dataset, Graph, URIRef

from compliance_engine.ontology.prefixes import CE, CMMC, EARL, G_ORDER
from compliance_engine.pipeline.dataset import create_dataset, graph_for, load_into
from compliance_engine.pipeline.plan_execution import emit_stage_activity
from compliance_engine.pipeline.provision import (
    FakeProvisionBackend,
    ProvisionUnavailable,
    TerraformBackend,
    is_us_region,
)
from compliance_engine.pipeline.state import (
    ApplyStageResult,
    AttestedRefResult,
    EvidenceStageResult,
    FetchResult,
    LoadOrderResult,
    OracleStageResult,
    PipelineState,
    PlanStageResult,
    PolicyCheckResult,
    PolicyFinding,
)

from compliance_engine.pipeline.evidence.hashing import _serialize_for_hash, hash_structural_model

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CATALOG_TTL = _REPO_ROOT / "data" / "ontology" / "cmmc-edit.ttl"
ATTREF_VOCAB_TTL = _REPO_ROOT / "data" / "ontology" / "ce-attestation-refs.ttl"
TIER1_TTL = _REPO_ROOT / "data" / "structural" / "tier1.ttl"
REFERENCES_TTL = _REPO_ROOT / "data" / "structural" / "references.ttl"

# The Order canonical shapes below MUST match order-compiler/compiler.py. They
# are re-implemented here (not imported) so the Factory verifies the Order
# independently of the tool that produced it — that is the point of hash-refs.
_TARGET_TIER = "Tier1"
_IMPACT_LEVEL = "IL4"
_STANDARD = "NIST SP 800-171 Rev 2"


class OrderVerificationError(RuntimeError):
    """The Order failed independent verification (LoadOrder / FetchByHash)."""


# ---------------------------------------------------------------------------
# Order verification helpers (independent re-derivation)
# ---------------------------------------------------------------------------

def _sha256(obj) -> str:
    return hashlib.sha256(_serialize_for_hash(obj).encode()).hexdigest()


def _local(uri) -> str:
    s = str(uri)
    for sep in ("#", "/"):
        if sep in s:
            s = s.rsplit(sep, 1)[-1]
    return s


def _module_cbd(struct: Graph, module: URIRef) -> Graph:
    g = Graph()
    for p, o in struct.predicate_objects(module):
        g.add((module, p, o))
        if isinstance(o, BNode):
            for p2, o2 in struct.predicate_objects(o):
                g.add((o, p2, o2))
    return g


def _order_facts(ds: Dataset, order_iri: URIRef) -> dict:
    """Read the Order's stated facts from <ce:order>."""
    g = graph_for(ds, "order")

    def one(pred):
        v = g.value(order_iri, pred)
        return str(v) if v is not None else None

    required = sorted(_local(c) for c in g.objects(order_iri, CE.requiresControl))
    included = sorted(_local(m) for m in g.objects(order_iri, CE.includesModule))
    module_hashes = {}
    for mh in g.objects(order_iri, CE.hasModuleHash):
        module = g.value(mh, CE.module)
        chash = g.value(mh, CE.contentHash)
        if module is not None and chash is not None:
            module_hashes[_local(module)] = str(chash)
    data_classes = sorted(str(x) for x in g.objects(order_iri, CE.scopeDataClass))
    policy_markers = sorted(str(x) for x in g.objects(order_iri, CE.policyMarker))
    attestation = g.value(order_iri, CE.attestedByCOP)
    att_passed = bool(
        attestation is not None
        and (attestation, CE.outcome, EARL.passed) in g
    )
    return {
        "contract": one(CE.forContract),
        "tier": one(CE.targetTier),
        "impact_level": one(CE.impactLevel),
        "standard": one(CE.standard),
        "required": required,
        "included": included,
        "module_hashes": module_hashes,
        "data_classes": data_classes,
        "policy_markers": policy_markers,
        "cop_hash": one(CE.copHash),
        "control_set_hash": one(CE.controlSetHash),
        "coverage_proof_hash": one(CE.coverageProofHash),
        "order_hash": one(CE.orderHash),
        "attestation_passed": att_passed,
    }


def _verify_order_scalars(facts: dict) -> None:
    """LoadOrder checks: attestation passed + controlSetHash + orderHash."""
    if not facts["attestation_passed"]:
        raise OrderVerificationError(
            "COP attestation missing or not earl:passed — refusing the Order."
        )
    recomputed_csh = _sha256({"controls": sorted(facts["required"])})
    if recomputed_csh != facts["control_set_hash"]:
        raise OrderVerificationError(
            f"controlSetHash mismatch: recomputed {recomputed_csh[:12]}… "
            f"!= stated {str(facts['control_set_hash'])[:12]}…"
        )
    scope = {
        "tier": facts["tier"],
        "impact_level": facts["impact_level"],
        "data_classes": facts["data_classes"],
        "policy_markers": facts["policy_markers"],
    }
    recomputed_oh = _sha256({
        "contract": facts["contract"],
        "tier": _TARGET_TIER,
        "impact_level": _IMPACT_LEVEL,
        "standard": _STANDARD,
        "scope": scope,
        "required_controls": sorted(facts["required"]),
        "module_hashes": facts["module_hashes"],
        "cop_hash": facts["cop_hash"],
        "control_set_hash": facts["control_set_hash"],
        "coverage_proof_hash": facts["coverage_proof_hash"],
    })
    if recomputed_oh != facts["order_hash"]:
        raise OrderVerificationError(
            f"orderHash mismatch: recomputed {recomputed_oh[:12]}… "
            f"!= stated {str(facts['order_hash'])[:12]}… (Order tampered)"
        )


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

def run_stage_load_order(state: PipelineState) -> None:
    act = emit_stage_activity(state.ds, "LoadOrder")
    state.stage_activities["LoadOrder"] = act
    order = URIRef(state.order_iri)
    facts = _order_facts(state.ds, order)
    _verify_order_scalars(facts)
    state.load_order = LoadOrderResult(
        order_iri=state.order_iri,
        order_hash=facts["order_hash"],
        verified=True,
        contract=facts["contract"],
        tier=facts["tier"],
        impact_level=facts["impact_level"],
        standard=facts["standard"],
        required_controls=tuple(facts["required"]),
        included_modules=tuple(facts["included"]),
    )


def run_stage_fetch(state: PipelineState) -> None:
    """FetchByHash: re-derive each included module's CBD hash from
    <ce:structural> and compare to the Order's stated ce:contentHash."""
    act = emit_stage_activity(state.ds, "FetchByHash")
    state.stage_activities["FetchByHash"] = act
    facts = _order_facts(state.ds, URIRef(state.order_iri))
    struct = graph_for(state.ds, "structural")
    verified: dict[str, str] = {}
    for module_local, stated in facts["module_hashes"].items():
        actual = hash_structural_model(_module_cbd(struct, CE[module_local]))
        if actual != stated:
            raise OrderVerificationError(
                f"module {module_local!r} content hash mismatch: fetched "
                f"{actual[:12]}… != Order {stated[:12]}… (module tampered / wrong version)"
            )
        verified[module_local] = actual
    state.fetch = FetchResult(modules_verified=True, module_hashes=verified)


def run_stage_plan(state: PipelineState) -> None:
    act = emit_stage_activity(state.ds, "Plan")
    state.stage_activities["Plan"] = act
    pr = state.provision_backend.plan()
    state.plan = PlanStageResult(
        plan_result=pr,
        resource_ids=tuple(pr.resource_ids()),
        plan_controls=tuple(pr.controls()),
    )


def run_stage_policycheck(state: PipelineState) -> None:
    """Region/policy gate + oracles on the REAL plan. A FAIL HALTS before Apply.

    Residency invariant (hard gate, never silently disabled): the plan MUST
    carry at least one region signal. A plan with zero region-bearing
    resources cannot prove residency, so the check itself is non-evidentiary
    and the run halts — safer than silently passing a mis-tagged plan.
    """
    from compliance_engine.oracles.criteria import CRITERIA, evaluate

    act = emit_stage_activity(state.ds, "PolicyCheck")
    state.stage_activities["PolicyCheck"] = act
    pr = state.plan.plan_result

    findings: list[PolicyFinding] = []
    region_signals_seen = 0
    for res in pr.resources:
        if res.region is not None:
            region_signals_seen += 1
            if not is_us_region(res.region):
                findings.append(PolicyFinding(
                    resource_id=res.resource_id,
                    reason="planned resource region is not US (data residency violation)",
                    detail={"region": res.region},
                ))
    if region_signals_seen == 0:
        findings.append(PolicyFinding(
            resource_id="<none>",
            reason=("residency invariant: plan carries no region-bearing "
                    "resource — cannot prove US-only residency"),
            detail={"region_signals_seen": 0},
        ))

    # Oracles on the plan-derived summary (region → ITAR-120.54 residency criterion).
    oracle_outcomes: dict[str, str] = {}
    for res in pr.resources:
        if res.region is None:
            continue
        summary = {"data_region": "US" if is_us_region(res.region) else res.region}
        for control_id in ("ITAR-120.54",):
            if control_id in CRITERIA:
                out = evaluate(summary, control_id).outcome
                oracle_outcomes[f"{res.resource_id}:{control_id}"] = out
                if out == "failed":
                    findings.append(PolicyFinding(
                        resource_id=res.resource_id,
                        reason=f"policy oracle {control_id} failed on the plan",
                        detail={"region": res.region},
                    ))

    passed = not findings
    state.policy_check = PolicyCheckResult(
        passed=passed, findings=tuple(findings), oracle_outcomes=oracle_outcomes,
    )
    if not passed:
        state.halt(
            "PolicyCheck",
            "policy-as-code gate failed on the real plan — halting before Apply",
            findings=[f.reason for f in findings],
        )


def run_stage_apply(state: PipelineState) -> None:
    act = emit_stage_activity(state.ds, "Apply")
    state.stage_activities["Apply"] = act
    ar = state.provision_backend.apply()
    state.apply = ApplyStageResult(
        state_hash=ar.state_hash, applied=ar.applied, resource_count=ar.resource_count,
    )


def run_stage_collect_evidence(state: PipelineState) -> None:
    from compliance_engine.pipeline.evidence.binding import bind_evidence
    from compliance_engine.pipeline.evidence.generators import GeneratorContext
    from compliance_engine.pipeline.evidence.generators.mock_config import MockConfigExportGenerator
    from compliance_engine.pipeline.evidence.generators.mock_policy import MockPolicyCheckGenerator

    act = emit_stage_activity(state.ds, "CollectEvidence")
    state.stage_activities["CollectEvidence"] = act
    ctx = GeneratorContext(evidence_set=state.evidence_set)
    ev_graph = graph_for(state.ds, "evidence")

    hashes: list[str] = []
    controls: set[str] = set()
    for gen in (MockConfigExportGenerator(), MockPolicyCheckGenerator()):
        for art in gen.collect(ctx):
            ev_iri = bind_evidence(ev_graph, art)
            chash = ev_graph.value(ev_iri, CE.contentHash)
            if chash is not None:
                hashes.append(str(chash))
            controls.update(art.controls)
            state.evidence_index.append({
                "iri": ev_iri,
                "summary": dict(art.summary),
                "controls": list(art.controls),
            })

    state.evidence = EvidenceStageResult(
        evidence_node_count=len(state.evidence_index),
        evidence_hashes=tuple(hashes),
        controls_addressed=tuple(sorted(controls)),
    )


def run_stage_oracles(state: PipelineState) -> None:
    from compliance_engine.oracles.assertion import emit_control_check_assertion
    from compliance_engine.oracles.criteria import CRITERIA, evaluate

    act = emit_stage_activity(state.ds, "Oracles")
    state.stage_activities["Oracles"] = act

    outcomes: dict[str, str] = {}
    assertions: list[str] = []
    # Track A — config-check oracle over machine evidence summaries.
    for entry in state.evidence_index:
        for control_id in entry["controls"]:
            result = evaluate(entry["summary"], control_id)
            assertion = emit_control_check_assertion(
                state.ds, entry["iri"], CMMC[control_id], result,
                criterion=CRITERIA.get(control_id), now_iso=state.now,
            )
            outcomes[control_id] = result.outcome
            assertions.append(str(assertion))

    # Track B — attested-reference oracle over machine-recorded document evidence.
    _run_attested_reference_pass(state, outcomes, assertions)

    state.oracles = OracleStageResult(
        outcomes=outcomes, assertion_iris=tuple(assertions),
    )


def _run_attested_reference_pass(
    state: PipelineState, outcomes: dict[str, str], assertions: list[str],
) -> None:
    """Track B: for each in-scope control claimed by an oracle-attested-reference
    module, resolve + hash the referenced document, capture its git provenance and a
    signed upload receipt, bind it as ce:DocumentEvidence, then run the attested-
    reference oracle (registered / resolves / fresh / role-signed). The verdict is a
    REAL gate: a stale, missing, dead-link, or wrong-signer reference yields
    needsAction/failed and the control is NOT auto-attested MET downstream."""
    from dataclasses import replace
    from datetime import datetime, timezone

    from compliance_engine.oracles.assertion import emit_control_check_assertion
    from compliance_engine.oracles.attested_reference import evaluate_attested_reference
    from compliance_engine.pipeline.evidence import doc_evidence
    from compliance_engine.traceability.attestation_store import load_all
    from compliance_engine.traceability.references import load_attested_controls

    required = set(state.load_order.required_controls) if state.load_order else set()
    attested = {
        cid: ac for cid, ac in load_attested_controls(state.ds).items()
        if cid in required
    }
    if not attested:
        return

    records = load_all(_REPO_ROOT / "data" / "attestations")
    now_dt: datetime | None = None
    if state.now:
        try:
            now_dt = datetime.fromisoformat(state.now)
        except ValueError:
            now_dt = None
    now_dt = now_dt or datetime.now(timezone.utc)

    ev_graph = graph_for(state.ds, "evidence")
    for cid, ac in sorted(attested.items()):
        # A control already resolved by the Track A config oracle keeps that result;
        # attested-reference is for the policy/human controls Track A has no criterion for.
        if outcomes.get(cid) in {"passed", "failed"}:
            continue

        uploaded_by = ac.custodian or "Affirming Official"
        ev = None
        view = ac.view
        evidence_iri: str | None = None
        if view is not None:
            ev = doc_evidence.capture(ac.reference_id, ac.uri, uploaded_by)
            view = replace(view, resolved_ok=ev.exists)
            node = doc_evidence.bind_doc_evidence(ev_graph, ev)
            evidence_iri = str(node)

        result = evaluate_attested_reference(
            cid, view, ac.required_role, records, now=now_dt,
        )
        subject = URIRef(evidence_iri) if evidence_iri else CMMC[cid]
        assertion = emit_control_check_assertion(
            state.ds, subject, CMMC[cid], result, now_iso=state.now,
        )
        outcomes[cid] = result.outcome
        assertions.append(str(assertion))

        picked = next(
            (a.id for a in records
             if ac.reference_id in a.covers and cid in a.controls_attested),
            None,
        )
        state.attested_refs[cid] = AttestedRefResult(
            control_id=cid, reference_id=ac.reference_id, outcome=result.outcome,
            reason=result.reason,
            sha256=ev.sha256 if ev else None,
            git_commit=ev.git_commit if ev else None,
            git_committed_at=ev.git_committed_at if ev else None,
            uploaded_by=uploaded_by,
            upload_sig_ok=doc_evidence.verify_upload_receipt(ev) if ev else False,
            evidence_iri=evidence_iri, attestation_id=picked,
        )


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def _run_preflight(provision_backend, store_backend, *, output_dir=None) -> None:
    """Probe BOTH backends before Stage 0; fail-fast with exit 2 on error."""
    from compliance_engine.pipeline.backends.base import BackendUnavailable

    print("\n[Preflight] Probing backends...")
    print(f"  Provision: {provision_backend.describe()}")
    print(f"  Storage:   {store_backend.describe()}")

    failures: list[str] = []
    try:
        provision_backend.probe()
        print("  Provision probe: PASS")
    except ProvisionUnavailable as exc:
        failures.append(f"provision={provision_backend.name}: {exc}")
        print(f"  Provision probe: FAIL — {exc}")

    try:
        store_backend.probe(output_dir=output_dir)
        print("  Storage probe:   PASS")
    except BackendUnavailable as exc:
        failures.append(f"backend={store_backend.name}: {exc}")
        print(f"  Storage probe:   FAIL — {exc}")

    if failures:
        print("\n[Preflight] ERROR: one or more backends are unusable.")
        for f in failures:
            print(f"  - {f}")
        sys.exit(2)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def _bind_runtime_provenance(state) -> None:
    """Bind the run's real artifacts as P-Plan Entities (full-chain provenance).

    Function-local import keeps the pipeline package free of a load-time
    dependency on traceability.
    """
    from compliance_engine.traceability.provenance import bind_runtime_provenance
    bind_runtime_provenance(state)


def run_factory(
    ds: Dataset,
    order_iri,
    *,
    provision_backend,
    store_backend,
    evidence_set: str = "all-covered",
    auto: bool = True,
    now: str | None = None,
    run_preflight: bool = True,
    output_dir=None,
) -> PipelineState:
    """Execute the Factory over a verified Order. Returns the PipelineState.

    A PolicyCheck failure halts before Apply (safety valve): no state hash, a
    StageFailure recorded, and CollectEvidence/Oracles skipped.
    """
    state = PipelineState(
        ds=ds,
        provision_backend=provision_backend,
        store_backend=store_backend,
        order_iri=str(order_iri),
        evidence_set=evidence_set,
        auto=auto,
        now=now,
    )
    if run_preflight:
        _run_preflight(provision_backend, store_backend, output_dir=output_dir)

    run_stage_load_order(state)
    run_stage_fetch(state)
    run_stage_plan(state)
    run_stage_policycheck(state)
    if state.halted:
        _bind_runtime_provenance(state)  # partial chain for a halted run
        return state  # safety valve — stop before Apply

    run_stage_apply(state)
    run_stage_collect_evidence(state)
    run_stage_oracles(state)
    _bind_runtime_provenance(state)
    return state


def load_factory_dataset(
    order_ttl,
    *,
    catalog_ttl=CATALOG_TTL,
    tier1_ttl=TIER1_TTL,
    attref_vocab_ttl=ATTREF_VOCAB_TTL,
    references_ttl=REFERENCES_TTL,
) -> Dataset:
    """Build a Dataset with catalog + attestation vocab + tier1 + references +
    a serialized Order loaded.

    `order_ttl` is a TriG/Turtle export whose Order triples land in <ce:order>.
    """
    ds = create_dataset()
    load_into(ds, "ontology", catalog_ttl)
    if Path(attref_vocab_ttl).is_file():
        load_into(ds, "ontology", attref_vocab_ttl)
    load_into(ds, "structural", tier1_ttl)
    if Path(references_ttl).is_file():
        load_into(ds, "structural", references_ttl)
    # An order file may be TriG (named graphs) or flat Turtle for <ce:order>.
    order_path = str(order_ttl)
    if order_path.endswith(".trig"):
        ds.parse(order_path, format="trig")
    else:
        graph_for(ds, "order").parse(order_path, format="turtle")
    return ds


# ---------------------------------------------------------------------------
# Typer shell
# ---------------------------------------------------------------------------

try:  # pragma: no cover - CLI wiring
    import typer
    from typing import Annotated

    app = typer.Typer(add_completion=False, help="Compliance Factory (execute an Order).")

    @app.command()
    def run(
        order: Annotated[str, typer.Option("--order", help="Path to the Order TriG/TTL.")],
        provision: Annotated[str, typer.Option(
            "--provision", help="Provision backend: terraform | fake.")] = "terraform",
        evidence_set: Annotated[str, typer.Option(
            "--evidence-set", help="Fixture evidence set.")] = "all-covered",
        chdir: Annotated[str, typer.Option(
            "--tf-chdir", help="Terraform dir.")] = "infrastructure/terraform/tier1",
        output_dir: Annotated[str, typer.Option(
            "--output-dir", help="Registry/output dir (probed for writability).")] = "output",
    ) -> None:
        """Load + verify an Order and run the Factory to raw results."""
        from compliance_engine.pipeline.backends.local import LocalBackend

        ds = load_factory_dataset(order)
        order_iri = next(ds.graph(URIRef(G_ORDER)).subjects(
            predicate=CE.orderHash), None)
        if order_iri is None:
            typer.echo("No Order (ce:orderHash) found in the file.", err=True)
            raise typer.Exit(2)
        backend = (
            FakeProvisionBackend() if provision == "fake"
            else TerraformBackend(chdir=chdir)
        )
        state = run_factory(
            ds, order_iri,
            provision_backend=backend,
            store_backend=LocalBackend(),
            evidence_set=evidence_set,
            output_dir=Path(output_dir),
        )
        if state.halted:
            typer.echo(f"HALTED at {state.halted_at}: "
                       f"{[f.reason for f in state.failures]}")
            raise typer.Exit(1)
        typer.echo(f"Factory complete. Evidence nodes: "
                   f"{state.evidence.evidence_node_count if state.evidence else 0}; "
                   f"oracle outcomes: {state.oracles.outcomes if state.oracles else {}}")

    def main() -> None:  # pragma: no cover
        app()
except ImportError:  # pragma: no cover
    app = None

    def main() -> None:
        raise SystemExit("typer is required for the Factory CLI")


if __name__ == "__main__":  # pragma: no cover
    main()
