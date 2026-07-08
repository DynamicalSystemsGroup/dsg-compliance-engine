"""Build attested-reference oracle inputs from the RDF graph.

Bridges the structural model (modules that carry ``ce:reference`` / ``ce:attestationRole``
/ ``cmmc:verificationMethod ce:oracle-attested-reference``) to the ``ReferenceView`` the
attested-reference oracle consumes. One ``AttestedControl`` per control claimed by an
attested-reference module, carrying the reference's uri / freshness / lastVerified /
custodian so the runner can resolve + hash the document and run the oracle.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from compliance_engine.oracles.attested_reference import ReferenceView

_ATTESTED_METHOD_SUFFIX = "oracle-attested-reference"


@dataclass(frozen=True)
class AttestedControl:
    """One Track B control and the reference/role behind it."""
    control_id: str
    reference_id: str
    uri: str
    required_role: str
    custodian: str
    source_system: str
    view: ReferenceView | None       # None ⇒ no ce:Reference registered (branch 1)


def _localname(node) -> str:
    return str(node).rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def _parse_dt(value) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _int(value, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def load_attested_controls(ds) -> dict[str, AttestedControl]:
    """Map every control claimed by an ``oracle-attested-reference`` module to its
    ``AttestedControl``. Reads from the union graph, so it works whether the structural
    triples live in ``<ce:structural>`` or are queried across the whole dataset."""
    from compliance_engine.ontology.prefixes import CE, CMMC

    out: dict[str, AttestedControl] = {}
    for module, _p, vm in ds.triples((None, CMMC.verificationMethod, None)):
        if not str(vm).endswith(_ATTESTED_METHOD_SUFFIX):
            continue
        ref = ds.value(module, CE.reference)
        role = ds.value(module, CE.attestationRole)
        required_role = _localname(role) if role is not None else ""
        reference_id = _localname(ref) if ref is not None else ""

        uri = ds.value(ref, CE.uri) if ref is not None else None
        custodian = ds.value(ref, CE.custodian) if ref is not None else None
        source = ds.value(ref, CE.sourceSystem) if ref is not None else None
        version = ds.value(ref, CE.version) if ref is not None else None
        signature = ds.value(ref, CE.signature) if ref is not None else None
        uri_s = str(uri) if uri is not None else ""
        custodian_s = str(custodian) if custodian is not None else ""
        source_s = _localname(source) if source is not None else ""

        view: ReferenceView | None = None
        if ref is not None:
            view = ReferenceView(
                id=reference_id,
                uri=uri_s,
                freshness_days=_int(ds.value(ref, CE.freshnessDays), 365),
                last_verified=_parse_dt(ds.value(ref, CE.lastVerified)),
                source_system=source_s,
                custodian=custodian_s,
                version=str(version) if version is not None else None,
                signature=str(signature) if signature is not None else None,
            )

        for _s, _pp, ctrl in ds.triples((module, CMMC.controlsSatisfied, None)):
            cid = _localname(ctrl)
            # First module claiming a control wins; controls map 1:1 to a policy module.
            out.setdefault(cid, AttestedControl(
                control_id=cid,
                reference_id=reference_id,
                uri=uri_s,
                required_role=required_role,
                custodian=custodian_s,
                source_system=source_s,
                view=view,
            ))
    return out
