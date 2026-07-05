"""Typed per-stage Factory state.

Adapted from ADCS `pipeline/state.py`: the runner splits into stage-level free
functions threaded by a single `PipelineState`. Each stage attaches a frozen
result record so downstream stages read prior outputs without
re-querying the graph. `activity_to_stage` maps each Factory stage short-name to
its ordinal; it MUST enumerate the identical set as
`pipeline.plan_execution.STEP_NAMES` and `pipeline/plan.ttl` (guarded by a test).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from rdflib import Dataset

if TYPE_CHECKING:  # pragma: no cover
    from compliance_engine.pipeline.provision.base import ApplyResult, PlanResult, ProvisionBackend
    from compliance_engine.pipeline.backends.base import StoreBackend


# ---------------------------------------------------------------------------
# Frozen per-stage result records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LoadOrderResult:
    order_iri: str
    order_hash: str
    verified: bool
    contract: str
    tier: str
    impact_level: str
    standard: str
    required_controls: tuple[str, ...]
    included_modules: tuple[str, ...]


@dataclass(frozen=True)
class FetchResult:
    modules_verified: bool
    module_hashes: dict[str, str]          # module_local -> content hash (verified)


@dataclass(frozen=True)
class PlanStageResult:
    plan_result: "PlanResult"
    resource_ids: tuple[str, ...]
    plan_controls: tuple[str, ...]


@dataclass(frozen=True)
class PolicyFinding:
    resource_id: str
    reason: str
    detail: dict = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyCheckResult:
    passed: bool
    findings: tuple[PolicyFinding, ...]
    oracle_outcomes: dict[str, str]        # control_id -> passed|failed|needsAction


@dataclass(frozen=True)
class ApplyStageResult:
    state_hash: str
    applied: bool
    resource_count: int


@dataclass(frozen=True)
class EvidenceStageResult:
    evidence_node_count: int
    evidence_hashes: tuple[str, ...]
    controls_addressed: tuple[str, ...]


@dataclass(frozen=True)
class OracleStageResult:
    outcomes: dict[str, str]               # control_id -> passed|failed|needsAction
    assertion_iris: tuple[str, ...]


@dataclass(frozen=True)
class AttestedRefResult:
    """Track B (attested-reference) result for one control: the machine-recorded
    document evidence behind a human attestation, plus the oracle's verdict."""
    control_id: str
    reference_id: str
    outcome: str                           # passed|failed|needsAction
    reason: str | None
    sha256: str | None                     # content hash of the resolved document
    git_commit: str | None
    git_committed_at: str | None
    uploaded_by: str
    upload_sig_ok: bool                    # signed upload receipt re-verified
    evidence_iri: str | None               # ce:DocumentEvidence node IRI
    attestation_id: str | None             # AO record picked, if any
    flexo_version: str | None = None       # append-only version id (set on flexo persist)


@dataclass(frozen=True)
class StageFailure:
    stage: str
    reason: str
    detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# The threaded state
# ---------------------------------------------------------------------------

@dataclass
class PipelineState:
    """Mutable container threaded through every Factory stage.

    `ds` is mutated in place (named-graph writes); each stage assigns its frozen
    result record. A policy FAIL sets `halted=True`/`halted_at` and records a
    `StageFailure`; Apply and everything after it are skipped.
    """

    ds: Dataset
    provision_backend: "ProvisionBackend"
    store_backend: "StoreBackend"
    order_iri: str
    contract: str = "NV012"
    evidence_set: str = "all-covered"
    auto: bool = True
    now: str | None = None

    # per-stage records (populated as stages complete)
    load_order: LoadOrderResult | None = None
    fetch: FetchResult | None = None
    plan: PlanStageResult | None = None
    policy_check: PolicyCheckResult | None = None
    apply: ApplyStageResult | None = None
    evidence: EvidenceStageResult | None = None
    oracles: OracleStageResult | None = None
    # Track B: control_id -> attested-reference result (doc evidence + oracle verdict)
    attested_refs: dict[str, "AttestedRefResult"] = field(default_factory=dict)

    # control flow
    halted: bool = False
    halted_at: str | None = None
    failures: list[StageFailure] = field(default_factory=list)
    stage_activities: dict[str, Any] = field(default_factory=dict)
    # CollectEvidence → Oracles hand-off: [{iri, summary, controls}]
    evidence_index: list[dict] = field(default_factory=list)

    # Factory stage ordinals — MUST match plan_execution.STEP_NAMES + plan.ttl.
    activity_to_stage: dict[str, int] = field(default_factory=lambda: {
        "LoadOrder":       0,
        "FetchByHash":     1,
        "Plan":            2,
        "PolicyCheck":     3,
        "Apply":           4,
        "CollectEvidence": 5,
        "Oracles":         6,
        "Attestation":     7,   # not run by the Factory back-half
        "Audit":           8,
        "SignAndStore":    9,
    })

    def record_failure(self, stage: str, reason: str, **detail) -> None:
        self.failures.append(StageFailure(stage=stage, reason=reason, detail=detail))

    def halt(self, stage: str, reason: str, **detail) -> None:
        self.halted = True
        self.halted_at = stage
        self.record_failure(stage, reason, **detail)
