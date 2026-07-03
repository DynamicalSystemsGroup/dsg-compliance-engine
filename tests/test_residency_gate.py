"""Residency hard-gate tests.

Two invariants — both must always hold for a submission to be valid:

  1. Non-US region signal in the plan → run HALTs at PolicyCheck, Apply and
     everything after is skipped, no state hash produced.
  2. Zero region signals in the plan → run HALTs at PolicyCheck (the check
     itself is non-evidentiary; silently passing a mis-tagged plan would be
     worse than failing).

Both invariants are exercised at the pipeline-runner level with the fake
provision backend (fast) and at the terraform-plan-generator level with the
real terraform binary (skipped when terraform is absent).
"""

from __future__ import annotations

import shutil

import pytest

from pipeline.provision import (
    ApplyResult,
    PlanResult,
    PlannedResource,
)


class _NoRegionBackend:
    """Provision backend whose plan carries zero region-bearing resources."""
    name = "no-region"

    def probe(self) -> None: ...
    def validate(self) -> None: ...
    def describe(self) -> str: return "no-region backend"

    def plan(self) -> PlanResult:
        return PlanResult(
            plan_json={"planned_values": {"root_module": {"resources": []}}},
            resources=(
                PlannedResource(
                    resource_id="Mystery_Resource",
                    address="terraform_data.mystery",
                    type="terraform_data",
                    controls=("SC.L2-3.13.1",),
                    region=None,  # <- the invariant violation
                ),
            ),
        )

    def apply(self) -> ApplyResult:
        return ApplyResult(state_hash="never-applied", applied=True, resource_count=0)


# ---------------------------------------------------------------------------
# Invariant #1 — non-US region signal halts before Apply. This is asserted by
# test_pipeline.test_policy_failure_halts_before_apply already; we assert here
# that the halt reason names the residency violation specifically so a future
# refactor doesn't silently downgrade the message.
# ---------------------------------------------------------------------------

def test_non_us_region_halt_reason_names_residency():
    from tests.test_pipeline import NOW, _attested_order_ds
    from pipeline.backends.local import LocalBackend
    from pipeline.provision import FakeProvisionBackend
    from pipeline.runner import run_factory

    ds, order = _attested_order_ds()
    state = run_factory(
        ds, order.iri,
        provision_backend=FakeProvisionBackend(compliant=False),
        store_backend=LocalBackend(),
        now=NOW, run_preflight=False,
    )
    assert state.halted and state.halted_at == "PolicyCheck"
    # The residency-specific reason lives on state.policy_check.findings; the
    # top-level failure record wraps them as the halt reason.
    finding_reasons = " | ".join(f.reason for f in state.policy_check.findings)
    assert "residency" in finding_reasons.lower() or "not us" in finding_reasons.lower(), (
        finding_reasons
    )


# ---------------------------------------------------------------------------
# Invariant #2 — zero region signals halts the run (never silently passes).
# ---------------------------------------------------------------------------

def test_zero_region_signals_halt_the_run():
    from tests.test_pipeline import NOW, _attested_order_ds
    from pipeline.backends.local import LocalBackend
    from pipeline.runner import run_factory

    ds, order = _attested_order_ds()
    state = run_factory(
        ds, order.iri,
        provision_backend=_NoRegionBackend(),
        store_backend=LocalBackend(),
        now=NOW, run_preflight=False,
    )
    assert state.halted, "run must halt when the plan carries no region signals"
    assert state.halted_at == "PolicyCheck"
    finding_reasons = " | ".join(f.reason for f in state.policy_check.findings)
    assert "residency invariant" in finding_reasons, finding_reasons
    assert state.apply is None


# ---------------------------------------------------------------------------
# Real terraform: plan with primary_region=europe-west1 produces non-US signals
# in the plan JSON. The generator-level check flags them.
# ---------------------------------------------------------------------------

@pytest.mark.terraform
@pytest.mark.skipif(shutil.which("terraform") is None,
                    reason="terraform binary not installed")
def test_real_terraform_plan_flags_non_us_region():
    from evidence.generators.terraform_plan import TerraformPlanGenerator, _is_us_region

    gen = TerraformPlanGenerator(tf_vars={"primary_region": "europe-west1"})
    plan = gen.plan_json()
    signals = gen._region_signals(gen._planned_resources(plan))
    assert signals, "plan must carry at least one region signal"
    non_us = [s for s in signals if not _is_us_region(s)]
    assert non_us, "europe-west1 must appear as a non-US signal"
