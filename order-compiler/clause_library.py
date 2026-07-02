"""Clause -> forced-obligation completeness check (U4, AUTHORING-TIME ONLY).

This module supports step B of the Order Compiler (COP extraction). When a
contract cites a DFARS/ITAR clause, that clause *forces* the presence of certain
obligations in the COP — e.g. citing DFARS 252.204-**7012** forces both a CUI
obligation and an 800-171 obligation. :func:`validate_cop_completeness` flags any
obligation a cited clause requires but the drafted COP omits, so the Compliance
Officer catches an under-specified COP before attesting it.

IMPORTANT — this is an **authoring-time** aid. It is NOT on the runtime
acceptance path: the Factory never calls it, and it can never cause an Order to
pass or fail at execution time. Its only job is to make the human-attested COP
more complete at draft time (a checklist, not a gate).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

# Single source of truth: cited clause -> the obligation tokens it forces into
# the COP. Tokens are the abstract obligation identifiers a COP must contain
# (matched by set membership, not by cmmc:Obligation IRI).
CLAUSE_TO_OBLIGATIONS: dict[str, frozenset] = {
    # DFARS 252.204-7012 — safeguarding CDI: forces CUI handling + NIST 800-171.
    "7012": frozenset({"CUI", "800-171"}),
    # DFARS 252.204-7021 — CMMC requirement: forces a CMMC-status obligation.
    "7021": frozenset({"CMMC-status"}),
    # ITAR topic (22 CFR 120-130): forces US-person, US residency, end-to-end boundary.
    "ITAR-topic": frozenset({"US-person", "residency", "e2e"}),
}


@dataclass(frozen=True)
class CompletenessReport:
    """Result of a COP completeness check.

    ``ok`` is True iff every cited clause's forced obligations are present in the
    COP. ``missing`` maps each deficient clause to the obligation tokens it forces
    that the COP omits. ``unknown_clauses`` lists cited clauses with no rule.
    """

    ok: bool
    missing: dict[str, frozenset] = field(default_factory=dict)
    unknown_clauses: frozenset = field(default_factory=frozenset)

    def __bool__(self) -> bool:
        return self.ok


def validate_cop_completeness(
    cited_clauses: Iterable[str],
    cop_obligations: Iterable[str],
) -> CompletenessReport:
    """Flag obligations a cited clause forces but the COP omits.

    Args:
        cited_clauses: clause identifiers cited by the contract (e.g. {"7012"}).
        cop_obligations: obligation tokens actually present in the drafted COP.

    Returns:
        CompletenessReport — ``ok`` False (and ``missing`` populated) when a
        cited clause forces an obligation the COP lacks; ``ok`` True otherwise.

    Authoring-time only — never called on the runtime acceptance path.
    """
    cited = set(cited_clauses)
    present = set(cop_obligations)

    missing: dict[str, frozenset] = {}
    unknown: set[str] = set()
    for clause in cited:
        required = CLAUSE_TO_OBLIGATIONS.get(clause)
        if required is None:
            unknown.add(clause)
            continue
        gap = required - present
        if gap:
            missing[clause] = frozenset(gap)

    return CompletenessReport(
        ok=not missing,
        missing=missing,
        unknown_clauses=frozenset(unknown),
    )
