"""U4 — clause_library authoring-time COP completeness check."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "order-compiler"))

import clause_library as cl  # noqa: E402


def test_7012_present_but_obligations_missing_is_flagged():
    report = cl.validate_cop_completeness(cited_clauses={"7012"}, cop_obligations=set())
    assert not report.ok
    assert report.missing["7012"] == {"CUI", "800-171"}


def test_7012_partially_missing_is_flagged():
    report = cl.validate_cop_completeness(
        cited_clauses={"7012"}, cop_obligations={"CUI"}
    )
    assert not report.ok
    assert report.missing["7012"] == {"800-171"}


def test_7012_obligations_present_passes():
    report = cl.validate_cop_completeness(
        cited_clauses={"7012"}, cop_obligations={"CUI", "800-171", "extra"}
    )
    assert report.ok
    assert report.missing == {}
    assert bool(report) is True


def test_multiple_clauses_all_satisfied():
    report = cl.validate_cop_completeness(
        cited_clauses={"7012", "7021", "ITAR-topic"},
        cop_obligations={"CUI", "800-171", "CMMC-status", "US-person", "residency", "e2e"},
    )
    assert report.ok


def test_itar_topic_missing_flagged():
    report = cl.validate_cop_completeness(
        cited_clauses={"ITAR-topic"}, cop_obligations={"US-person"}
    )
    assert not report.ok
    assert report.missing["ITAR-topic"] == {"residency", "e2e"}


def test_unknown_clause_recorded_not_crash():
    report = cl.validate_cop_completeness(
        cited_clauses={"9999"}, cop_obligations=set()
    )
    # unknown clause imposes nothing -> ok, but recorded for the author
    assert report.ok
    assert "9999" in report.unknown_clauses


def test_no_clauses_passes():
    report = cl.validate_cop_completeness(cited_clauses=set(), cop_obligations=set())
    assert report.ok
