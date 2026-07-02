"""U4 — rule_library obligation -> control resolution + spillover guard."""
import sys
from pathlib import Path

import pytest

# order-compiler/ has a hyphen -> not an importable package name; add it to path.
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "order-compiler"))

import rule_library as rl  # noqa: E402


def test_obl_cmmc_l2_resolves_to_all_110():
    obl = rl.Obligation("OBL-CMMC-L2", rl.FRAMEWORK, derives={"ALL-110-NIST-800-171"})
    controls = rl.resolve(obl)
    assert len(controls) == 110
    # sanity: a couple of known IDs are present
    assert "AC.L2-3.1.1" in controls
    assert "SI.L2-3.14.7" in controls


def test_obl_itar_includes_fips_control_and_markers():
    obl = rl.Obligation(
        "OBL-ITAR", rl.PERSONNEL, data_marker=rl.ITAR, derives={"SC.L2-3.13.11"}
    )
    controls = rl.resolve(obl)
    assert "SC.L2-3.13.11" in controls
    # non-control policy markers are preserved on the ControlSet
    assert "US-PERSON" in controls.markers
    assert "RESIDENCY" in controls.markers


def test_obl_cui_boundary_control_set():
    obl = rl.Obligation("OBL-CUI-BOUNDARY", rl.DATA, data_marker=rl.CUI)
    controls = rl.resolve(obl)
    assert controls == {"AC.L2-3.1.1", "AC.L2-3.1.3", "SC.L2-3.13.8", "SC.L2-3.13.16"}


def test_obl_il5_resolves_empty_not_error():
    obl = rl.Obligation("OBL-IL5", rl.HOSTING, derives={"IL5-OVERLAY"})
    controls = rl.resolve(obl)
    assert controls == set()
    assert not controls  # falsy, empty


def test_il5_overlay_token_resolves_empty():
    obl = rl.Obligation("IL5-OVERLAY", rl.HOSTING)
    assert rl.resolve(obl) == set()


def test_phase1_env_marker():
    obl = rl.Obligation("OBL-PHASE1-ENV", rl.ENVIRONMENT, derives={"TIER1-SCOPE"})
    controls = rl.resolve(obl)
    assert controls == set()
    assert "TIER1-SCOPE" in controls.markers


def test_plain_deliverable_resolves_empty():
    obl = rl.Obligation("OBL-AUDIT-EVIDENCE", rl.DELIVERABLE)
    controls = rl.resolve(obl)
    assert controls == set()


def test_cui_marked_deliverable_raises_spillover():
    obl = rl.Obligation("OBL-VENDOR-PORTAL", rl.DELIVERABLE, data_marker=rl.CUI)
    with pytest.raises(rl.SpilloverReviewRequired) as exc:
        rl.resolve(obl)
    assert exc.value.obligation is obl


def test_itar_marked_deliverable_raises_spillover():
    obl = rl.Obligation("OBL-SOME-DELIVERABLE", rl.DELIVERABLE, data_marker=rl.ITAR)
    with pytest.raises(rl.SpilloverReviewRequired):
        rl.resolve(obl)


def test_unknown_control_id_raises():
    obl = rl.Obligation("OBL-BOGUS", rl.DATA, derives={"ZZ.L2-3.9.9"})
    with pytest.raises(rl.UnknownControlError):
        rl.resolve(obl)


def test_unknown_obligation_type_raises():
    obl = rl.Obligation("OBL-WEIRD", "made-up-type")
    with pytest.raises(ValueError):
        rl.resolve(obl)


def test_load_obligations_from_ttl_roundtrips_through_resolve():
    obls = rl.load_obligations()
    # the finalized COP defines these
    assert "OBL-CMMC-L2" in obls
    assert "OBL-IL5" in obls
    assert rl.resolve(obls["OBL-CMMC-L2"]) == rl.resolve(
        rl.Obligation("OBL-CMMC-L2", rl.FRAMEWORK)
    )
    # the CUI-marked deliverable from the ttl trips the guard
    with pytest.raises(rl.SpilloverReviewRequired):
        rl.resolve(obls["OBL-VENDOR-PORTAL"])
