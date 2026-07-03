"""Line-delimited JSON store for AO attestations.

Each record is one signed statement by an Affirming Official (or another
role-appropriate signer) over one or more ce:Reference IDs, asserting that
the referenced authoritative source satisfies a specific set of controls at
a specific point in time. Records are the input to Gate-2 attestation
materialization: at load time, each record becomes a ``ce:Attestation`` node
in the ``<ce:attestations>`` named graph via ``traceability.attestation.request_attestation``.

Schema (per line):

    {
      "id": "att-<uuid>",                       # required, unique per file
      "signer": "<email or IRI>",               # required
      "signer_role": "Role_AffirmingOfficial",  # required, matches a ce:Role individual
      "signed_at": "2026-07-03T12:00:00+00:00", # required, ISO-8601 with tz
      "covers": ["<ref-id>", ...],              # required, ≥1 ce:Reference IDs
      "controls_attested": ["IR.L2-3.6.1", ...], # required, ≥1 control ids
      "outcome": "passed" | "failed" | "cantTell" | "needsAction",  # required
      "adequacy": "...",                        # required for outcome=passed
      "sufficiency": "...",                     # required for outcome=passed
      "sig": null | "<base64>",                 # optional; cosign detached sig
      "sig_algo": "none" | "cosign-v1",         # required (matches sig)
      "notes": "..."                            # optional
    }

Integrity model (fixture mode):
  * sig_algo="none" → the record is trusted iff the file is git-tracked.
    The audit trail is the git history of the file.
  * sig_algo="cosign-v1" → sig verified against the record's content-hash
    (record with sig field stripped, canonical JSON, sha256). Cosign wiring
    is deferred to a later phase; the shape is here now so records written
    today are format-stable.

File location: `attestations/*.jsonl`. All *.jsonl files under that dir are
loaded at pipeline start (see traceability.attestation_store.load_all).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from oracles.criteria import VALID_OUTCOMES

# The two supported signature algorithms today. cosign-v1 is a shape reservation
# (verification is deferred to the sigstore integration phase); "none" is the
# fixture-mode default where trust comes from the git audit trail.
SIG_ALGO_NONE = "none"
SIG_ALGO_COSIGN_V1 = "cosign-v1"

# The four role slugs — match ce:Role individuals in ontology/ce-attestation-refs.ttl.
VALID_ROLES: frozenset[str] = frozenset({
    "Role_AffirmingOfficial",
    "Role_SecurityOfficer",
    "Role_ITAdmin",
    "Role_OPs",
})


class AttestationStoreError(RuntimeError):
    """Raised on malformed records, freshness violations, or sig mismatches."""


@dataclass(frozen=True)
class AttestationRecord:
    id: str
    signer: str
    signer_role: str
    signed_at: str
    covers: tuple[str, ...]
    controls_attested: tuple[str, ...]
    outcome: str
    adequacy: str = ""
    sufficiency: str = ""
    sig: str | None = None
    sig_algo: str = SIG_ALGO_NONE
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise AttestationStoreError("record.id must be non-empty")
        if self.signer_role not in VALID_ROLES:
            raise AttestationStoreError(
                f"invalid signer_role {self.signer_role!r}; "
                f"expected one of {sorted(VALID_ROLES)}"
            )
        if self.outcome not in VALID_OUTCOMES:
            raise AttestationStoreError(
                f"invalid outcome {self.outcome!r}; "
                f"expected one of {sorted(VALID_OUTCOMES)}"
            )
        if not self.covers:
            raise AttestationStoreError(
                "record.covers must reference ≥1 ce:Reference IDs"
            )
        if not self.controls_attested:
            raise AttestationStoreError(
                "record.controls_attested must list ≥1 controls"
            )
        # Timestamp must parse and be tz-aware.
        try:
            dt = datetime.fromisoformat(self.signed_at)
        except ValueError as e:
            raise AttestationStoreError(
                f"signed_at is not ISO-8601: {self.signed_at!r}"
            ) from e
        if dt.tzinfo is None:
            raise AttestationStoreError(
                f"signed_at must be timezone-aware: {self.signed_at!r}"
            )
        # A passed outcome requires adequacy + sufficiency text (mirrors
        # cmmc:PassedRequiresAdequacyAndSufficiencyShape in cmmc_shapes.ttl).
        if self.outcome == "passed" and not (self.adequacy and self.sufficiency):
            raise AttestationStoreError(
                f"outcome=passed requires non-empty adequacy + sufficiency "
                f"(record {self.id!r})"
            )
        # Sig-algo consistency.
        if self.sig_algo == SIG_ALGO_NONE and self.sig is not None:
            raise AttestationStoreError(
                f"sig_algo=none forbids a sig value (record {self.id!r})"
            )
        if self.sig_algo == SIG_ALGO_COSIGN_V1 and not self.sig:
            raise AttestationStoreError(
                f"sig_algo=cosign-v1 requires a sig value (record {self.id!r})"
            )

    def content_hash(self) -> str:
        """SHA-256 over the canonical JSON of the record with `sig` stripped.

        This is what a cosign signature would sign. Included even for
        sig_algo=none so callers can chain-hash records into an audit ledger
        without waiting on cosign wiring.
        """
        payload = {k: v for k, v in asdict(self).items() if k != "sig"}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_file(path: str | Path) -> list[AttestationRecord]:
    """Parse one JSONL file into records. Blank lines and `# …` comments are
    skipped. Raises AttestationStoreError on any malformed line."""
    records: list[AttestationRecord] = []
    seen_ids: set[str] = set()
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise AttestationStoreError(
                    f"{path}:{lineno}: not valid JSON: {e.msg}"
                ) from e
            rec = _record_from_obj(obj, path, lineno)
            if rec.id in seen_ids:
                raise AttestationStoreError(
                    f"{path}:{lineno}: duplicate record id {rec.id!r}"
                )
            seen_ids.add(rec.id)
            records.append(rec)
    return records


def load_all(dir_path: str | Path) -> list[AttestationRecord]:
    """Load every *.jsonl file under `dir_path` (non-recursive). Returns
    records in file+line order. Empty result if the directory is missing."""
    d = Path(dir_path)
    if not d.is_dir():
        return []
    all_records: list[AttestationRecord] = []
    for path in sorted(d.glob("*.jsonl")):
        all_records.extend(load_file(path))
    return all_records


def append_record(path: str | Path, record: AttestationRecord) -> None:
    """Append one record to a JSONL file (creating the file if missing)."""
    line = json.dumps(_record_to_obj(record), sort_keys=True, separators=(",", ":"))
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _record_from_obj(obj: dict, path, lineno: int) -> AttestationRecord:
    required = {"id", "signer", "signer_role", "signed_at",
                "covers", "controls_attested", "outcome"}
    missing = required - obj.keys()
    if missing:
        raise AttestationStoreError(
            f"{path}:{lineno}: missing required fields: {sorted(missing)}"
        )
    return AttestationRecord(
        id=obj["id"],
        signer=obj["signer"],
        signer_role=obj["signer_role"],
        signed_at=obj["signed_at"],
        covers=tuple(obj["covers"]),
        controls_attested=tuple(obj["controls_attested"]),
        outcome=obj["outcome"],
        adequacy=obj.get("adequacy", ""),
        sufficiency=obj.get("sufficiency", ""),
        sig=obj.get("sig"),
        sig_algo=obj.get("sig_algo", SIG_ALGO_NONE),
        notes=obj.get("notes", ""),
    )


def _record_to_obj(rec: AttestationRecord) -> dict:
    return {
        "id": rec.id,
        "signer": rec.signer,
        "signer_role": rec.signer_role,
        "signed_at": rec.signed_at,
        "covers": list(rec.covers),
        "controls_attested": list(rec.controls_attested),
        "outcome": rec.outcome,
        "adequacy": rec.adequacy,
        "sufficiency": rec.sufficiency,
        "sig": rec.sig,
        "sig_algo": rec.sig_algo,
        "notes": rec.notes,
    }
