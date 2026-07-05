"""Tests for the attested-reference machinery — the Track B foundation.

Covers:
  * oracles/freshness.py — annual/quarterly/event-based windows, error paths.
  * oracles/attested_reference.py — all six branches of the universal oracle.
  * traceability/attestation_store.py — JSONL roundtrip, validation errors,
    duplicate-id detection, content-hash stability.
  * End-to-end sanity — every Track B module in tier1.ttl + references.ttl +
    attestations/tier1.jsonl resolves to PASS via the real oracle.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path


import pytest
from rdflib import Graph, Namespace, URIRef

from compliance_engine.oracles.attested_reference import (
    AO_ROLE,
    ReferenceView,
    evaluate_attested_reference,
)
from compliance_engine.oracles.freshness import (
    ANNUAL,
    EVENT_BASED,
    POLICY_DAYS,
    QUARTERLY,
    check_freshness,
    resolve_policy,
)
from compliance_engine.traceability.attestation_store import (
    SIG_ALGO_COSIGN_V1,
    SIG_ALGO_NONE,
    VALID_ROLES,
    AttestationRecord,
    AttestationStoreError,
    append_record,
    load_all,
    load_file,
)

NOW = datetime(2026, 7, 3, tzinfo=timezone.utc)

# ---------------------------------------------------------------------------
# freshness
# ---------------------------------------------------------------------------

class TestFreshness:
    def test_annual_within_window(self):
        v = check_freshness(NOW - timedelta(days=100), ANNUAL, now=NOW)
        assert v.is_fresh and v.reason == "fresh" and v.age_days == 100

    def test_annual_beyond_window(self):
        v = check_freshness(NOW - timedelta(days=400), ANNUAL, now=NOW)
        assert not v.is_fresh and v.reason == "stale:400d>365d"

    def test_quarterly_boundary(self):
        # Exactly at boundary: still fresh (age <= window).
        v = check_freshness(NOW - timedelta(days=90), QUARTERLY, now=NOW)
        assert v.is_fresh
        v = check_freshness(NOW - timedelta(days=91), QUARTERLY, now=NOW)
        assert not v.is_fresh

    def test_event_based_never_stale(self):
        v = check_freshness(NOW - timedelta(days=9999), EVENT_BASED, now=NOW)
        assert v.is_fresh and v.reason == "event-based" and v.age_days is None

    def test_naive_datetime_rejected(self):
        with pytest.raises(ValueError, match="timezone-aware"):
            check_freshness(datetime(2026, 1, 1), 90)

    def test_negative_freshness_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            check_freshness(NOW, -1)

    def test_resolve_policy_by_name(self):
        assert resolve_policy("annual") == ANNUAL
        assert resolve_policy("quarterly") == QUARTERLY
        assert resolve_policy("event-based") == EVENT_BASED

    def test_resolve_policy_by_int(self):
        assert resolve_policy(42) == 42

    def test_resolve_policy_unknown_name(self):
        with pytest.raises(ValueError, match="unknown freshness policy"):
            resolve_policy("yearly")

    def test_all_policy_names_map_to_ints(self):
        assert all(isinstance(v, int) and v >= 0 for v in POLICY_DAYS.values())

# ---------------------------------------------------------------------------
# attested-reference oracle — the six-branch decision tree
# ---------------------------------------------------------------------------

def _ref(**kw):
    base = dict(id="ref-x", uri="https://ex/doc", freshness_days=365,
                last_verified=NOW - timedelta(days=30))
    base.update(kw)
    return ReferenceView(**base)

def _att(**kw):
    base = dict(
        id="att-1", signer="ao@dsg", signer_role="Role_AffirmingOfficial",
        signed_at="2026-07-01T12:00:00+00:00",  # after default ref lastVerified
        covers=("ref-x",), controls_attested=("IR.L2-3.6.1",),
        outcome="passed", adequacy="ok", sufficiency="ok",
    )
    base.update(kw)
    return AttestationRecord(**base)

class TestAttestedReferenceOracle:
    def test_no_reference_registered_yields_needsAction(self):
        r = evaluate_attested_reference("IR.L2-3.6.1", None, "Role_SecurityOfficer", [], now=NOW)
        assert r.outcome == "needsAction" and r.reason == "reference-missing"

    def test_empty_uri_yields_failed(self):
        r = evaluate_attested_reference("IR.L2-3.6.1", _ref(uri=""), "Role_SecurityOfficer", [], now=NOW)
        assert r.outcome == "failed" and r.reason == "reference-unresolvable"

    def test_never_verified_yields_needsAction(self):
        r = evaluate_attested_reference("IR.L2-3.6.1", _ref(last_verified=None),
                                        "Role_SecurityOfficer", [], now=NOW)
        assert r.outcome == "needsAction" and r.reason == "reference-never-verified"

    def test_stale_reference_yields_failed(self):
        r = evaluate_attested_reference(
            "IR.L2-3.6.1",
            _ref(freshness_days=90, last_verified=NOW - timedelta(days=200)),
            "Role_SecurityOfficer", [_att()], now=NOW,
        )
        assert r.outcome == "failed" and r.reason.startswith("stale:")

    def test_no_attestation_yields_needsAction(self):
        r = evaluate_attested_reference("IR.L2-3.6.1", _ref(), "Role_SecurityOfficer", [], now=NOW)
        assert r.outcome == "needsAction" and r.reason == "awaiting-attestation"

    def test_signer_role_mismatch_yields_failed(self):
        r = evaluate_attested_reference("IR.L2-3.6.1", _ref(),
                                        "Role_SecurityOfficer",
                                        [_att(signer_role="Role_ITAdmin")], now=NOW)
        assert r.outcome == "failed" and r.reason.startswith("signer-role-mismatch:")

    def test_attestation_predates_reference_yields_failed(self):
        r = evaluate_attested_reference(
            "IR.L2-3.6.1",
            _ref(last_verified=NOW - timedelta(days=5)),
            "Role_SecurityOfficer",
            [_att(signed_at="2026-06-01T12:00:00+00:00")],
            now=NOW,
        )
        assert r.outcome == "failed" and r.reason == "attestation-predates-reference"

    def test_declined_attestation_propagates(self):
        # needsAction has its own propagation test below (test_declined_needsAction_propagates).
        for declined in ("failed",):
            adequacy = "not ready" if declined == "failed" else "ok"
            sufficiency = "not ready" if declined == "failed" else ""
            r = evaluate_attested_reference(
                "IR.L2-3.6.1", _ref(), "Role_SecurityOfficer",
                [_att(outcome=declined, adequacy=adequacy, sufficiency=sufficiency)],
                now=NOW,
            )
            assert r.outcome == declined, declined

    def test_declined_needsAction_propagates(self):
        r = evaluate_attested_reference(
            "IR.L2-3.6.1", _ref(), "Role_SecurityOfficer",
            [_att(outcome="needsAction", adequacy="", sufficiency="", notes="not yet")],
            now=NOW,
        )
        assert r.outcome == "needsAction"

    def test_happy_path_ao(self):
        r = evaluate_attested_reference("IR.L2-3.6.1", _ref(),
                                        "Role_SecurityOfficer", [_att()], now=NOW)
        assert r.outcome == "passed"
        assert "attested MET" in r.detail

    def test_happy_path_domain_role(self):
        r = evaluate_attested_reference(
            "IR.L2-3.6.1", _ref(),
            "Role_SecurityOfficer", [_att(signer_role="Role_SecurityOfficer")], now=NOW,
        )
        assert r.outcome == "passed"

    def test_ao_overrides_role_requirement(self):
        # AO can attest ANY control regardless of the module's attestationRole.
        assert AO_ROLE == "Role_AffirmingOfficial"
        r = evaluate_attested_reference("IR.L2-3.6.1", _ref(),
                                        "Role_OPs", [_att()], now=NOW)
        assert r.outcome == "passed"

    def test_most_recent_attestation_wins_the_tie(self):
        # Given two attestations, prefer the most recent one for the role check.
        old = _att(id="att-old", signed_at="2026-06-16T12:00:00+00:00",
                   signer_role="Role_ITAdmin")
        new = _att(id="att-new", signed_at="2026-06-25T12:00:00+00:00",
                   signer_role="Role_AffirmingOfficial")
        r = evaluate_attested_reference("IR.L2-3.6.1", _ref(),
                                        "Role_SecurityOfficer", [old, new], now=NOW)
        assert r.outcome == "passed"

# ---------------------------------------------------------------------------
# attestation JSONL store
# ---------------------------------------------------------------------------

class TestAttestationStore:
    def _valid(self, **kw):
        base = dict(id="att-x", signer="a@b", signer_role="Role_ITAdmin",
                    signed_at="2026-07-03T12:00:00+00:00",
                    covers=("ref-1",), controls_attested=("AC.L2-3.1.1",),
                    outcome="passed", adequacy="ok", sufficiency="ok")
        base.update(kw)
        return AttestationRecord(**base)

    def test_roundtrip(self, tmp_path):
        r = self._valid()
        p = tmp_path / "att.jsonl"
        append_record(p, r)
        loaded = load_file(p)
        assert loaded == [r]

    def test_load_all_reads_every_jsonl(self, tmp_path):
        append_record(tmp_path / "a.jsonl", self._valid(id="att-a"))
        append_record(tmp_path / "b.jsonl", self._valid(id="att-b"))
        loaded = load_all(tmp_path)
        assert {r.id for r in loaded} == {"att-a", "att-b"}

    def test_load_all_missing_directory_returns_empty(self, tmp_path):
        assert load_all(tmp_path / "does-not-exist") == []

    def test_content_hash_stable_across_calls(self):
        r = self._valid()
        assert r.content_hash() == r.content_hash()

    def test_content_hash_ignores_sig_field(self):
        r1 = self._valid()
        r2 = self._valid(sig=None, sig_algo=SIG_ALGO_NONE)
        assert r1.content_hash() == r2.content_hash()

    def test_invalid_role_rejected(self):
        with pytest.raises(AttestationStoreError, match="invalid signer_role"):
            self._valid(signer_role="Role_CFO")

    def test_invalid_outcome_rejected(self):
        with pytest.raises(AttestationStoreError, match="invalid outcome"):
            self._valid(outcome="wat")

    def test_empty_covers_rejected(self):
        with pytest.raises(AttestationStoreError, match="covers must reference"):
            self._valid(covers=())

    def test_empty_controls_rejected(self):
        with pytest.raises(AttestationStoreError, match="controls_attested"):
            self._valid(controls_attested=())

    def test_naive_timestamp_rejected(self):
        with pytest.raises(AttestationStoreError, match="timezone-aware"):
            self._valid(signed_at="2026-07-03T12:00:00")

    def test_bad_iso_timestamp_rejected(self):
        with pytest.raises(AttestationStoreError, match="not ISO-8601"):
            self._valid(signed_at="whenever")

    def test_passed_without_texts_rejected(self):
        with pytest.raises(AttestationStoreError, match="requires non-empty"):
            self._valid(adequacy="", sufficiency="")

    def test_sig_with_none_algo_rejected(self):
        with pytest.raises(AttestationStoreError, match="sig_algo=none forbids"):
            self._valid(sig="deadbeef", sig_algo=SIG_ALGO_NONE)

    def test_cosign_algo_requires_sig(self):
        with pytest.raises(AttestationStoreError, match="requires a sig"):
            self._valid(sig=None, sig_algo=SIG_ALGO_COSIGN_V1)

    def test_duplicate_id_rejected(self, tmp_path):
        p = tmp_path / "dup.jsonl"
        r = self._valid()
        append_record(p, r)
        append_record(p, r)
        with pytest.raises(AttestationStoreError, match="duplicate record id"):
            load_file(p)

    def test_valid_roles_are_the_four(self):
        assert VALID_ROLES == {"Role_AffirmingOfficial", "Role_SecurityOfficer",
                                "Role_ITAdmin", "Role_OPs"}

# ---------------------------------------------------------------------------
# End-to-end — every Track B module resolves to PASS against the real files
# ---------------------------------------------------------------------------

class TestTrackBEndToEnd:
    """Load structural/tier1.ttl + references.ttl + attestations/*.jsonl,
    run the attested-reference oracle over every Track B module, and assert
    every claimed control PASSes."""

    def test_every_track_b_control_passes(self):
        g = Graph()
        g.parse(Path(__file__).resolve().parent.parent / "data" / "structural" / "tier1.ttl", format="turtle")
        g.parse(Path(__file__).resolve().parent.parent / "data" / "structural" / "references.ttl", format="turtle")

        CE = Namespace("http://dynamicalsystems.group/compliance-engine/")

        # Discover modules by verificationMethod = ce:oracle-attested-reference.
        q = """
        PREFIX ce:<http://dynamicalsystems.group/compliance-engine/>
        PREFIX cmmc:<http://dynamicalsystems.group/ontology/cmmc#>
        SELECT ?mod ?ref ?role ?ctrl WHERE {
            ?mod cmmc:verificationMethod ce:oracle-attested-reference ;
                 ce:reference ?ref ;
                 ce:attestationRole ?role ;
                 cmmc:controlsSatisfied ?ctrl .
        }
        """
        modules: dict[str, dict] = {}
        for mod, ref, role, ctrl in g.query(q):
            key = str(mod).rsplit("/", 1)[-1]
            m = modules.setdefault(key, {
                "ref": str(ref).rsplit("/", 1)[-1],
                "role": str(role).rsplit("/", 1)[-1],
                "controls": [],
            })
            m["controls"].append(str(ctrl).rsplit("#", 1)[-1].rsplit("/", 1)[-1])

        assert len(modules) == 16, f"expected 16 Track B modules, got {len(modules)}"

        def read_ref(rid: str) -> ReferenceView:
            ref = URIRef(str(CE) + rid)
            uri = str(next(g.objects(ref, CE.uri)))
            fd = int(str(next(g.objects(ref, CE.freshnessDays))))
            lv = datetime.fromisoformat(str(next(g.objects(ref, CE.lastVerified))))
            return ReferenceView(id=rid, uri=uri, freshness_days=fd, last_verified=lv)

        atts = load_all(Path(__file__).resolve().parent.parent / "data" / "attestations")
        assert len(atts) == 16

        results = {}
        for mod_name, d in modules.items():
            ref = read_ref(d["ref"])
            for ctrl in d["controls"]:
                r = evaluate_attested_reference(ctrl, ref, d["role"], atts, now=NOW)
                results[(mod_name, ctrl)] = r.outcome

        non_pass = {k: v for k, v in results.items() if v != "passed"}
        assert not non_pass, f"non-passing Track B controls: {non_pass}"
        # 43 Track B controls, all PASS.
        assert len(results) == 43
