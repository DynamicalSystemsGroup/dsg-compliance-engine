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
    assert len(r["factory_state"].oracles.outcomes) == 66
    assert r["factory_state"].evidence.evidence_node_count == 25

    audit = r["audit"]
    assert audit.sprs.score == 110
    assert audit.sprs.status == "Final"
    assert audit.sprs.valid_submission is True
    assert len(audit.contradictions) == 0
    # Every required control now has a real (mock) oracle result: 20 machine-proven
    # + 2 CSP-inherited = 22 MET. Nothing is attested MET without a concrete result.
    assert audit.proven.machine_count == 20
    assert audit.proven.human_count == 2

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


def test_contradiction_drops_score_and_invalidates_submission():
    r = _engine.run_pipeline("contradiction")

    assert r["refused"] is False
    audit = r["audit"]
    # The contradiction has teeth: IA.L2-3.5.3 (weight 5) is attested MET over a
    # FAILED oracle with no override, so it does NOT count as MET — its weight is
    # deducted and the submission is invalid. The number can no longer hide it.
    assert len(audit.contradictions) == 1
    assert audit.sprs.score == 105
    assert audit.sprs.status == "Conditional"
    assert audit.sprs.valid_submission is False
    assert "IA.L2-3.5.3" in audit.sprs.unmet
    # IA.L2-3.5.3 flips to a failed oracle here, so 19 machine-proven + 3 human.
    assert audit.proven.machine_count == 19
    assert audit.proven.human_count == 3


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
