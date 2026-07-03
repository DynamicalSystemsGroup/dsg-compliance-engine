"""The attested-reference oracle — the universal Track B check.

For a module that carries `ce:reference <REF>` and `ce:attestationRole <ROLE>`,
this oracle answers one question per control it claims:

    Is there a signed attestation (from a signer whose role satisfies the
    module's ce:attestationRole, or from the Affirming Official) over a
    ce:Reference that resolves into its authoritative source, and is that
    reference within its freshness window?

Five explicit branches, in order of check. Each failure yields a specific
`needsAction` or `failed` reason so the SSP / BOM / UI can present a concrete
work item instead of a shrug:

    1. reference-missing        → needsAction
    2. reference-unresolvable   → failed (bad URI / dead link)
    3. reference-stale          → failed  ("stale:172d>90d")
    4. awaiting-attestation     → needsAction
    5. signer-role-mismatch     → failed  ("ITAdmin!=SecurityOfficer")
    6. attestation-predates-ref → failed  (attestation older than lastVerified)
    → PASS

The oracle does NOT verify the substance of what the reference points at;
that is bob's judgement, captured in the attestation. The engine's role is
the bureaucracy layer: reference exists, is fresh, is attested by the right
role. See Zargham's model in docs/plans/2026-07-03-002-path-to-self-assessment.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from oracles.criteria import (
    OUTCOME_FAILED,
    OUTCOME_NEEDS_ACTION,
    OUTCOME_PASSED,
    OracleResult,
)
from oracles.freshness import check_freshness
from traceability.attestation_store import AttestationRecord

# The AO can attest anything — they carry § 1001 liability. Other roles must
# match the module's required ce:attestationRole.
AO_ROLE = "Role_AffirmingOfficial"


@dataclass(frozen=True)
class ReferenceView:
    """Materialized view of a ce:Reference for the oracle.

    Populated by traceability code from the RDF graph (or by tests directly).
    """
    id: str                       # slug of the ce:Reference IRI
    uri: str                      # ce:uri (empty ⇒ reference-missing)
    freshness_days: int           # ce:freshnessDays
    last_verified: datetime | None  # ce:lastVerified (None ⇒ never verified)
    source_system: str = ""       # ce:sourceSystem local name (optional)
    custodian: str = ""           # ce:custodian (optional)

    def is_resolvable(self) -> bool:
        """A reference is resolvable if it has a URI. Live resolution (does
        the URL 200?) is deferred to a resolver plugin per source-system; the
        engine's job here is to detect a *registered but empty* reference
        distinctly from a *not-yet-registered* one."""
        return bool(self.uri.strip())


def evaluate_attested_reference(
    control_id: str,
    reference: ReferenceView | None,
    required_role: str,
    attestations: Iterable[AttestationRecord],
    *,
    now: datetime | None = None,
) -> OracleResult:
    """Apply the attested-reference oracle to one control.

    Args:
        control_id:     the cmmc:Control being checked.
        reference:      the ce:Reference view for the module claiming this
                        control, or None if no reference is registered.
        required_role:  the module's ce:attestationRole (slug matching a
                        ce:Role individual). "Role_AffirmingOfficial" always
                        satisfies.
        attestations:   candidate AttestationRecords (usually all records
                        loaded from `attestations/` — this function filters).
        now:            override current time for tests.

    Returns:
        OracleResult with one of: passed / needsAction / failed. All
        needsAction / failed results carry a machine-readable `reason` so
        downstream consumers can present concrete work items.
    """
    now = now or datetime.now(timezone.utc)

    # Branch 1 — no reference registered.
    if reference is None:
        return OracleResult(
            control_id, None, OUTCOME_NEEDS_ACTION,
            "no ce:Reference registered for a module claiming this control",
            reason="reference-missing",
        )

    # Branch 2 — reference declared but no URI.
    if not reference.is_resolvable():
        return OracleResult(
            control_id, None, OUTCOME_FAILED,
            f"reference {reference.id!r} has no ce:uri",
            reason="reference-unresolvable",
        )

    # Branch 3 — reference stale beyond its freshness window.
    if reference.last_verified is None:
        return OracleResult(
            control_id, None, OUTCOME_NEEDS_ACTION,
            f"reference {reference.id!r} has never been ce:lastVerified",
            reason="reference-never-verified",
        )
    verdict = check_freshness(
        reference.last_verified, reference.freshness_days, now=now,
    )
    if not verdict.is_fresh:
        return OracleResult(
            control_id, verdict.age_days, OUTCOME_FAILED,
            f"reference {reference.id!r} is stale: {verdict.reason}",
            reason=verdict.reason,
        )

    # Filter attestations to those covering this reference AND this control.
    candidates = [
        a for a in attestations
        if reference.id in a.covers and control_id in a.controls_attested
    ]
    if not candidates:
        return OracleResult(
            control_id, None, OUTCOME_NEEDS_ACTION,
            f"reference {reference.id!r} registered and fresh, "
            f"but no attestation covers control {control_id}",
            reason="awaiting-attestation",
        )

    # Prefer the most recent attestation for the tie-break.
    candidates.sort(key=lambda a: a.signed_at, reverse=True)
    picked = candidates[0]

    # Branch 5 — signer's role must satisfy the module's required role
    # (or be the AO, who overrides).
    if picked.signer_role != AO_ROLE and picked.signer_role != required_role:
        return OracleResult(
            control_id, None, OUTCOME_FAILED,
            f"attestation {picked.id!r} signed by {picked.signer_role}, "
            f"required {required_role} (or {AO_ROLE})",
            reason=f"signer-role-mismatch:{picked.signer_role}!={required_role}",
        )

    # Branch 6 — attestation must not predate the reference's last_verified.
    # Signing before the evidence exists is a smell (the signer attested
    # something they hadn't seen the current form of).
    signed_at = datetime.fromisoformat(picked.signed_at)
    if signed_at < reference.last_verified:
        return OracleResult(
            control_id, None, OUTCOME_FAILED,
            f"attestation {picked.id!r} signed at {picked.signed_at} "
            f"predates reference lastVerified {reference.last_verified.isoformat()}",
            reason="attestation-predates-reference",
        )

    # The attestation itself may be declined (outcome=failed / cantTell /
    # needsAction). Propagate — the reference is fresh but the AO did not
    # attest MET.
    if picked.outcome != OUTCOME_PASSED:
        # Recreate the outcome literally so callers see needsAction as
        # needsAction (with a reason), and failed as failed.
        return OracleResult(
            control_id, None, picked.outcome,
            f"attestation {picked.id!r} outcome is {picked.outcome!r}: "
            f"{picked.notes or picked.adequacy or 'no rationale recorded'}",
            reason=(f"attestation-outcome:{picked.outcome}"
                    if picked.outcome == OUTCOME_NEEDS_ACTION else None),
        )

    return OracleResult(
        control_id, picked.id, OUTCOME_PASSED,
        f"attested MET by {picked.signer} ({picked.signer_role}) "
        f"over reference {reference.id!r} "
        f"({verdict.age_days}d old, within {reference.freshness_days}d)",
    )
