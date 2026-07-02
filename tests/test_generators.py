"""Tests for the mocked evidence generators (U6b).

A generator reads ``fixtures/nv012/<set>/*.json`` and yields ``EvidenceArtifact``s
whose ``summary`` keys match ``oracles/criteria.py`` metric_keys and whose
``controls`` name the addressed controls. The three fixture sets drive the U13
happy path / gap / contradiction cases.
"""

from __future__ import annotations

import json

import pytest

from evidence.binding import CollectionMetadata
from evidence.generators import EvidenceArtifact, Generator, GeneratorContext
from evidence.generators.mock_config import MockConfigExportGenerator
from evidence.generators.mock_policy import MockPolicyCheckGenerator

# summary keys the oracles read (must stay aligned with oracles/criteria.py).
_ORACLE_KEYS = {
    "mfa_enforced_privileged",
    "fips_module_present",
    "cui_encrypted_at_rest",
    "unauthorized_principals",
    "data_region",
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
        # 5 fixture exports in all-covered → 5 artifacts.
        assert len(arts) == 5
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

    def test_gap_set_omits_fips_control(self):
        arts = MockConfigExportGenerator().collect(GeneratorContext(evidence_set="gap"))
        addressed = {c for a in arts for c in a.controls}
        # gap/ drops the FIPS export -> SC.L2-3.13.11 is unaddressed (Gate-1 refusal).
        assert "SC.L2-3.13.11" not in addressed
        assert "fips_module_present" not in _summary_keys(arts)
        # The other four criteria are still present.
        assert "IA.L2-3.5.3" in addressed

    def test_contradiction_set_has_failing_mfa(self):
        arts = MockConfigExportGenerator().collect(GeneratorContext(evidence_set="contradiction"))
        mfa = [a for a in arts if "mfa_enforced_privileged" in a.summary]
        assert mfa and mfa[0].summary["mfa_enforced_privileged"] is False

    def test_missing_set_dir_is_empty_not_error(self):
        arts = MockConfigExportGenerator().collect(GeneratorContext(evidence_set="does-not-exist"))
        assert arts == []


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
