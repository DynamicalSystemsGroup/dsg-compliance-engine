"""Operator CLI driver (the one-command NV012 demo)."""

import json
import sys
from pathlib import Path

from typer.testing import CliRunner

from compliance_engine import cli

runner = CliRunner()
def _run(args, out: Path):
    return runner.invoke(cli.app, [*args, "--output-dir", str(out)])
# ---------------------------------------------------------------------------
# demo — happy path (all-covered)
# ---------------------------------------------------------------------------

def test_demo_all_covered_runs_full_chain(tmp_path):
    res = _run(["demo", "--evidence-set", "all-covered", "--auto"], tmp_path)
    assert res.exit_code == 0, res.output

    # Full chain markers present, incl. the SSP stub step.
    for marker in ("compile-order", "run-factory", "attest", "audit", "bom", "ssp"):
        assert marker in res.output
    # Full required set attested → SPRS 110 / Final / valid over the Order's set.
    assert "SPRS: score=110 status=Final valid_submission=True" in res.output
    audit = json.loads((tmp_path / "audit.json").read_text())
    assert audit["sprs"]["score"] == 110
    assert audit["sprs"]["status"] == "Final"
    assert audit["sprs"]["valid_submission"] is True
    assert not audit["contradictions"]

    # output/bom.json written and mock (R12).
    bom_path = tmp_path / "bom.json"
    assert bom_path.exists()
    bom = json.loads(bom_path.read_text())
    assert bom["evidentiary_status"] == "mock"
    assert bom["contract_id"] == "NV012"
    assert len(bom["control_mapping"]) == 22
    # Every required control is MET in the BOM (full coverage).
    assert all(row["status"] == "MET" for row in bom["control_mapping"])

    # SSP rendered from the run — NON-EVIDENTIARY banner (R12) + real colophon.
    assert "SSP: wrote" in res.output
    ssp = (tmp_path / "ssp.md").read_text()
    assert "NON-EVIDENTIARY" in ssp                       # R12 banner
    assert "SPRS summary: score 110 (Final)" in ssp        # ties SSP to the audit
    assert "contradictions: 0" in ssp
# ---------------------------------------------------------------------------
# demo — gap set stops at Gate 1
# ---------------------------------------------------------------------------

def test_demo_gap_stops_at_gate1(tmp_path):
    res = _run(["demo", "--evidence-set", "gap"], tmp_path)
    assert res.exit_code != 0
    assert "Gate 1 REFUSED" in res.output
    # Track A + B now cover all 110 catalog controls, so the demo names the
    # fake unknown control id (XX.L2-3.99.99) that trips the pre-Gate-1
    # catalog validator — same educational refusal path.
    assert "XX.L2-3.99.99" in res.output
    # Factory never ran → no BOM and no SSP written.
    assert not (tmp_path / "bom.json").exists()
    assert not (tmp_path / "ssp.md").exists()
# ---------------------------------------------------------------------------
# demo — contradiction set surfaces R13
# ---------------------------------------------------------------------------

def test_demo_contradiction_reports_r13(tmp_path):
    res = _run(["demo", "--evidence-set", "contradiction"], tmp_path)
    assert res.exit_code == 0, res.output
    assert "Contradictions (attested MET over failed machine check):" in res.output
    # A MET attestation over a failing oracle (mfa=False) → ≥1 contradiction.
    audit = json.loads((tmp_path / "audit.json").read_text())
    assert len(audit["contradictions"]) >= 1
    # The contradicted control (IA.L2-3.5.3) is still counted MET per the human
    # attestation — the contradiction dimension flags it, it is not dropped.
    contradicted = {c["control"] for c in audit["contradictions"]}
    assert "IA.L2-3.5.3" in contradicted
    assert "IA.L2-3.5.3" in audit["met_control_ids"]
    assert (tmp_path / "bom.json").exists()
    # SSP colophon reflects the contradiction.
    ssp = (tmp_path / "ssp.md").read_text()
    assert "contradictions: 1" in ssp
    assert "NON-EVIDENTIARY" in ssp
# ---------------------------------------------------------------------------
# ssp subcommand — ImportError stub path
# ---------------------------------------------------------------------------

def test_ssp_stub_when_module_absent(tmp_path, monkeypatch):
    # Simulate the SSP compiler being unavailable.
    import compliance_engine.cli as cli_mod
    def _mock(_out, **__):
        import typer
        typer.echo("SSP: skipped (documents/ssp.py not available)")
    monkeypatch.setattr(cli_mod, "_ssp_hook", _mock)
    res = _run(["ssp"], tmp_path)
    assert res.exit_code == 0
    assert "SSP: skipped" in res.output
def test_ssp_present_does_not_crash(tmp_path):
    res = _run(["ssp"], tmp_path)
    assert res.exit_code == 0
    assert "SSP:" in res.output
# ---------------------------------------------------------------------------
# invalid evidence set
# ---------------------------------------------------------------------------

def test_demo_rejects_unknown_evidence_set(tmp_path):
    res = _run(["demo", "--evidence-set", "nope"], tmp_path)
    assert res.exit_code == 2
# ---------------------------------------------------------------------------
# store-backend flexo — Registry/FlexoBackend composition (KI-2)
# ---------------------------------------------------------------------------

def test_demo_store_backend_flexo_exits_clean_and_reports_not_degraded(tmp_path):
    res = _run(
        ["demo", "--evidence-set", "all-covered", "--auto", "--store-backend", "flexo"],
        tmp_path,
    )
    assert res.exit_code == 0, res.output

    run_state = json.loads((tmp_path / "run_state.json").read_text())
    assert run_state["degraded"] is False

    # The BOM object landed in the Flexo registry-objects tier, not only local.
    # bom.json is written verbatim as the canonical bytes registry.put() hashes,
    # so re-hashing it recovers the exact key store_bom() used.
    from compliance_engine.pipeline.backends.flexo import FlexoBackend
    from compliance_engine.pipeline.registry import content_hash

    bom_bytes = (tmp_path / "bom.json").read_bytes()
    bom_hash = content_hash(bom_bytes)
    flexo = FlexoBackend(store_root=tmp_path / "flexo", ref="NV012")
    assert flexo.get_object(bom_hash) == bom_bytes


def test_demo_store_backend_local_reports_not_degraded(tmp_path):
    res = _run(["demo", "--evidence-set", "all-covered", "--auto"], tmp_path)
    assert res.exit_code == 0, res.output
    run_state = json.loads((tmp_path / "run_state.json").read_text())
    assert run_state["degraded"] is False
