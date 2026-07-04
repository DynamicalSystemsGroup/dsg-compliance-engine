"""The audit-package report (ce report).

Renders package/manifest.json into a self-contained HTML report (always) and a PDF
when the weasyprint binary is available. Also covers `ce demo --full` producing the
full 110-control package the report renders.
"""

from __future__ import annotations

import json
import re
import pathlib
import tempfile

import pytest
from typer.testing import CliRunner

from compliance_engine import cli
from compliance_engine.documents.report import (
    build_report_html,
    render_report,
    weasyprint_available,
)
from compliance_engine.order_compiler import compiler, cop

runner = CliRunner()

_SECTIONS = [
    "Audit Package",
    "What this report says",
    "How to read this report",
    "The score",
    "How each control was verified",
    "Integrity and verification",
    "Provenance",
    "Contradictions and overrides",
    "Control-by-control detail",
    "Full control catalog",
]


def _demo_package(out: pathlib.Path, *, full: bool = False):
    from compliance_engine.order_compiler import rule_library as rl

    ds, obligations = compiler.load_pipeline_dataset()
    obligations = dict(obligations)
    if full:
        obligations["OBL-FULL"] = rl.Obligation(
            "OBL-FULL", rl.FRAMEWORK, derives=frozenset({"ALL-110-NIST-800-171"})
        )
    cop_att = cop.attest_cop(ds, obligations, auto=True, now=cli.RUN_SEED_TS)
    order = compiler.compile_order(ds, obligations, cop_att, now=cli.RUN_SEED_TS)
    state = cli._do_run_factory(ds, order.iri, "all-covered", "fake", out)
    cli._do_attest(ds, state)
    report = cli._do_audit(ds, out)
    bom = cli._do_bom(state, ds, out)
    cli._save_ds(ds, out)
    cli._ssp_hook(out, ds=ds, audit_report=report, bom=bom)
    from compliance_engine.traceability.package import build_audit_package
    build_audit_package(ds, out, order.contract, audit_report=report, bom_hash=bom.bom_hash)
    return out / "package"


def test_report_html_has_all_sections_and_no_emoji():
    out = pathlib.Path(tempfile.mkdtemp(prefix="ce-rep-"))
    pkg = _demo_package(out)
    res = render_report(pkg)
    assert res.html_path.exists()
    html = res.html_path.read_text()
    for s in _SECTIONS:
        assert s in html, f"missing section: {s}"
    assert not re.findall(r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF]", html)


def test_report_pdf_when_weasyprint_present():
    out = pathlib.Path(tempfile.mkdtemp(prefix="ce-rep-"))
    pkg = _demo_package(out)
    res = render_report(pkg)
    if weasyprint_available():
        assert res.pdf_path is not None and res.pdf_path.exists()
        assert res.pdf_path.read_bytes()[:5] == b"%PDF-"
        assert res.pdf_engine == "weasyprint"
    else:
        assert res.pdf_path is None and "weasyprint" in res.note.lower()


def test_render_report_errors_on_missing_manifest(tmp_path):
    with pytest.raises(FileNotFoundError):
        render_report(tmp_path / "no-package")


def test_build_report_html_from_synthetic_manifest():
    manifest = {
        "contract": "NV012", "bom_hash": "abc123", "evidentiary_status": "mock",
        "sprs": {"score": 110, "status": "Final", "valid_submission": True},
        "proven_vs_attested": {"machine": 4, "human_only": 18},
        "provenance": {"sop_adherence_ok": True, "executed_steps": ["EmitOrder", "Oracles"], "deviations": []},
        "contradictions": [],
        "controls": [{"control": "AC.L2-3.1.1", "status": "MET", "evidence_backing": "machine",
                      "oracle_outcome": "passed", "attestation": {"outcome": "passed"},
                      "policy_references": []}],
        "policies": [], "artifacts": [{"name": "bom.json", "sha256": "deadbeef"}],
    }
    html = build_report_html(manifest, {"sig_algo": "ed25519-v1", "key_id": "d8ec6f0e"})
    assert "NON-EVIDENTIARY" in html.upper()  # mock -> banner
    assert "AC.L2-3.1.1" in html and "ed25519-v1" in html
    # Plain-language verdict is rendered from the numbers, not a static string.
    assert "1 of 1" in html and "Access Control" in html


def test_ce_package_writes_report_into_package_dir():
    """`ce package` renders the report into package/ so it travels with the manifest."""
    out = pathlib.Path(tempfile.mkdtemp(prefix="ce-pkg-"))
    assert runner.invoke(cli.app, ["demo", "--output-dir", str(out)]).exit_code == 0
    result = runner.invoke(cli.app, ["package", "--output-dir", str(out)])
    assert result.exit_code == 0, result.output
    assert (out / "package" / "report.html").exists()
    if weasyprint_available():
        assert (out / "package" / "report.pdf").exists()


def test_ce_demo_full_produces_110_control_package():
    out = pathlib.Path(tempfile.mkdtemp(prefix="ce-full-"))
    result = runner.invoke(cli.app, ["demo", "--full", "--output-dir", str(out)])
    assert result.exit_code == 0, result.output
    manifest = json.loads((out / "package" / "manifest.json").read_text())
    assert len(manifest["controls"]) == 110
    assert manifest["sprs"]["score"] == 110 and manifest["sprs"]["status"] == "Final"
