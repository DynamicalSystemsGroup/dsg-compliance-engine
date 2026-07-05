"""Factory orchestrator tests (FakeProvisionBackend; deterministic, no terraform).

Refuse-first: the safety-valve test is written first so a non-compliant plan is
proven to HALT before Apply before any happy path.
"""

from pathlib import Path

import pytest
from rdflib import Literal
from rdflib.namespace import RDF


from compliance_engine.order_compiler import compiler
from compliance_engine.order_compiler import cop
from compliance_engine.ontology.prefixes import CE, EARL, G_PLAN_EXECUTION, P_PLAN
from compliance_engine.pipeline.backends.local import LocalBackend
from compliance_engine.pipeline.dataset import graph_for
from compliance_engine.pipeline.plan_execution import STEP_NAMES
from compliance_engine.pipeline.provision import FakeProvisionBackend
from compliance_engine.pipeline.runner import OrderVerificationError, _run_preflight, run_factory
from compliance_engine.pipeline.state import PipelineState

NOW = "2026-07-02T00:00:00+00:00"

FACTORY_STAGES = ["LoadOrder", "FetchByHash", "Plan", "PolicyCheck",
                  "Apply", "CollectEvidence", "Oracles"]

def _attested_order_ds():
    """A ds with catalog+tier1+COP loaded and a verified NV012 Order emitted."""
    ds, obl = compiler.load_pipeline_dataset()
    att = cop.attest_cop(ds, obl, auto=True, now=NOW)
    order = compiler.compile_order(ds, obl, att, now=NOW)
    return ds, order

# ---------------------------------------------------------------------------
# SAFETY VALVE — proven first
# ---------------------------------------------------------------------------

def test_policy_failure_halts_before_apply():
    """A plan failing the region/policy oracle HALTS before Apply: no state
    hash, a failure record, CollectEvidence/Oracles skipped."""
    ds, order = _attested_order_ds()
    state = run_factory(
        ds, order.iri,
        provision_backend=FakeProvisionBackend(compliant=False),  # europe-west1
        store_backend=LocalBackend(),
        now=NOW, run_preflight=False,
    )
    assert state.halted is True
    assert state.halted_at == "PolicyCheck"
    assert state.policy_check is not None and state.policy_check.passed is False
    assert state.apply is None                 # no state hash — never applied
    assert state.evidence is None and state.oracles is None
    assert state.failures and state.failures[0].stage == "PolicyCheck"
    # Plan+PolicyCheck activities emitted; Apply activity NOT emitted.
    assert "PolicyCheck" in state.stage_activities
    assert "Apply" not in state.stage_activities

# ---------------------------------------------------------------------------
# HAPPY PATH
# ---------------------------------------------------------------------------

def test_happy_path_runs_all_stages():
    ds, order = _attested_order_ds()
    state = run_factory(
        ds, order.iri,
        provision_backend=FakeProvisionBackend(),
        store_backend=LocalBackend(),
        now=NOW, run_preflight=False,
    )
    assert not state.halted
    # one p-plan:Activity per Factory stage
    assert sorted(state.stage_activities) == sorted(FACTORY_STAGES)

    assert state.load_order.verified and len(state.load_order.required_controls) == 22
    assert state.fetch.modules_verified and len(state.fetch.module_hashes) == 10
    assert state.plan.resource_ids  # non-empty
    assert state.policy_check.passed
    assert state.apply.applied and len(state.apply.state_hash) == 64

    # PipelineState carries evidence hashes + oracle outcomes for a non-empty set.
    assert state.evidence.evidence_node_count > 0
    assert len(state.evidence.evidence_hashes) == state.evidence.evidence_node_count
    assert state.oracles.outcomes  # non-empty control set
    assert set(state.oracles.outcomes.values()) <= {"passed", "failed", "needsAction"}
    assert any(v == "passed" for v in state.oracles.outcomes.values())

def test_each_stage_emits_one_plan_activity():
    ds, order = _attested_order_ds()
    state = run_factory(
        ds, order.iri, provision_backend=FakeProvisionBackend(),
        store_backend=LocalBackend(), now=NOW, run_preflight=False,
    )
    pe = graph_for(state.ds, "plan_execution")
    steps: dict[str, int] = {}
    for _, _, step in pe.triples((None, P_PLAN.correspondsToStep, None)):
        local = str(step).rsplit("step-", 1)[-1]
        steps[local] = steps.get(local, 0) + 1
    for stage in FACTORY_STAGES:
        assert steps.get(stage) == 1, f"stage {stage}: {steps.get(stage)} activities"

def test_no_bom_built_by_factory():
    """The Factory collects raw results only — BOM assembly is a separate post-step."""
    ds, order = _attested_order_ds()
    state = run_factory(
        ds, order.iri, provision_backend=FakeProvisionBackend(),
        store_backend=LocalBackend(), now=NOW, run_preflight=False,
    )
    assert not hasattr(state, "bom")
    # No BOM node types emitted anywhere in the dataset.
    for _s, _p, o, _c in state.ds.quads((None, RDF.type, None)):
        assert "BOM" not in str(o) and "BillOfMaterials" not in str(o)

# ---------------------------------------------------------------------------
# Order verification (reuses the compiler hash recipe, independently)
# ---------------------------------------------------------------------------

def test_tampered_module_definition_refused_at_fetch():
    ds, order = _attested_order_ds()
    # Mutate the module's definition so its CBD no longer hashes to the Order's.
    graph_for(ds, "structural").add(
        (CE["Workspace2SV_CUI_OU"], CE["tampered"], Literal("x"))
    )
    with pytest.raises(OrderVerificationError, match="content hash mismatch"):
        run_factory(ds, order.iri, provision_backend=FakeProvisionBackend(),
                    store_backend=LocalBackend(), now=NOW, run_preflight=False)

def test_missing_cop_attestation_refused_at_load():
    ds, order = _attested_order_ds()
    og = graph_for(ds, "order")
    att = og.value(order.iri, CE.attestedByCOP)
    og.remove((att, CE.outcome, EARL.passed))   # strip the passed outcome
    with pytest.raises(OrderVerificationError, match="attestation"):
        run_factory(ds, order.iri, provision_backend=FakeProvisionBackend(),
                    store_backend=LocalBackend(), now=NOW, run_preflight=False)

def test_tampered_order_hash_refused_at_load():
    ds, order = _attested_order_ds()
    og = graph_for(ds, "order")
    # Tamper a stated module content hash → orderHash recompute mismatches.
    mh = next(og.objects(order.iri, CE.hasModuleHash))
    old = og.value(mh, CE.contentHash)
    og.set((mh, CE.contentHash, Literal("0" * 64)))
    og.remove((order.iri, CE.contentHash, old))  # no-op safety
    with pytest.raises(OrderVerificationError, match="orderHash|content hash"):
        run_factory(ds, order.iri, provision_backend=FakeProvisionBackend(),
                    store_backend=LocalBackend(), now=NOW, run_preflight=False)

# ---------------------------------------------------------------------------
# Preflight fail-fast
# ---------------------------------------------------------------------------

def test_preflight_unwritable_registry_exits_2(tmp_path):
    ro = tmp_path / "ro"
    ro.mkdir()
    ro.chmod(0o555)
    try:
        with pytest.raises(SystemExit) as exc:
            _run_preflight(FakeProvisionBackend(), LocalBackend(), output_dir=ro)
        assert exc.value.code == 2
    finally:
        ro.chmod(0o755)

# ---------------------------------------------------------------------------
# activity_to_stage ↔ STEP_NAMES ↔ plan.ttl
# ---------------------------------------------------------------------------

def test_activity_to_stage_matches_step_names():
    from compliance_engine.pipeline.dataset import create_dataset
    state = PipelineState(
        ds=create_dataset(),
        provision_backend=FakeProvisionBackend(),
        store_backend=LocalBackend(),
        order_iri="x",
    )
    assert set(state.activity_to_stage) == set(STEP_NAMES)

def test_plan_ttl_steps_match_step_names():
    from rdflib import Graph
    from compliance_engine.pipeline.plan_execution import step_iri
    g = Graph()
    g.parse(Path(__file__).resolve().parent.parent / "src" / "compliance_engine" / "pipeline" / "plan.ttl", format="turtle")
    from compliance_engine.ontology.prefixes import P_PLAN as PP
    declared = {str(s) for s in g.subjects(PP.isStepOfPlan, None)}
    missing = [n for n in STEP_NAMES if str(step_iri(n)) not in declared]
    assert not missing, f"plan.ttl missing steps: {missing}"
