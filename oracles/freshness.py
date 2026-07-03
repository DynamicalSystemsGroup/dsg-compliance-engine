"""Freshness policy for attested references.

A reference (ce:Reference) carries a ce:freshnessDays and a ce:lastVerified
timestamp. This module answers one question: given those two, is the reference
still fresh at a given `now`?

Semantics:
  * freshness_days > 0  → reference goes stale `freshness_days` days after
                          last_verified. The attested-reference oracle FAILs
                          the control (needsAction) once stale.
  * freshness_days == 0 → EVENT-based reference: never goes stale on time
                          alone. Used for records that only need to exist per
                          event (offboarding tickets, sanitization records,
                          background-check attestations). Their staleness is
                          judged by other means (audit of event coverage).
  * freshness_days < 0  → invalid; raises.

Default windows are named policy constants so callers don't sprinkle magic
numbers through Turtle: ANNUAL (365d), QUARTERLY (90d), MONTHLY (30d),
EVENT_BASED (0). Turtle authors pick a policy constant by name in the
generator/fixture; the number is centralized here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Final

# Canonical policy windows. Turtle authors pick by name in the generator; the
# integer value lives here so a policy change updates one file, not sixteen
# fixtures.
ANNUAL: Final[int] = 365
SEMI_ANNUAL: Final[int] = 180
QUARTERLY: Final[int] = 90
MONTHLY: Final[int] = 30
EVENT_BASED: Final[int] = 0

# Mapping from human name → days. Exported so fixture and Turtle authors can
# refer to policies by name (e.g. "annual") rather than hardcoding integers.
POLICY_DAYS: Final[dict[str, int]] = {
    "annual": ANNUAL,
    "semi-annual": SEMI_ANNUAL,
    "quarterly": QUARTERLY,
    "monthly": MONTHLY,
    "event-based": EVENT_BASED,
}


@dataclass(frozen=True)
class FreshnessVerdict:
    """The result of checking a reference's freshness at a point in time."""
    is_fresh: bool
    reason: str  # "fresh", "stale:172d>90d", "event-based", "invalid:..."
    age_days: int | None  # None for event-based (age is meaningless there)


def check_freshness(
    last_verified: datetime,
    freshness_days: int,
    *,
    now: datetime | None = None,
) -> FreshnessVerdict:
    """Return the freshness verdict for one reference.

    Args:
        last_verified: When the reference was last confirmed authoritative.
                       MUST be timezone-aware. Naive datetimes raise.
        freshness_days: Non-negative int. 0 means event-based (never stale on
                       time alone).
        now:           Override "now" (used by tests for determinism). If None,
                       uses datetime.now(timezone.utc).

    Raises:
        ValueError:    If freshness_days < 0 or last_verified is naive.
    """
    if freshness_days < 0:
        raise ValueError(
            f"freshness_days must be non-negative, got {freshness_days}"
        )
    if last_verified.tzinfo is None:
        raise ValueError(
            "last_verified must be timezone-aware; got a naive datetime"
        )

    if freshness_days == 0:
        return FreshnessVerdict(is_fresh=True, reason="event-based", age_days=None)

    now = now or datetime.now(timezone.utc)
    age = now - last_verified
    age_days = age.days
    if age <= timedelta(days=freshness_days):
        return FreshnessVerdict(
            is_fresh=True, reason="fresh", age_days=age_days,
        )
    return FreshnessVerdict(
        is_fresh=False,
        reason=f"stale:{age_days}d>{freshness_days}d",
        age_days=age_days,
    )


def resolve_policy(name_or_days: str | int) -> int:
    """Turn a policy name ("annual") or an int (365) into the days integer.

    Used by generators/fixtures so Turtle can carry either the string policy
    name or the raw integer.
    """
    if isinstance(name_or_days, int):
        if name_or_days < 0:
            raise ValueError(f"days must be non-negative, got {name_or_days}")
        return name_or_days
    key = name_or_days.strip().lower()
    if key not in POLICY_DAYS:
        raise ValueError(
            f"unknown freshness policy {name_or_days!r}; "
            f"expected int or one of {sorted(POLICY_DAYS)}"
        )
    return POLICY_DAYS[key]
