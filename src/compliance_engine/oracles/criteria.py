"""Machine-checkable control criteria — verification, not validation.

SCAFFOLD, patterned on ADCS-lifecycle-demo/analysis/oracle.py.

An oracle pulls `metric_key` from an evidence artifact's `summary` dict and
compares it to `threshold` via `comparator`. A control with NO criterion here
returns `needsAction` with a concrete reason (register a criterion, or route the
control to the attested-reference oracle): the config oracle never shrugs. The
oracle NEVER asserts a control is MET — only the Affirming Official does that.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

OUTCOME_PASSED = "passed"
OUTCOME_FAILED = "failed"
OUTCOME_NEEDS_ACTION = "needsAction"

VALID_OUTCOMES: frozenset[str] = frozenset({
    OUTCOME_PASSED, OUTCOME_FAILED, OUTCOME_NEEDS_ACTION,
})

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
    outcome: str             # passed | failed | needsAction
    detail: str
    reason: str | None = None  # machine-readable reason (required for needsAction)

    def __post_init__(self) -> None:
        if self.outcome not in VALID_OUTCOMES:
            raise ValueError(f"invalid outcome {self.outcome!r}; "
                             f"expected one of {sorted(VALID_OUTCOMES)}")
        if self.outcome == OUTCOME_NEEDS_ACTION and not self.reason:
            raise ValueError("needsAction requires a machine-readable reason")


# Single source of truth for machine-checkable controls. This is the
# Tier 1-mapped machine set: it aligns 1:1 with the `ce:oracle-*`
# verificationMethod IRIs in structural/tier1.ttl (agent-1). Controls with no
# automatable signal (policy / training / PS / IR / physical) are ABSENT here on
# purpose — but they are NO LONGER left to shrug: they route through the
# attested-reference oracle (oracles/attested_reference.py, wired into
# run_stage_oracles) which resolves + freshness-checks + role-verifies their
# document reference and returns passed / needsAction / failed. A control routed
# to THIS table with no criterion returns needsAction("no-machine-criterion") —
# a concrete modeling gap to fix, never a silent shrug.
#
# Every metric_key is a real or plausible evidence-summary export field. The
# five confirmed keys emitted by the evidence generators are:
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
    # SC.L2-3.13.1 (boundary protection) is region-gated by the same org-policy
    # signal and is addressed by the mock_policy evidence (data_region). Without a
    # criterion here the oracle could not interpret evidence it could actually read —
    # the criterion makes it resolve to passed/failed like any machine control.
    "SC.L2-3.13.1":  Criterion("SC.L2-3.13.1", "data_region", "eq", "US",
                               "boundary protection: CUI data resident in US region"),
    # --- VPC segmentation (oracle-vpc-segmentation) --------------------------
    # One config-check criterion per SC.13 control the module claims. The
    # keys mirror fixtures/nv012/all-covered/gcp_vpc_segmentation.json summary.
    "SC.L2-3.13.3":  Criterion("SC.L2-3.13.3", "cui_subnet_private", "eq", True,
                               "separate CUI subnet from general access"),
    "SC.L2-3.13.4":  Criterion("SC.L2-3.13.4", "shared_resource_isolation", "eq", True,
                               "prevent unauthorized transfer via shared resources"),
    "SC.L2-3.13.5":  Criterion("SC.L2-3.13.5", "public_access_denied", "eq", True,
                               "deny public access to CUI subnetwork"),
    "SC.L2-3.13.6":  Criterion("SC.L2-3.13.6", "default_deny_ingress", "eq", True,
                               "default-deny network ingress"),
    "SC.L2-3.13.7":  Criterion("SC.L2-3.13.7", "split_tunnel_disabled", "eq", True,
                               "split-tunnel VPN disabled"),
    "SC.L2-3.13.8":  Criterion("SC.L2-3.13.8", "tls_minimum_version", "ge", "1.2",
                               "TLS 1.2+ enforced for crypto in transit"),
    "SC.L2-3.13.9":  Criterion("SC.L2-3.13.9", "session_termination_configured", "eq", True,
                               "network sessions terminate at end"),
    "SC.L2-3.13.15": Criterion("SC.L2-3.13.15", "session_authenticity_protected", "eq", True,
                               "communications session authenticity protected"),
    # --- EndpointVerification_CrowdStrike (oracle-endpoint-edr) --------------
    "SI.L2-3.14.2":  Criterion("SI.L2-3.14.2", "malware_protection_active", "eq", True,
                               "malware protection active on all endpoints"),
    "SI.L2-3.14.4":  Criterion("SI.L2-3.14.4", "av_definition_age_hours", "le", 24,
                               "AV definitions updated within 24h"),
    "SI.L2-3.14.7":  Criterion("SI.L2-3.14.7", "anomaly_detection_active", "eq", True,
                               "endpoint anomaly detection active"),
    # --- MDM_ChromeOS (oracle-mdm-policy) -----------------------------------
    "AC.L2-3.1.16":  Criterion("AC.L2-3.1.16", "wireless_authorized", "eq", True,
                               "wireless connections authorized before use"),
    "AC.L2-3.1.17":  Criterion("AC.L2-3.1.17", "wireless_crypto_enforced", "eq", True,
                               "WPA3 / 802.1X wireless crypto enforced"),
    "AC.L2-3.1.18":  Criterion("AC.L2-3.1.18", "mdm_enrolled", "eq", True,
                               "mobile device management enrolled"),
    "AC.L2-3.1.19":  Criterion("AC.L2-3.1.19", "mobile_encryption_at_rest", "eq", True,
                               "mobile CUI encrypted at rest"),
    "MP.L2-3.8.7":   Criterion("MP.L2-3.8.7", "removable_media_blocked", "eq", True,
                               "USB / removable media blocked for CUI OU"),
    # --- SecurityCommandCenter (oracle-scc-vuln-mgmt) -----------------------
    "RA.L2-3.11.2":  Criterion("RA.L2-3.11.2", "vuln_scan_age_days", "le", 30,
                               "vulnerability scan within last 30 days"),
    "SI.L2-3.14.1":  Criterion("SI.L2-3.14.1", "high_severity_findings_open", "eq", 0,
                               "no high-severity vuln findings open"),
    "SI.L2-3.14.5":  Criterion("SI.L2-3.14.5", "scan_coverage_complete", "eq", True,
                               "vuln scan coverage complete over CUI assets"),
    # --- WorkspaceAdmin_Policy (oracle-workspace-admin-policy) --------------
    "IA.L2-3.5.1":   Criterion("IA.L2-3.5.1", "user_uniquely_identified", "eq", True,
                               "each user uniquely identified"),
    "IA.L2-3.5.5":   Criterion("IA.L2-3.5.5", "identifier_reuse_days", "ge", 90,
                               "identifier reuse period ≥ 90 days"),
    "IA.L2-3.5.6":   Criterion("IA.L2-3.5.6", "inactive_disable_days", "le", 30,
                               "inactive accounts disabled ≤ 30 days"),
    "IA.L2-3.5.7":   Criterion("IA.L2-3.5.7", "password_complexity_enforced", "eq", True,
                               "password complexity enforced"),
    "IA.L2-3.5.8":   Criterion("IA.L2-3.5.8", "password_reuse_prohibited", "eq", True,
                               "password reuse prohibited"),
    "IA.L2-3.5.9":   Criterion("IA.L2-3.5.9", "temp_password_expires_first_use", "eq", True,
                               "temporary passwords expire at first use"),
    "IA.L2-3.5.10":  Criterion("IA.L2-3.5.10", "passwords_stored_hashed", "eq", True,
                               "stored passwords cryptographically protected"),
    "IA.L2-3.5.11":  Criterion("IA.L2-3.5.11", "auth_feedback_obscured", "eq", True,
                               "authentication feedback obscured"),
    # --- VPNAccess_BeyondCorp (oracle-beyondcorp-remote-access) -------------
    "AC.L2-3.1.12":  Criterion("AC.L2-3.1.12", "remote_sessions_monitored", "eq", True,
                               "all remote sessions monitored + controlled"),
    "AC.L2-3.1.13":  Criterion("AC.L2-3.1.13", "remote_tls_enforced", "eq", True,
                               "remote access encrypted (TLS/VPN)"),
    "AC.L2-3.1.14":  Criterion("AC.L2-3.1.14", "remote_routes_via_managed_proxy", "eq", True,
                               "remote access via managed access-control points"),
    # --- ChangeManagement_GitHub (oracle-github-change-mgmt) ----------------
    "CM.L2-3.4.3":   Criterion("CM.L2-3.4.3", "change_log_present", "eq", True,
                               "change log entries per commit"),
    "CM.L2-3.4.5":   Criterion("CM.L2-3.4.5", "required_reviews_enforced", "eq", True,
                               "required reviews + no force-push enforced"),
    # --- CloudIdentity_RemoteMaintenance (oracle-remote-maintenance-mfa) ----
    "MA.L2-3.7.5":   Criterion("MA.L2-3.7.5", "ops_mfa_enforced", "eq", True,
                               "MFA enforced for ops / break-glass roles"),
    # --- CloudLogging_Config (oracle-cloud-logging-config) -----------------
    "AU.L2-3.3.4":   Criterion("AU.L2-3.3.4", "log_failure_alerting", "eq", True,
                               "audit log processing failure alerting"),
    "AU.L2-3.3.7":   Criterion("AU.L2-3.3.7", "ntp_configured", "eq", True,
                               "NTP time sync configured"),
    "AU.L2-3.3.8":   Criterion("AU.L2-3.3.8", "log_bucket_access_restricted", "eq", True,
                               "audit log bucket access restricted"),
    "AU.L2-3.3.9":   Criterion("AU.L2-3.3.9", "audit_mgmt_privileged", "eq", True,
                               "audit management limited to privileged users"),
    # --- OrgPolicy_Allowlist (oracle-binauth-allowlist) ---------------------
    "CM.L2-3.4.8":   Criterion("CM.L2-3.4.8", "deny_by_default_binauth", "eq", True,
                               "deny-by-default image policy active"),
    "CM.L2-3.4.9":   Criterion("CM.L2-3.4.9", "user_software_approval_required", "eq", True,
                               "user-installed software approval workflow"),
    # --- OrgPolicy_SessionControl (oracle-session-control) ------------------
    "AC.L2-3.1.8":   Criterion("AC.L2-3.1.8", "failed_login_lockout_enabled", "eq", True,
                               "account lockout after N failed logins"),
    "AC.L2-3.1.10":  Criterion("AC.L2-3.1.10", "idle_session_timeout_minutes", "le", 15,
                               "idle session lock ≤ 15 minutes"),
    "AC.L2-3.1.11":  Criterion("AC.L2-3.1.11", "session_termination_conditions", "eq", True,
                               "session termination conditions configured"),
    # --- AccessTransparency_ExternalSystems (oracle-vpc-sc-perimeter) -------
    "AC.L2-3.1.20":  Criterion("AC.L2-3.1.20", "external_system_perimeter_defined", "eq", True,
                               "external system connections enumerated + authorized"),
    # --- IAMRoles_Privilege (oracle-iam-privileged-use) ---------------------
    "AC.L2-3.1.6":   Criterion("AC.L2-3.1.6", "non_privileged_accounts_used_for_non_security", "eq", True,
                               "non-privileged accounts used for non-security work"),
    "AC.L2-3.1.7":   Criterion("AC.L2-3.1.7", "privileged_actions_logged", "eq", True,
                               "non-admin attempts to run privileged functions logged"),
}


def evaluate(summary: dict[str, Any], control_id: str,
             criteria: dict[str, Criterion] = CRITERIA) -> OracleResult:
    """Evaluate one control's criterion against an evidence summary dict."""
    crit = criteria.get(control_id)
    if crit is None:
        return OracleResult(
            control_id, None, OUTCOME_NEEDS_ACTION,
            "no machine-readable criterion for a control routed to the config oracle "
            "— register a criterion or route it to the attested-reference oracle",
            reason="no-machine-criterion")
    if crit.metric_key not in summary:
        return OracleResult(
            control_id, None, OUTCOME_NEEDS_ACTION,
            f"metric {crit.metric_key!r} absent from evidence",
            reason="metric-absent")
    value = summary[crit.metric_key]
    ok = _COMPARATORS[crit.comparator](value, crit.threshold)
    return OracleResult(
        control_id, value,
        OUTCOME_PASSED if ok else OUTCOME_FAILED,
        f"{crit.metric_key} = {value!r} {crit.comparator} {crit.threshold!r} "
        f"-> {'pass' if ok else 'fail'} (config-level)",
    )
