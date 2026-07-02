"""Deterministic obligation -> required-control-set mappings (U4).

This is the *regulation-cited* rule library used by step C of the Order Compiler
pipeline (obligation -> control). It is deterministic and versioned: every rule
is a single-source-of-truth entry in ``RULES`` (the dict-of-callables pattern
from ``ADCS-lifecycle-demo/analysis/oracle.py``), and the CMMC-L2 expansion is
read live from ``ontology/cmmc-edit.ttl`` — the 110 control IDs are never
hardcoded here.

The environment/deliverable split (R11) is made *safe*: a ``deliverable``
obligation that carries a CUI/ITAR :pyattr:`cmmc:dataMarker` must NOT silently
resolve to an empty set (that would drop an environment control on the floor).
Such an obligation raises :class:`SpilloverReviewRequired` so a human resolves
the env-spillover before an Order is compiled.

Return contract (consumed by U5):
    resolve(obligation) -> ControlSet
        * ControlSet IS a frozenset[str] of NIST 800-171 control IDs.
        * ControlSet.markers is a frozenset[str] of non-control policy markers
          (e.g. US-PERSON, RESIDENCY, E2E-CUI-BOUNDARY, TIER1-SCOPE).
        * Empty resolution (OBL-IL5 / IL5-OVERLAY / plain deliverable) returns an
          empty ControlSet — it compares == set() and is falsy — NOT an error.
    Raises SpilloverReviewRequired  — CUI/ITAR-marked deliverable.
    Raises UnknownControlError      — obligation cites a control-shaped ID absent
                                      from the catalog.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from rdflib import Graph, RDF

from ontology.prefixes import CMMC, CE  # noqa: F401  (CE re-exported for U5)

# Repo root = this file's grandparent (order-compiler/ -> repo root).
_REPO_ROOT = Path(__file__).resolve().parent.parent
_CATALOG_TTL = _REPO_ROOT / "ontology" / "cmmc-edit.ttl"

# A NIST 800-171 Rev.2 CMMC control ID, e.g. "AC.L2-3.1.1" / "SC.L2-3.13.16".
_CONTROL_ID_RE = re.compile(r"^[A-Z]{2}\.L2-3\.\d+\.\d+$")

# Obligation-type vocabulary (mirrors obligations.ttl cmmc:obligationType).
FRAMEWORK = "framework"
HOSTING = "hosting"
DATA = "data"
PERSONNEL = "personnel"
ENVIRONMENT = "environment"
DELIVERABLE = "deliverable"
OBLIGATION_TYPES = frozenset(
    {FRAMEWORK, HOSTING, DATA, PERSONNEL, ENVIRONMENT, DELIVERABLE}
)

# Data-sensitivity markers (cmmc:dataMarker) that make a deliverable dangerous.
CUI = "CUI"
ITAR = "ITAR"
SPILLOVER_MARKERS = frozenset({CUI, ITAR})


class UnknownControlError(ValueError):
    """An obligation cites a control-shaped ID that is not in the catalog."""


class SpilloverReviewRequired(Exception):
    """A CUI/ITAR-marked deliverable would drop to {} — human review required.

    Carries the offending obligation so U5 can surface it in the COP-attestation
    prompt ("this deliverable touches CUI/ITAR on DSG infra; confirm the env
    controls it imposes") instead of silently omitting environment controls.
    """

    def __init__(self, obligation: "Obligation"):
        self.obligation = obligation
        super().__init__(
            f"Deliverable obligation {obligation.name!r} carries dataMarker "
            f"{obligation.data_marker!r}; it may spill environment controls onto "
            f"DSG infrastructure and must not resolve to an empty set silently. "
            f"Route to env-spillover review (R11)."
        )


class ControlSet(frozenset):
    """An immutable set of control IDs plus non-control policy ``markers``.

    Subclasses ``frozenset`` so ``len``, ``in``, ``==`` and set algebra work as
    a plain control-ID set (``ControlSet() == set()`` is True), while preserving
    the policy markers a rule attaches (US-PERSON, RESIDENCY, TIER1-SCOPE, ...).
    """

    markers: frozenset

    def __new__(cls, controls: Iterable[str] = (), markers: Iterable[str] = ()):
        self = super().__new__(cls, controls)
        self.markers = frozenset(markers)
        return self

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        base = sorted(self)
        if self.markers:
            return f"ControlSet({base!r}, markers={sorted(self.markers)!r})"
        return f"ControlSet({base!r})"


@dataclass(frozen=True)
class Obligation:
    """A COP obligation, as consumed by the rule library.

    ``derives`` holds whatever ``cmmc:derivesControls`` names: real control IDs,
    an expansion token (``ALL-110-NIST-800-171`` / ``IL5-OVERLAY`` /
    ``TIER1-SCOPE``), and/or policy markers.
    """

    name: str
    obligation_type: str
    data_marker: str | None = None
    source_ref: str | None = None
    derives: frozenset = field(default_factory=frozenset)

    def __post_init__(self):
        object.__setattr__(self, "derives", frozenset(self.derives or ()))


class _Catalog:
    """Lazy, cached view of the control IDs declared in cmmc-edit.ttl."""

    _cache: dict[Path, frozenset] = {}

    def __init__(self, path: Path = _CATALOG_TTL):
        self.path = path

    def all_controls(self) -> frozenset:
        if self.path not in _Catalog._cache:
            g = Graph()
            g.parse(self.path, format="turtle")
            ids = {
                str(g.value(node, CMMC.controlId))
                for node in g.subjects(RDF.type, CMMC.Control)
            }
            ids.discard("None")
            _Catalog._cache[self.path] = frozenset(ids)
        return _Catalog._cache[self.path]


def _is_control_shaped(token: str) -> bool:
    return bool(_CONTROL_ID_RE.match(token))


def _validate_control_ids(tokens: Iterable[str], catalog: _Catalog) -> None:
    """Raise if any control-shaped token is absent from the catalog."""
    known = catalog.all_controls()
    for token in tokens:
        if _is_control_shaped(token) and token not in known:
            raise UnknownControlError(
                f"Obligation cites control ID {token!r}, which is not one of the "
                f"{len(known)} controls in {catalog.path.name}."
            )


# ---------------------------------------------------------------------------
# Single source of truth: obligation-name -> resolver.
# Each resolver takes the catalog view and returns a ControlSet. Keep every
# regulation-cited mapping here so the rule set is auditable in one place.
# ---------------------------------------------------------------------------
RULES = {
    # Q36/Q42: CMMC L2 == the full 800-171 Rev.2 baseline. Read live, never hardcoded.
    "OBL-CMMC-L2": lambda cat: ControlSet(cat.all_controls()),
    # ITAR: FIPS-validated crypto control + US-person / residency / e2e markers.
    "OBL-ITAR": lambda cat: ControlSet(
        {"SC.L2-3.13.11"},
        markers={"US-PERSON", "RESIDENCY", "E2E-CUI-BOUNDARY"},
    ),
    # CUI data boundary: access flow-control + transmission/at-rest confidentiality.
    "OBL-CUI-BOUNDARY": lambda cat: ControlSet(
        {"AC.L2-3.1.1", "AC.L2-3.1.3", "SC.L2-3.13.8", "SC.L2-3.13.16"}
    ),
    # Phase I environment scope: a marker, not a direct control.
    "OBL-PHASE1-ENV": lambda cat: ControlSet((), markers={"TIER1-SCOPE"}),
    # IL5 hosting overlay is deferred to Tier 2 -> empty in Phase I (NOT an error).
    "OBL-IL5": lambda cat: ControlSet(),
    "IL5-OVERLAY": lambda cat: ControlSet(),
}

# Expansion tokens some obligations put in cmmc:derivesControls, mapped to the
# rule that expands them (so a ttl-loaded obligation resolves the same way).
_TOKEN_TO_RULE = {
    "ALL-110-NIST-800-171": "OBL-CMMC-L2",
    "IL5-OVERLAY": "IL5-OVERLAY",
    "TIER1-SCOPE": "OBL-PHASE1-ENV",
}


def resolve(obligation: Obligation, *, catalog_path: Path | None = None) -> ControlSet:
    """Resolve an obligation to its required control set.

    See module docstring for the full contract. Deterministic; safe on the
    environment/deliverable split.
    """
    catalog = _Catalog(catalog_path) if catalog_path else _Catalog()

    if obligation.obligation_type not in OBLIGATION_TYPES:
        raise ValueError(
            f"Unknown obligationType {obligation.obligation_type!r}; "
            f"expected one of {sorted(OBLIGATION_TYPES)}."
        )

    # -- R11 spillover guard: deliverables are normally not provisioned, but a
    #    CUI/ITAR-marked deliverable must never drop silently to {}.
    if obligation.obligation_type == DELIVERABLE:
        if obligation.data_marker in SPILLOVER_MARKERS:
            raise SpilloverReviewRequired(obligation)
        # plain deliverable: validate any explicit IDs, then not provisioned.
        _validate_control_ids(obligation.derives, catalog)
        return ControlSet()

    # -- Validate any explicitly-cited control IDs before dispatch.
    _validate_control_ids(obligation.derives, catalog)

    # -- Named rule (the regulation-cited mappings) takes priority.
    if obligation.name in RULES:
        return RULES[obligation.name](catalog)

    # -- Otherwise expand tokens / fall back to explicit derives.
    for token in obligation.derives:
        if token in _TOKEN_TO_RULE:
            return RULES[_TOKEN_TO_RULE[token]](catalog)

    controls = {t for t in obligation.derives if _is_control_shaped(t)}
    markers = {t for t in obligation.derives if not _is_control_shaped(t)}
    return ControlSet(controls, markers=markers)


# ---------------------------------------------------------------------------
# Loader — read the finalized COP obligations from obligations.ttl so U5 can
# feed resolve() without reconstructing Obligation objects by hand.
# ---------------------------------------------------------------------------
_OBLIGATIONS_TTL = _REPO_ROOT / "order-compiler" / "obligations.ttl"


def load_obligations(ttl_path: Path | None = None) -> dict[str, Obligation]:
    """Load ``cmmc:Obligation`` individuals into ``{name: Obligation}``."""
    path = ttl_path or _OBLIGATIONS_TTL
    g = Graph()
    g.parse(path, format="turtle")
    out: dict[str, Obligation] = {}
    for node in g.subjects(RDF.type, CMMC.Obligation):
        name = str(node).rsplit("/", 1)[-1].rsplit("#", 1)[-1]
        otype = g.value(node, CMMC.obligationType)
        marker = g.value(node, CMMC.dataMarker)
        source = g.value(node, CMMC.sourceRef)
        derives = set()
        for obj in g.objects(node, CMMC.derivesControls):
            # object may be a cmmc:Control IRI or a literal expansion token
            if str(obj).startswith(str(CMMC)):
                derives.add(str(obj).rsplit("#", 1)[-1].rsplit("/", 1)[-1])
            else:
                derives.add(str(obj))
        out[name] = Obligation(
            name=name,
            obligation_type=str(otype) if otype is not None else "",
            data_marker=str(marker) if marker is not None else None,
            source_ref=str(source) if source is not None else None,
            derives=frozenset(derives),
        )
    return out
