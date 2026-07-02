"""Machine-checkable control criteria — verification, not validation.

SCAFFOLD, patterned on ADCS-lifecycle-demo/analysis/oracle.py.

An oracle pulls `metric_key` from an evidence artifact's `summary` dict and
compares it to `threshold` via `comparator`. A control with NO criterion here
returns `cantTell` on purpose: it must be human-attested from documentary
evidence. The oracle NEVER asserts a control is MET — only the Affirming
Official does that.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

OUTCOME_PASSED = "passed"
OUTCOME_FAILED = "failed"
OUTCOME_CANTTELL = "cantTell"

_COMPARATORS = {
    "eq": lambda v, t: v == t,
    "ne": lambda v, t: v != t,
    "le": lambda v, t: v <= t,
    "ge": lambda v, t: v >= t,
    "in": lambda v, t: v in t,
}


@dataclass(frozen=True)
class Criterion:
    control_id: str
    metric_key: str          # key into an evidence artifact's summary dict
    comparator: str          # eq | ne | le | ge | in
    threshold: Any
    label: str = ""


@dataclass(frozen=True)
class OracleResult:
    control_id: str
    metric_value: Any
    outcome: str             # passed | failed | cantTell
    detail: str


# Single source of truth for machine-checkable controls. This is the
# Tier 1-mapped machine set: it aligns 1:1 with the `ce:oracle-*`
# verificationMethod IRIs in structural/tier1.ttl (agent-1). The ~40 controls
# with no automatable signal (policy / training / PS / IR / physical) are
# intentionally ABSENT → evaluate() returns cantTell for them (never fabricate).
#
# Every metric_key is a real or plausible evidence-summary export field. The
# five confirmed keys emitted by U6 (agent-3) are:
#   mfa_enforced_privileged (bool), fips_module_present (bool),
#   cui_encrypted_at_rest (bool), unauthorized_principals (int), data_region (str).
# Two further plausible fields are added (documented at their entries):
#   overprivileged_bindings (int)  — an IAM-count signal
#   audit_log_export_enabled (bool) — a logging signal
CRITERIA: dict[str, Criterion] = {
    # --- MFA (oracle-mfa-2sv-enforced) ---
    "IA.L2-3.5.3":   Criterion("IA.L2-3.5.3", "mfa_enforced_privileged", "eq", True,
                               "MFA enforced for privileged access"),
    # --- FIPS crypto + CUI-at-rest (oracle-cmek-fips-keyring) ---
    "SC.L2-3.13.11": Criterion("SC.L2-3.13.11", "fips_module_present", "eq", True,
                               "FIPS-validated crypto module present (CMVP cert)"),
    "SC.L2-3.13.16": Criterion("SC.L2-3.13.16", "cui_encrypted_at_rest", "eq", True,
                               "CUI encrypted at rest (CMK)"),
    # --- IAM (oracle-iam-least-privilege) ---
    "AC.L2-3.1.1":   Criterion("AC.L2-3.1.1", "unauthorized_principals", "eq", 0,
                               "no unauthorized principals with access"),
    # IAM-count signal: least privilege == zero role bindings above the CUI-OU
    # baseline. `overprivileged_bindings` is a plausible IAM-audit export field
    # (count of bindings exceeding least-privilege baseline).
    "AC.L2-3.1.5":   Criterion("AC.L2-3.1.5", "overprivileged_bindings", "le", 0,
                               "least privilege: no overprivileged IAM role bindings"),
    # --- Logging (oracle-auditlog-export) ---
    # Logging signal: audit-log export to retained storage is enabled.
    # `audit_log_export_enabled` is a plausible Workspace/GCP export field.
    "AU.L2-3.3.1":   Criterion("AU.L2-3.3.1", "audit_log_export_enabled", "eq", True,
                               "audit logs created and exported to retained storage"),
    # --- Data residency (oracle-orgpolicy-us-residency) ---
    # ITAR residency (modelled as a pseudo-control id, not a NIST 800-171 control)
    "ITAR-120.54":   Criterion("ITAR-120.54", "data_region", "eq", "US",
                               "data residency US-only"),
}


def evaluate(summary: dict[str, Any], control_id: str,
             criteria: dict[str, Criterion] = CRITERIA) -> OracleResult:
    """Evaluate one control's criterion against an evidence summary dict."""
    crit = criteria.get(control_id)
    if crit is None:
        return OracleResult(control_id, None, OUTCOME_CANTTELL,
                            "no machine-readable criterion — requires human attestation")
    if crit.metric_key not in summary:
        return OracleResult(control_id, None, OUTCOME_CANTTELL,
                            f"metric {crit.metric_key!r} absent from evidence")
    value = summary[crit.metric_key]
    ok = _COMPARATORS[crit.comparator](value, crit.threshold)
    return OracleResult(
        control_id, value,
        OUTCOME_PASSED if ok else OUTCOME_FAILED,
        f"{crit.metric_key} = {value!r} {crit.comparator} {crit.threshold!r} "
        f"-> {'pass' if ok else 'fail'} (config-level)",
    )
