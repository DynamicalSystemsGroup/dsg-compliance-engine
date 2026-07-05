"""Smoke tests for the marimo walkthrough's engine layer (`notebook/_engine.py`).

These assert the notebook is a faithful viewport onto the engine: the same three
scenarios the CLI runs produce the same terminal signals, and the run is
deterministic. UI is not tested here — only the UI-free adapter and that the
notebook file itself is a valid marimo app.
"""

from __future__ import annotations

import pytest

from notebooks import _engine


def test_all_covered_completes_with_full_score():
    r = _engine.run_pipeline("all-covered")

    assert r["refused"] is False
    assert r["order"].order_hash
    assert len(r["required_controls"]) == 22
    assert len(r["order"].required_controls) == 22
    # 6 tier-1 outcomes + 45 Track A criteria = 51 oracle outcomes.
    assert len(r["factory_state"].oracles.outcomes) == 6 + 45 == 51
    # 7 tier-1 evidence nodes + 13 Track A config exports = 20 evidence nodes.
    assert r["factory_state"].evidence.evidence_node_count == 7 + 13 == 20

    audit = r["audit"]
    assert audit.sprs.score == 110
    assert audit.sprs.status == "Final"
    assert audit.sprs.valid_submission is True
    assert len(audit.contradictions) == 0
    # SC.L2-3.13.1 (boundary/residency) is machine-proven via its data_region
    # criterion — it used to lack a criterion and return no config result.
    assert audit.proven.machine_count == 5
    assert audit.proven.human_count == 17

    assert r["bom"].evidentiary_status == "mock"
    assert "NON-EVIDENTIARY" in r["ssp"]


def test_gap_is_refused_at_gate_1_and_names_the_control():
    r = _engine.run_pipeline("gap")

    assert r["refused"] is True
    assert r["order"] is None
    assert r["gate1"].gap_controls() == [_engine.GAP_CONTROL]
    # nothing downstream ran
    assert "factory_state" not in r
    assert "bom" not in r


def test_contradiction_completes_but_flags_one_contradiction():
    r = _engine.run_pipeline("contradiction")

    assert r["refused"] is False
    audit = r["audit"]
    assert audit.sprs.score == 110
    assert len(audit.contradictions) == 1
    # SC.L2-3.13.1 now machine-resolved (data_region criterion).
    assert audit.proven.machine_count == 4
    assert audit.proven.human_count == 18


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
    from notebooks import compliance_walkthrough as nb

    assert isinstance(nb.app, marimo.App)
