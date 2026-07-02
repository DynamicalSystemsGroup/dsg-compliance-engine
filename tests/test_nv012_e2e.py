"""U13 — NV012 end-to-end acceptance characterization (the capstone).

Drives the whole chain programmatically (NOT via cli.py) through the committed
entry points, proving three end-states:

  * all-covered  → Gate 1 passes → Factory runs → all 22 required controls
                   attested MET → SPRS 110 / Final / valid → BOM (mock) → SSP
                   with the R12 NON-EVIDENTIARY banner; registry resolves
                   NV012 → latest BOM → artifact hashes.
  * gap          → an uncovered 5-point required control → Gate 1 refuses,
                   naming the gap; the Factory never runs.
  * contradiction→ an oracle FAILS but the official attests MET without an
                   override → the audit's R13 contradiction dimension fires and
                   the SSP surfaces it; adding an override clears it.

Timestamps are fed (now=NOW) to every entry point that accepts one, so the
chain is deterministic. (request_attestation stamps event-time; see the
"BUG FOUND / observation" note in results — it does not affect these
semantic assertions.)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "order-compiler") not in sys.path:
    sys.path.insert(0, str(_ROOT / "order-compiler"))

import compiler  # noqa: E402
import cop  # noqa: E402
import rule_library as rl  # noqa: E402
from rdflib.namespace import RDF  # noqa: E402

from ontology.prefixes import CE  # noqa: E402
from pipeline.backends.local import LocalBackend  # noqa: E402
from pipeline.dataset import graph_for  # noqa: E402
from pipeline.provision import FakeProvisionBackend  # noqa: E402
from pipeline.registry import Registry  # noqa: E402
from pipeline.runner import run_factory  # noqa: E402
from traceability import audit as auditmod  # noqa: E402
from traceability import bom as bommod  # noqa: E402
from traceability.attestation import (  # noqa: E402
    OUTCOME_FAILED,
    OUTCOME_PASSED,
    request_attestation,
)
from documents.ssp import compile_ssp_from_run  # noqa: E402

NOW = "2026-07-02T00:00:00+00:00"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _compile_order():
    """Front-half: load NV012 COP → attest → compile the Order (Gate 1 passes)."""
    ds, obl = compiler.load_pipeline_dataset()
    att = cop.attest_cop(ds, obl, auto=True, now=NOW)
    order = compiler.compile_order(ds, obl, att, now=NOW)
    return ds, order


def _run_factory(ds, order, evidence_set):
    return run_factory(
        ds, order.iri,
        provision_backend=FakeProvisionBackend(),
        store_backend=LocalBackend(),
        evidence_set=evidence_set,
        now=NOW,
        run_preflight=False,
    )


def _attest_met(ds, controls, **kw):
    for cid in controls:
        request_attestation(ds, cid, "Jane Official", auto_attest=True,
                            adequacy="Implementation adequate.",
                            sufficiency="Evidence sufficient for MET.",
                            outcome=OUTCOME_PASSED, **kw)


def _vcrm_status(doc: str, control_id: str) -> str:
    """The Status cell (column 6) for a control's VCRM row."""
    for line in doc.splitlines():
        if line.startswith(f"| {control_id} |"):
            return line.split("|")[6].strip()
    raise AssertionError(f"{control_id} not found in the VCRM")


# --------------------------------------------------------------------------- #
# Scenario 1 — AE happy path (all-covered)
# --------------------------------------------------------------------------- #

class TestHappyPathAllCovered:
    def _run(self, tmp_path):
        ds, order = _compile_order()
        required = sorted(order.required_controls)
        state = _run_factory(ds, order, "all-covered")
        assert not state.halted
        _attest_met(ds, required)
        report = auditmod.audit(ds)
        bom = bommod.build_bom(state, ds, "NV012")
        reg = Registry(tmp_path / "registry")
        bom_hash = bommod.store_bom(bom, reg, "NV012")
        ssp = compile_ssp_from_run(ds, audit_report=report, bom=bom)
        return ds, order, state, report, bom, reg, bom_hash, ssp, required

    def test_gate1_passes_and_factory_completes(self, tmp_path):
        _ds, order, state, *_ = self._run(tmp_path)
        assert len(order.required_controls) == 22
        assert state.evidence is not None and state.oracles is not None

    def test_sprs_110_final_valid(self, tmp_path):
        *_, report, _bom, _reg, _h, _ssp, _req = self._run(tmp_path)
        assert report.sprs is not None
        assert report.sprs.score == 110
        assert report.sprs.status == "Final"
        assert report.sprs.valid_submission is True

    def test_bom_and_run_carry_mock_evidentiary_status(self, tmp_path):
        _ds, _order, _state, _report, bom, *_ = self._run(tmp_path)
        assert bom.evidentiary_status == "mock"

    def test_ssp_shows_non_evidentiary_banner_r12(self, tmp_path):
        *_, ssp, _req = self._run(tmp_path)
        assert "NON-EVIDENTIARY" in ssp
        assert ssp.index("NON-EVIDENTIARY") < ssp.index("Verification Cross-Reference")
        assert "NON-EVIDENTIARY stamp:" in ssp  # cannot be omitted

    def test_every_required_control_met_and_machine_subset_cited(self, tmp_path):
        _ds, _order, _state, _report, bom, *_rest = self._run(tmp_path)
        rows = {r.control_id: r for r in bom.control_mapping}
        required = set(rows)
        # All 22 required controls are MET (status driven by the attestation).
        assert all(rows[c].status == "MET" for c in required)
        # The machine-checkable subset is cited to an evidence hash. (The
        # remaining controls are human-attested from documentary evidence and
        # carry no ce:contentHash by design — the thesis is scoped to the
        # machine-checkable subset.)
        cited = {c for c in required if rows[c].evidence_hashes}
        assert cited, "no required control was cited to an evidence hash"
        assert cited >= {"IA.L2-3.5.3", "AC.L2-3.1.1", "SC.L2-3.13.11", "SC.L2-3.13.16"}
        for c in cited:
            assert all(len(h) == 64 for h in rows[c].evidence_hashes)

    def test_ssp_vcrm_status_equals_attestation_outcomes_no_drift(self, tmp_path):
        ds, _order, _state, _report, _bom, _reg, _h, ssp, required = self._run(tmp_path)
        # VCRM status column == the attestation graph outcomes (no drift):
        # every required control is earl:passed in the graph AND MET in the VCRM.
        met_in_graph = auditmod.met_control_ids(ds)
        assert met_in_graph == set(required)
        for c in required:
            assert _vcrm_status(ssp, c) == "MET"
        # A non-required, unattested control is PLANNED (a gap) and NOT in the graph.
        assert "AC.L2-3.1.4" not in met_in_graph
        assert _vcrm_status(ssp, "AC.L2-3.1.4") == "PLANNED"

    def test_registry_resolves_contract_to_bom_to_artifacts(self, tmp_path):
        _ds, _order, _state, _report, bom, reg, bom_hash, _ssp, _req = self._run(tmp_path)
        assert reg.latest_bom("NV012") == bom_hash
        assert reg.bom_artifacts(bom_hash) == bom.artifact_hashes()
        assert bom.order_hash in reg.bom_artifacts(bom_hash)
        assert bommod.verify_bom(bom, reg) is True


# --------------------------------------------------------------------------- #
# Scenario 2 — Gate 1 error path (gap)
# --------------------------------------------------------------------------- #

class TestGate1GapRefusesOrder:
    def test_uncovered_control_refuses_order_and_factory_never_runs(self):
        ds, obl = compiler.load_pipeline_dataset()
        # Require an uncovered 5-point control (no tier1 module claims it).
        obl = dict(obl)
        obl["OBL-EXTRA-REMOTE-MFA"] = rl.Obligation(
            "OBL-EXTRA-REMOTE-MFA", rl.DATA, derives=frozenset({"AC.L2-3.1.12"}),
        )
        att = cop.attest_cop(ds, obl, auto=True, now=NOW)

        with pytest.raises(compiler.Gate1Failed) as exc:
            compiler.compile_order(ds, obl, att, now=NOW)

        report = exc.value.report
        assert not report.passed
        assert "AC.L2-3.1.12" in report.gap_controls()   # the gap names the control

        # The Order was NOT emitted → the Factory has nothing to run.
        order_g = graph_for(ds, "order")
        assert (CE["Order-NV012"], RDF.type, CE.Order) not in order_g


# --------------------------------------------------------------------------- #
# Scenario 3 — Gate 2 + R13 error path (contradiction)
# --------------------------------------------------------------------------- #

class TestContradictionMetOverFailedOracle:
    _CTRL = "IA.L2-3.5.3"

    def _run_to_contradiction(self):
        ds, order = _compile_order()
        state = _run_factory(ds, order, "contradiction")
        # The oracle for the MFA control FAILS in the contradiction fixture set.
        assert state.oracles.outcomes[self._CTRL] == "failed"
        # The official attests MET anyway, WITHOUT an override → contradiction.
        request_attestation(
            ds, self._CTRL, "Jane Official", auto_attest=True,
            adequacy="Compensating control asserted.", sufficiency="Deemed MET.",
            outcome=OUTCOME_PASSED,
            backing_oracle=CE["oracle-mfa-2sv"], oracle_outcome=OUTCOME_FAILED,
        )
        return ds, order, state

    def test_audit_flags_met_over_failed_oracle_and_ssp_surfaces_it(self):
        ds, _order, _state = self._run_to_contradiction()
        report = auditmod.audit(ds)

        # R13: the contradiction dimension flags the MET-over-failed-oracle.
        flagged = {c.control for c in report.contradictions}
        assert self._CTRL in flagged
        row = next(c for c in report.contradictions if c.control == self._CTRL)
        assert row.oracle_outcome == "failed"
        assert row.has_override is False

        # The report states "N MET-by-machine / M MET-by-human-only" — the human
        # MET call counts as human-only (the oracle did not pass).
        assert self._CTRL in report.proven.met_by_human_only
        assert self._CTRL not in report.proven.met_by_machine

        # SPRS reflects the human MET call (the control counts as MET).
        assert self._CTRL in auditmod.met_control_ids(ds)

        # The SSP surfaces the contradiction in its colophon.
        ssp = compile_ssp_from_run(ds, audit_report=report)
        assert "contradictions: 1." in ssp

    def test_override_clears_the_contradiction(self):
        ds, _order, _state = self._run_to_contradiction()
        assert len(auditmod.audit(ds).contradictions) == 1

        # The AO records an override justification → contradiction cleared.
        request_attestation(
            ds, self._CTRL, "Jane Official", auto_attest=True,
            adequacy="Compensating control asserted.", sufficiency="Deemed MET.",
            outcome=OUTCOME_PASSED,
            backing_oracle=CE["oracle-mfa-2sv"], oracle_outcome=OUTCOME_FAILED,
            override_justification="AO override: phishing-resistant MFA enforced "
                                   "via compensating IdP policy; ticket SEC-4471.",
        )
        report = auditmod.audit(ds)
        assert report.contradictions == []
        ssp = compile_ssp_from_run(ds, audit_report=report)
        assert "contradictions: 0." in ssp
