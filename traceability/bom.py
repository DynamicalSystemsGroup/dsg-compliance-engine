"""BOM assembly + hash-reference into the registry (U11b).

"Compliance is a provisioning artifact." The BOM (Bill of Materials) is the
byproduct of a Factory run that IS the compliance proof — and the SSP's source
(U12). It is assembled **wholesale** from a finalized `PipelineState` (U8) plus
the Gate-2 attestations graph (U9), content-addressed (SHA-256), and stored
**write-once** in the registry (U11a) with the two-level index.

Design invariants:
  * status is driven by the **attestation** outcome — a control is MET only when
    a human attested it passed. The machine oracle outcome is supporting context,
    never determinative (a passing oracle with NO attestation is NOT MET).
  * `evidentiary_status` propagates the WEAKEST input status (R12): if any input
    evidence is mock / mock-plan / auto, the whole BOM is `"mock"`.
  * the BOM hash is SHA-256 over the CANONICAL serialization (sorted keys, no
    wall-clock — every time is pulled from the state/graph, never datetime.now).
  * `hash_reference()` (registry) is the seam where Sigstore slots in later — no
    "sign" naming here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rdflib import Dataset, Graph, Literal
from rdflib.namespace import RDF

from ontology.prefixes import CE, CMMC, PROV
from evidence.hashing import _serialize_for_hash
from pipeline.registry import content_hash
from traceability.queries import (
    ATTESTATION_DETAIL,
    EVIDENCE_FOR_CONTROL,
    query_to_dicts,
)

if TYPE_CHECKING:  # pragma: no cover
    from pipeline.registry import Registry
    from pipeline.state import PipelineState

BOM_SCHEMA = "ce-bom/1"

# EARL outcome short-name → CMMC determination label (mirrors
# traceability.attestation.STATUS_LABEL, keyed by short name here).
_SHORT_STATUS = {
    "passed": "MET",
    "failed": "NOT MET",
    "inapplicable": "N/A",
    "untested": "PLANNED",
    "cantTell": "CANT TELL",
}
# A control with no attestation is NOT MET (MET requires a human attestation).
_UNATTESTED_STATUS = "NOT MET"

# Evidentiary statuses that make the whole BOM non-evidentiary (R12).
_WEAK_STATUSES = {"mock", "mock-plan", "auto", "automatic", "semiAuto"}


# ---------------------------------------------------------------------------
# Row / record shapes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ControlMappingRow:
    """One required control → what provisioned it, the evidence, and its status."""
    control_id: str
    resource_ids: tuple[str, ...]
    evidence_hashes: tuple[str, ...]
    oracle_outcome: str | None
    attestation_outcome: str | None      # earl short name, or None
    status: str                          # MET | NOT MET | N/A | PLANNED | CANT TELL

    def to_dict(self) -> dict:
        return {
            "control_id": self.control_id,
            "resource_ids": sorted(self.resource_ids),
            "evidence_hashes": sorted(self.evidence_hashes),
            "oracle_outcome": self.oracle_outcome,
            "attestation_outcome": self.attestation_outcome,
            "status": self.status,
        }


@dataclass(frozen=True)
class AttestationRecord:
    """A Gate-2 attestation as it appears in the BOM."""
    control_id: str
    official: str
    role: str
    outcome: str                         # earl short name
    override_justification: str | None = None

    def to_dict(self) -> dict:
        return {
            "control_id": self.control_id,
            "official": self.official,
            "role": self.role,
            "outcome": self.outcome,
            "override_justification": self.override_justification,
        }


@dataclass(frozen=True)
class BOM:
    """The compliance Bill of Materials — content-addressed provisioning proof."""
    contract_id: str
    order_hash: str
    tier: str
    impact_level: str
    standard: str
    state_hash: str | None
    plan_resource_ids: tuple[str, ...]
    evidence_hashes: tuple[str, ...]
    module_hashes: dict[str, str]
    oracle_outcomes: dict[str, str]
    policy_passed: bool
    policy_findings: tuple[str, ...]
    control_mapping: tuple[ControlMappingRow, ...]
    attestations: tuple[AttestationRecord, ...]
    evidentiary_status: str
    bom_hash: str = ""                   # filled by build_bom

    # -- canonical serialization (deterministic; excludes bom_hash) ----------
    def to_canonical_dict(self) -> dict:
        return {
            "schema": BOM_SCHEMA,
            "contract_id": self.contract_id,
            "order_hash": self.order_hash,
            "tier": self.tier,
            "impact_level": self.impact_level,
            "standard": self.standard,
            "state_hash": self.state_hash,
            "plan_resource_ids": sorted(self.plan_resource_ids),
            "evidence_hashes": sorted(self.evidence_hashes),
            "module_hashes": dict(sorted(self.module_hashes.items())),
            "oracle_outcomes": dict(sorted(self.oracle_outcomes.items())),
            "policy": {
                "passed": self.policy_passed,
                "findings": sorted(self.policy_findings),
            },
            "control_mapping": [
                r.to_dict() for r in sorted(self.control_mapping,
                                            key=lambda x: x.control_id)
            ],
            "attestations": [
                a.to_dict() for a in sorted(self.attestations,
                                            key=lambda x: (x.control_id, x.official))
            ],
            "evidentiary_status": self.evidentiary_status,
        }

    def to_canonical_json(self) -> str:
        return _serialize_for_hash(self.to_canonical_dict())

    def canonical_bytes(self) -> bytes:
        return self.to_canonical_json().encode("utf-8")

    def compute_hash(self) -> str:
        return content_hash(self.canonical_bytes())

    # -- artifact references -------------------------------------------------
    def artifact_hashes(self) -> list[str]:
        """Every artifact hash this BOM references (sorted, deduped)."""
        hashes: set[str] = set()
        if self.order_hash:
            hashes.add(self.order_hash)
        if self.state_hash:
            hashes.add(self.state_hash)
        hashes.update(self.evidence_hashes)
        hashes.update(self.module_hashes.values())
        for row in self.control_mapping:
            hashes.update(row.evidence_hashes)
        return sorted(hashes)

    def hash_reference(self, registry: "Registry") -> str:
        """`registry://<bom_hash>` — the (unsigned) content reference seam."""
        return registry.hash_reference(self.bom_hash)

    # -- RDF view (for graph consumers; U12 may also read the dict) -----------
    def to_rdf(self, graph: Graph | None = None) -> Graph:
        g = graph if graph is not None else Graph()
        bom = CE[f"BOM/{self.bom_hash}"]
        g.add((bom, RDF.type, CE.BOM))
        g.add((bom, RDF.type, PROV.Entity))
        g.add((bom, CE.forContract, Literal(self.contract_id)))
        g.add((bom, CE.derivedFromOrder, Literal(self.order_hash)))
        if self.state_hash:
            g.add((bom, CE.stateHash, Literal(self.state_hash)))
        g.add((bom, CE.bomHash, Literal(self.bom_hash)))
        g.add((bom, CE.evidentiaryStatus, Literal(self.evidentiary_status)))
        for h in self.artifact_hashes():
            g.add((bom, CE.referencesArtifact, Literal(h)))
        for row in self.control_mapping:
            node = CE[f"BOM/{self.bom_hash}/mapping/{row.control_id}"]
            g.add((bom, CE.hasControlMapping, node))
            g.add((node, CE.control, CMMC[row.control_id]))
            g.add((node, CE.bomStatus, Literal(row.status)))
            for rid in row.resource_ids:
                g.add((node, CE.resource, CE[rid]))
            for eh in row.evidence_hashes:
                g.add((node, CE.evidenceHash, Literal(eh)))
        return g


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def _attestation_outcomes(ds: Dataset) -> dict[str, dict]:
    """{control_id: {outcome, official, override}} from <ce:attestations>."""
    out: dict[str, dict] = {}
    for row in query_to_dicts(ds, ATTESTATION_DETAIL):
        cid = row.get("controlId")
        if not cid:
            continue
        out[cid] = {
            "outcome": row.get("outcomeShort"),
            "official": row.get("official") or "",
            "override": row.get("override"),
        }
    return out


def _evidence_hashes_for(ds: Dataset, control_id: str) -> list[str]:
    rows = query_to_dicts(ds, EVIDENCE_FOR_CONTROL % control_id)
    return sorted({r["hash"] for r in rows if r.get("hash")})


def _evidentiary_status(ds: Dataset) -> str:
    """Propagate the WEAKEST input status (R12).

    `"mock"` if ANY evidence node carries a weak status (mock/mock-plan/auto),
    OR if there is no evidence at all (conservative). `"real"` only when every
    evidence node is real.
    """
    statuses = {str(o) for _s, _p, o in _iter_triples(ds, (None, CE.evidentiaryStatus, None))}
    if not statuses or any(s in _WEAK_STATUSES for s in statuses):
        return "mock"
    return "real"


def _iter_triples(ds, pattern):
    if isinstance(ds, Dataset):
        for s, p, o, _g in ds.quads(pattern):
            yield s, p, o
    else:
        yield from ds.triples(pattern)


def build_bom(
    state: "PipelineState",
    ds: Dataset,
    contract_id: str = "NV012",
) -> BOM:
    """Assemble the BOM wholesale from a finalized PipelineState + attestations."""
    lo = state.load_order
    if lo is None:
        raise ValueError("cannot build a BOM: PipelineState has no LoadOrder result")

    required = list(lo.required_controls)
    plan_resources = state.plan.plan_result.resources if state.plan else ()
    oracle_outcomes = dict(state.oracles.outcomes) if state.oracles else {}
    module_hashes = dict(state.fetch.module_hashes) if state.fetch else {}
    state_hash = state.apply.state_hash if state.apply else None
    evidence_hashes = tuple(state.evidence.evidence_hashes) if state.evidence else ()
    policy_passed = state.policy_check.passed if state.policy_check else False
    policy_findings = tuple(
        f.reason for f in state.policy_check.findings
    ) if state.policy_check else ()

    attn = _attestation_outcomes(ds)

    # control_mapping: one row per required control.
    rows: list[ControlMappingRow] = []
    for control_id in sorted(required):
        resource_ids = tuple(sorted(
            r.resource_id for r in plan_resources if control_id in r.controls
        ))
        ev_hashes = tuple(_evidence_hashes_for(ds, control_id))
        att = attn.get(control_id)
        att_outcome = att["outcome"] if att else None
        status = _SHORT_STATUS.get(att_outcome, _UNATTESTED_STATUS) if att_outcome \
            else _UNATTESTED_STATUS
        rows.append(ControlMappingRow(
            control_id=control_id,
            resource_ids=resource_ids,
            evidence_hashes=ev_hashes,
            oracle_outcome=oracle_outcomes.get(control_id),
            attestation_outcome=att_outcome,
            status=status,
        ))

    # attestations[]
    records: list[AttestationRecord] = []
    for cid, info in sorted(attn.items()):
        records.append(AttestationRecord(
            control_id=cid,
            official=info["official"],
            role="Affirming Official",
            outcome=info["outcome"] or "",
            override_justification=info["override"],
        ))

    bom = BOM(
        contract_id=contract_id,
        order_hash=lo.order_hash,
        tier=lo.tier,
        impact_level=lo.impact_level,
        standard=lo.standard,
        state_hash=state_hash,
        plan_resource_ids=tuple(state.plan.resource_ids) if state.plan else (),
        evidence_hashes=evidence_hashes,
        module_hashes=module_hashes,
        oracle_outcomes=oracle_outcomes,
        policy_passed=policy_passed,
        policy_findings=policy_findings,
        control_mapping=tuple(rows),
        attestations=tuple(records),
        evidentiary_status=_evidentiary_status(ds),
    )
    # Content-address the canonical serialization (bom_hash excluded from it).
    return _with_hash(bom)


def _with_hash(bom: BOM) -> BOM:
    from dataclasses import replace
    return replace(bom, bom_hash=bom.compute_hash())


# ---------------------------------------------------------------------------
# Storage (write-once, two-level index)
# ---------------------------------------------------------------------------

def store_bom(
    bom: BOM,
    registry: "Registry",
    contract_id: str,
    *,
    artifacts: dict[str, bytes] | None = None,
) -> str:
    """Store the BOM + wire the two-level index; return the bom_hash.

    Puts the BOM's canonical bytes (write-once), optionally puts any provided
    artifact bytes (whose SHA-256 must equal the referenced hash), records
    `set_bom_artifacts` (level 2) and `set_latest_bom` (level 1).
    """
    stored = registry.put(bom.canonical_bytes(), kind="bom")
    if stored != bom.bom_hash:
        raise ValueError(
            f"stored BOM hash {stored} != computed {bom.bom_hash} (non-canonical bytes)"
        )
    if artifacts:
        for ahash, abytes in artifacts.items():
            put_hash = registry.put(abytes, kind="artifact")
            if put_hash != ahash:
                raise ValueError(
                    f"artifact bytes hash to {put_hash}, not the referenced {ahash}"
                )
    registry.set_bom_artifacts(bom.bom_hash, bom.artifact_hashes())
    registry.set_latest_bom(contract_id, bom.bom_hash)
    return bom.bom_hash


def verify_bom(bom: BOM, registry: "Registry") -> bool:
    """Re-check the stored BOM + every stored referenced artifact (tamper check).

    Returns False if the BOM object is missing/tampered, or any referenced
    artifact that IS stored no longer hashes to its key.
    """
    if not registry.verify(bom.bom_hash):
        return False
    for ahash in bom.artifact_hashes():
        if registry.has(ahash) and not registry.verify(ahash):
            return False
    return True
