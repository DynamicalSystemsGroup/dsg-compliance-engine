"""The signed audit package (Phase E).

Build the full deliverable from a real run, then re-verify it the way a C3PAO
would: the manifest signature must verify, every bundled artifact must re-hash to
its recorded value, and the per-control control->signed-policy chain must be
complete. Tampering with an artifact or the manifest must be caught.
"""

from __future__ import annotations

import json
import pathlib
import tempfile

from compliance_engine import cli
from compliance_engine.order_compiler import compiler, cop
from compliance_engine.traceability.package import (
    build_audit_package,
    verify_audit_package,
)


def _run_and_package():
    out = pathlib.Path(tempfile.mkdtemp(prefix="ce-pkg-"))
    ds, obligations = compiler.load_pipeline_dataset()
    cop_att = cop.attest_cop(ds, obligations, auto=True, now=cli.RUN_SEED_TS)
    order = compiler.compile_order(ds, obligations, cop_att, now=cli.RUN_SEED_TS)
    state = cli._do_run_factory(ds, order.iri, "all-covered", "fake", out)
    cli._do_attest(ds, state)
    report = cli._do_audit(ds, out)
    bom = cli._do_bom(state, ds, out)
    cli._save_ds(ds, out)
    cli._ssp_hook(out, ds=ds, audit_report=report, bom=bom)
    pkg = build_audit_package(
        ds, out, order.contract, audit_report=report, bom_hash=bom.bom_hash,
    )
    return out, pkg


def test_build_and_verify_roundtrip():
    out, pkg = _run_and_package()
    result = verify_audit_package(pkg.package_dir)
    assert result.ok, result.summary()
    assert result.signature_ok and result.artifacts_ok and result.chain_ok


def test_manifest_has_full_chain():
    _out, pkg = _run_and_package()
    m = pkg.manifest
    assert m["contract"] == "NV012"
    assert len(m["controls"]) == 22
    assert m["sprs"]["score"] == 110
    assert m["provenance"]["sop_adherence_ok"] is True
    # every MET control carries an attestation outcome
    for c in m["controls"]:
        if c["status"] == "MET":
            assert c["attestation"]["outcome"]
    # the signed-policy inventory (Track B references) is bundled for the assessor
    assert len(m["policies"]) >= 16
    assert all("ref" in p for p in m["policies"])


def test_tampered_artifact_is_detected():
    _out, pkg = _run_and_package()
    bom = pkg.package_dir / "bom.json"
    bom.write_text(bom.read_text() + "\n{}")
    result = verify_audit_package(pkg.package_dir)
    assert not result.ok
    assert not result.artifacts_ok


def test_ce_package_on_incomplete_dir_errors_clearly(tmp_path):
    from typer.testing import CliRunner

    from compliance_engine.cli import app

    result = CliRunner().invoke(app, ["package", "--output-dir", str(tmp_path / "empty")])
    assert result.exit_code == 2
    assert "No completed run" in result.output  # not a raw traceback


def test_tampered_manifest_breaks_signature():
    _out, pkg = _run_and_package()
    manifest = pkg.package_dir / "manifest.json"
    data = json.loads(manifest.read_text())
    data["sprs"]["score"] = 55  # forge a better-looking score
    manifest.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")))
    result = verify_audit_package(pkg.package_dir)
    assert not result.ok
    assert not result.signature_ok
