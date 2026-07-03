"""Smoke tests for the marimo walkthrough's engine layer (`notebook/_engine.py`).

These assert the notebook is a faithful viewport onto the engine: the same three
scenarios the CLI runs produce the same terminal signals, and the run is
deterministic. UI is not tested here — only the UI-free adapter and that the
notebook file itself is a valid marimo app.
"""

from __future__ import annotations

import pytest

from notebook import _engine


def test_all_covered_completes_with_full_score():
    r = _engine.run_pipeline("all-covered")

    assert r["refused"] is False
    assert r["order"].order_hash
    assert len(r["required_controls"]) == 22
    assert len(r["order"].required_controls) == 22
    # 6 tier-1 oracle outcomes + 8 VPC_Segmentation criteria (SC.13.3/4/5/6/7/8/9/15).
    assert len(r["factory_state"].oracles.outcomes) == 6 + 8 == 14
    # 7 tier-1 evidence nodes + 1 VPC_Segmentation config export fixture.
    assert r["factory_state"].evidence.evidence_node_count == 7 + 1 == 8

    audit = r["audit"]
    assert audit.sprs.score == 110
    assert audit.sprs.status == "Final"
    assert audit.sprs.valid_submission is True
    assert len(audit.contradictions) == 0
    assert audit.proven.machine_count == 4
    assert audit.proven.human_count == 18

    assert r["bom"].evidentiary_status == "mock"
    assert "NON-EVIDENTIARY" in r["ssp"]


def test_gap_is_refused_at_gate_1_and_names_the_control():
    r = _engine.run_pipeline("gap")

    assert r["refused"] is True
    assert r["order"] is None
    assert r["gate1"].gap_controls() == ["AC.L2-3.1.12"]
    # nothing downstream ran
    assert "factory_state" not in r
    assert "bom" not in r


def test_contradiction_completes_but_flags_one_contradiction():
    r = _engine.run_pipeline("contradiction")

    assert r["refused"] is False
    audit = r["audit"]
    assert audit.sprs.score == 110
    assert len(audit.contradictions) == 1
    assert audit.proven.machine_count == 3
    assert audit.proven.human_count == 19


def test_run_is_deterministic():
    a = _engine.run_pipeline("all-covered")
    b = _engine.run_pipeline("all-covered")
    assert a["order"].order_hash == b["order"].order_hash
    assert a["bom"].bom_hash == b["bom"].bom_hash


def test_unknown_scenario_raises_value_error():
    with pytest.raises(ValueError):
        _engine.run_pipeline("does-not-exist")


def test_named_graphs_are_populated_after_a_run():
    r = _engine.run_pipeline("all-covered")
    counts = {row["layer"]: row["triples"] for row in _engine.named_graph_counts(r["ds"])}
    for layer in ("ontology", "structural", "order", "evidence", "attestations", "audit"):
        assert counts[layer] > 0, f"expected triples in <ce:{layer}>"


def test_notebook_file_is_a_valid_marimo_app():
    # Only meaningful when the `notebook` dependency group is installed.
    marimo = pytest.importorskip("marimo")
    from notebook import compliance_walkthrough as nb

    assert isinstance(nb.app, marimo.App)
