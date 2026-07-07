"""Tests for the mocked evidence generators.

A generator reads ``fixtures/nv012/<set>/*.json`` and yields ``EvidenceArtifact``s
whose ``summary`` keys match ``oracles/criteria.py`` metric_keys and whose
``controls`` name the addressed controls. The three fixture sets drive the
happy path / gap / contradiction end-to-end scenarios.
"""

from __future__ import annotations

import json

import pytest

from compliance_engine.pipeline.evidence.binding import CollectionMetadata
from compliance_engine.pipeline.evidence.generators import EvidenceArtifact, Generator, GeneratorContext
from compliance_engine.pipeline.evidence.generators.mock_config import MockConfigExportGenerator
from compliance_engine.pipeline.evidence.generators.mock_policy import MockPolicyCheckGenerator

# summary keys the oracles read (must stay aligned with oracles/criteria.py).
# 5 Tier-1 keys + 45 Track A summary keys across 13 fixture files.
_ORACLE_KEYS = {
    # Tier 1 (5)
    "mfa_enforced_privileged", "fips_module_present", "cui_encrypted_at_rest",
    "unauthorized_principals", "data_region",
    # VPC_Segmentation (8)
    "cui_subnet_private", "shared_resource_isolation", "public_access_denied",
    "default_deny_ingress", "split_tunnel_disabled", "tls_minimum_version",
    "session_termination_configured", "session_authenticity_protected",
    # EndpointVerification_CrowdStrike (3)
    "malware_protection_active", "av_definition_age_hours", "anomaly_detection_active",
    # MDM_ChromeOS (5)
    "wireless_authorized", "wireless_crypto_enforced", "mdm_enrolled",
    "mobile_encryption_at_rest", "removable_media_blocked",
    # SecurityCommandCenter (3)
    "vuln_scan_age_days", "high_severity_findings_open", "scan_coverage_complete",
    # WorkspaceAdmin_Policy (8)
    "user_uniquely_identified", "identifier_reuse_days", "inactive_disable_days",
    "password_complexity_enforced", "password_reuse_prohibited",
    "temp_password_expires_first_use", "passwords_stored_hashed",
    "auth_feedback_obscured",
    # VPNAccess_BeyondCorp (3)
    "remote_sessions_monitored", "remote_tls_enforced", "remote_routes_via_managed_proxy",
    # ChangeManagement_GitHub (2)
    "change_log_present", "required_reviews_enforced",
    # CloudIdentity_RemoteMaintenance (1)
    "ops_mfa_enforced",
    # CloudLogging_Config (4)
    "log_failure_alerting", "ntp_configured", "log_bucket_access_restricted",
    "audit_mgmt_privileged",
    # OrgPolicy_Allowlist (2)
    "deny_by_default_binauth", "user_software_approval_required",
    # OrgPolicy_SessionControl (3)
    "failed_login_lockout_enabled", "idle_session_timeout_minutes",
    "session_termination_conditions",
    # AccessTransparency_ExternalSystems (1)
    "external_system_perimeter_defined",
    # IAMRoles_Privilege (2)
    "non_privileged_accounts_used_for_non_security", "privileged_actions_logged",
    # Access enforcement (3)
    "transaction_type_restrictions_enforced", "cui_flow_control_enforced",
    "overprivileged_bindings",
    # Audit & accountability (3)
    "audit_log_export_enabled", "audit_user_attribution_enabled", "audit_correlation_enabled",
    # Configuration management (4)
    "config_baseline_established", "config_change_enforcement_active",
    "least_functionality_enforced", "nonessential_services_disabled",
    # Identification & authentication (2)
    "device_authentication_required", "replay_resistant_auth_enabled",
    # Crypto KM + system integrity (3)
    "key_management_established", "security_alert_response_enabled",
    "network_attack_monitoring_active",
}


def _summary_keys(artifacts: list[EvidenceArtifact]) -> set[str]:
    keys: set[str] = set()
    for a in artifacts:
        keys |= set(a.summary)
    return keys


class TestProtocolConformance:
    def test_generators_satisfy_protocol(self):
        assert isinstance(MockConfigExportGenerator(), Generator)
        assert isinstance(MockPolicyCheckGenerator(), Generator)


class TestMockConfigExportGenerator:
    def test_all_covered_emits_every_criterion(self):
        arts = MockConfigExportGenerator().collect(GeneratorContext(evidence_set="all-covered"))
        # 18 original fixtures + 5 coverage-completing fixtures = 23 artifacts.
        assert len(arts) == 18 + 5 == 23
        # Every machine criterion's metric appears in some fixture summary — no
        # control claims a config oracle without evidence to feed it.
        assert _summary_keys(arts) == _ORACLE_KEYS

    def test_artifact_shape(self):
        arts = MockConfigExportGenerator().collect(GeneratorContext(evidence_set="all-covered"))
        a = arts[0]
        assert isinstance(a.raw_bytes, bytes)
        assert a.evidentiary_status == "mock"
        assert a.method == "config-export"
        assert a.controls  # non-empty
        assert isinstance(a.collection_metadata, CollectionMetadata)
        assert a.collection_metadata.source_system
        # raw_bytes round-trips to JSON (used by binding for hashing).
        assert isinstance(json.loads(a.raw_bytes.decode()), dict)

    def test_gap_set_layers_over_base(self):
        # Scenario sets layer over all-covered, so gap inherits full evidence
        # coverage. The gap SCENARIO refuses at Gate 1 structurally (it injects a
        # non-catalog control with no claiming module), not by omitting evidence.
        arts = MockConfigExportGenerator().collect(GeneratorContext(evidence_set="gap"))
        addressed = {c for a in arts for c in a.controls}
        assert "SC.L2-3.13.11" in addressed          # FIPS inherited from base
        assert "fips_module_present" in _summary_keys(arts)
        assert "IA.L2-3.5.3" in addressed

    def test_contradiction_set_has_failing_mfa(self):
        arts = MockConfigExportGenerator().collect(GeneratorContext(evidence_set="contradiction"))
        mfa = [a for a in arts if "mfa_enforced_privileged" in a.summary]
        assert mfa and mfa[0].summary["mfa_enforced_privileged"] is False

    def test_missing_set_dir_falls_back_to_base(self):
        # A non-base set that has no dir of its own layers over all-covered, so it
        # yields the base coverage rather than raising or coming back empty.
        arts = MockConfigExportGenerator().collect(GeneratorContext(evidence_set="does-not-exist"))
        base = MockConfigExportGenerator().collect(GeneratorContext(evidence_set="all-covered"))
        assert len(arts) == len(base) and len(arts) > 0


class TestMockPolicyCheckGenerator:
    def test_emits_policy_checks_for_checked_controls(self):
        arts = MockPolicyCheckGenerator().collect(GeneratorContext(evidence_set="all-covered"))
        # IAM (AC.L2-3.1.1) + region (SC.L2-3.13.1) fixtures each yield one check.
        addressed = {c for a in arts for c in a.controls}
        assert addressed == {"AC.L2-3.1.1", "SC.L2-3.13.1"}
        for a in arts:
            assert a.method == "policy-check"
            assert a.tool == "opa"
            assert a.result is not None
            assert a.result["status"] in {"PASS", "FAIL"}

    def test_all_covered_checks_pass(self):
        arts = MockPolicyCheckGenerator().collect(GeneratorContext(evidence_set="all-covered"))
        assert all(a.result["status"] == "PASS" for a in arts)


@pytest.mark.parametrize("evidence_set", ["all-covered", "gap", "contradiction"])
def test_both_generators_overlap_on_iam_control(evidence_set):
    """Config + policy generators both address AC.L2-3.1.1 (coverage overlap)."""
    cfg = MockConfigExportGenerator().collect(GeneratorContext(evidence_set=evidence_set))
    pol = MockPolicyCheckGenerator().collect(GeneratorContext(evidence_set=evidence_set))
    assert any("AC.L2-3.1.1" in a.controls for a in cfg)
    assert any("AC.L2-3.1.1" in a.controls for a in pol)
