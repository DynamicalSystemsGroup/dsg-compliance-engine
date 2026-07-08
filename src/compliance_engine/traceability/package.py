"""The audit package (Phase E): one signed deliverable a C3PAO re-verifies.

`build_audit_package` assembles a run's outputs — the BOM, the SSP, the audit +
SPRS verdict, the full-chain provenance (SOP adherence), and the per-control
chain from control -> attestation -> signed policy references — into a single
`manifest.json`, then signs the manifest (Ed25519 by default; cosign+KMS in
production). `verify_audit_package` re-derives everything offline: it verifies the
manifest signature, re-hashes every bundled artifact, and re-runs the SOP-adherence
check — so an assessor can confirm the delivery is exactly what was signed and that
its automated checks reproduce, without trusting the producer.

The manifest is deterministic and byte-stable (sorted keys), so re-building from
the same inputs yields the same bytes and the same signature.
"""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph

from compliance_engine.ontology.prefixes import CE, CMMC
from compliance_engine.signing import SigningError, default_local_signer, get_signer
from compliance_engine.traceability.provenance import check_sop_adherence

PACKAGE_SCHEMA = "ce-audit-package/v1"
_MANIFEST = "manifest.json"
_SIGNATURE = "manifest.sig"
# Artifacts copied into the package and re-hashed on verify.
_BUNDLED = ("bom.json", "ssp.md")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


# ---------------------------------------------------------------------------
# control -> policy references (from the structural model)
# ---------------------------------------------------------------------------

def _control_reference_map(repo_root: Path) -> dict[str, list[dict]]:
    """{control_id: [{ref, source, version, signature, uri}]} for the attested
    (Track B) controls, read from tier1.ttl + references.ttl. Empty for controls
    with no attested-reference module (machine / inherited)."""
    struct = Graph()
    struct.parse(repo_root / "data" / "structural" / "tier1.ttl", format="turtle")
    struct.parse(repo_root / "data" / "structural" / "references.ttl", format="turtle")

    out: dict[str, list[dict]] = {}
    for module in struct.subjects(CE.reference, None):
        ref = struct.value(module, CE.reference)
        if ref is None:
            continue
        src = struct.value(module, CE.authoritativeSource)
        rec = {
            "ref": str(ref).rsplit("/", 1)[-1],
            "source": str(struct.value(src, None) or src).rsplit("/", 1)[-1] if src else "",
            "uri": str(struct.value(ref, CE.uri) or ""),
            "version": str(struct.value(ref, CE.version) or ""),
            "signature": str(struct.value(ref, CE.signature) or ""),
        }
        for ctrl in struct.objects(module, CMMC.controlsSatisfied):
            cid = str(ctrl).rsplit("#", 1)[-1].rsplit("/", 1)[-1]
            out.setdefault(cid, []).append(rec)
    return out


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

@dataclass
class AuditPackage:
    package_dir: Path
    manifest: dict
    sig_algo: str
    key_id: str


def build_audit_package(
    ds,
    output_dir: Path,
    contract_id: str,
    *,
    audit_report,
    bom_hash: str,
    repo_root: Path | None = None,
    signer=None,
) -> AuditPackage:
    """Assemble + sign the audit package under `output_dir/package/`.

    `audit_report` is the AuditReport for this run (sprs, contradictions, proven
    split); `bom_hash` is the BOM's content hash. Requires bom.json + ssp.md
    already written under `output_dir`.
    """
    output_dir = Path(output_dir)
    repo_root = repo_root or Path(__file__).resolve().parents[3]
    signer = signer or default_local_signer()

    bom = json.loads((output_dir / "bom.json").read_text())
    prov = check_sop_adherence(ds)
    ref_map = _control_reference_map(repo_root)
    # Full signed-policy inventory (all Track B references with version + signature),
    # independent of which controls this Order's slice exercised.
    policies = {}
    for refs in ref_map.values():
        for r in refs:
            policies[r["ref"]] = r
    policy_list = sorted(policies.values(), key=lambda r: r["ref"])

    # Per-control chain: status + backing + attestation + signed policy references.
    attestations = {a["control_id"]: a for a in bom.get("attestations", [])}
    controls = []
    for row in bom.get("control_mapping", []):
        cid = row["control_id"]
        att = attestations.get(cid, {})
        controls.append({
            "control": cid,
            "status": row.get("status"),
            "evidence_backing": row.get("evidence_backing"),
            "evidence_hashes": row.get("evidence_hashes", []),
            "oracle_outcome": row.get("oracle_outcome"),
            "reference_id": row.get("reference_id"),
            "git_commit": row.get("git_commit"),
            "git_committed_at": row.get("git_committed_at"),
            "attestation": {
                "outcome": att.get("outcome"),
                "official": att.get("official"),
                "override_justification": att.get("override_justification"),
                "override_evidence": att.get("override_evidence"),
            },
            "policy_references": ref_map.get(cid, []),
        })

    sprs = audit_report.sprs
    manifest = {
        "schema": PACKAGE_SCHEMA,
        "contract": contract_id,
        "bom_hash": bom_hash,
        "evidentiary_status": bom.get("evidentiary_status"),
        "sprs": {
            "score": sprs.score,
            "status": sprs.status,
            "valid_submission": sprs.valid_submission,
        },
        "contradictions": [
            {"control": c.control, "oracle_outcome": c.oracle_outcome}
            for c in audit_report.contradictions
        ],
        "proven_vs_attested": {
            "machine": audit_report.proven.machine_count,
            "human_only": audit_report.proven.human_count,
        },
        "provenance": {
            "sop_adherence_ok": prov.ok,
            "executed_steps": list(prov.executed_steps),
            "deviations": list(prov.orphan_activities)
                          + list(prov.predecessor_violations)
                          + list(prov.unrealized_outputs),
        },
        "controls": sorted(controls, key=lambda c: c["control"]),
        "policies": policy_list,
        "artifacts": [
            {"name": name, "sha256": _sha256_file(output_dir / name)}
            for name in _BUNDLED if (output_dir / name).exists()
        ],
    }

    manifest_bytes = _canonical_bytes(manifest)
    signature = base64.b64encode(signer.sign(manifest_bytes)).decode("ascii")
    key_id = getattr(signer, "key_id", signer.algo)

    pkg = output_dir / "package"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / _MANIFEST).write_bytes(manifest_bytes)
    (pkg / _SIGNATURE).write_text(json.dumps(
        {"sig": signature, "sig_algo": signer.algo, "key_id": key_id},
        sort_keys=True, indent=2,
    ))
    for name in _BUNDLED:
        src = output_dir / name
        if src.exists():
            shutil.copy2(src, pkg / name)

    # bom.json.sig (ce:step-SignAndStore's detached BOM signature, written by
    # cli.py's _do_bom) is not sha256-tracked as a bundled artifact — it is
    # itself a signature, not content to re-hash — but it is copied alongside
    # bom.json so an assessor examining the package alone (without the raw
    # output_dir) can still verify the BOM's own signature independently of
    # the manifest's signature over the whole package.
    bom_sig_src = output_dir / "bom.json.sig"
    if bom_sig_src.exists():
        shutil.copy2(bom_sig_src, pkg / "bom.json.sig")

    return AuditPackage(package_dir=pkg, manifest=manifest, sig_algo=signer.algo, key_id=key_id)


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------

@dataclass
class PackageVerifyResult:
    ok: bool
    signature_ok: bool
    artifacts_ok: bool
    chain_ok: bool
    issues: list[str]

    def summary(self) -> str:
        if self.ok:
            return "Audit package VERIFIED: signature valid, artifacts intact, chain complete."
        return "Audit package FAILED: " + "; ".join(self.issues)


def verify_audit_package(package_dir: Path) -> PackageVerifyResult:
    """Re-verify a package offline: manifest signature, artifact hashes, and the
    per-control control -> signed-policy chain."""
    package_dir = Path(package_dir)
    issues: list[str] = []

    manifest_path = package_dir / _MANIFEST
    sig_path = package_dir / _SIGNATURE
    if not manifest_path.exists() or not sig_path.exists():
        return PackageVerifyResult(False, False, False, False,
                                   [f"missing {_MANIFEST} or {_SIGNATURE}"])

    manifest_bytes = manifest_path.read_bytes()
    sig_obj = json.loads(sig_path.read_text())

    # 1. signature over the manifest bytes.
    #    The algorithm is NOT taken on trust from the signature block: an unsigned
    #    or downgraded manifest (sig_algo=none / empty) cannot be "verified as
    #    authentic". Rewriting manifest.sig to {"sig_algo":"none","sig":""} — the
    #    cheap forgery that needs no key — is rejected here rather than accepted by
    #    a NullSigner. Only a real cryptographic algorithm can clear this gate.
    signature_ok = False
    sig_algo = sig_obj.get("sig_algo")
    if sig_algo in (None, "", "none"):
        issues.append(
            "manifest is unsigned (sig_algo=none) — a package cannot be verified as "
            "authentic without a real signature. If this package was signed, its "
            "signature block was downgraded (tampering)."
        )
    else:
        try:
            signer = get_signer(sig_algo)
            signature_ok = signer.verify(
                manifest_bytes, base64.b64decode(sig_obj["sig"], validate=True)
            )
        except (SigningError, ValueError, KeyError) as exc:
            issues.append(f"signature error: {exc}")
        if not signature_ok:
            issues.append("manifest signature does not verify (tampered or wrong key)")

    manifest = json.loads(manifest_bytes)

    # 2. re-hash bundled artifacts
    artifacts_ok = True
    for art in manifest.get("artifacts", []):
        f = package_dir / art["name"]
        if not f.exists():
            artifacts_ok = False
            issues.append(f"artifact missing: {art['name']}")
        elif _sha256_file(f) != art["sha256"]:
            artifacts_ok = False
            issues.append(f"artifact hash mismatch: {art['name']}")

    # 2.5. bom.json.sig — the BOM's own detached signature (ce:step-SignAndStore),
    #      independent of the manifest's signature over the whole package. Its
    #      absence is non-fatal (older packages predate this signature); its
    #      presence with an invalid signature is a hard failure.
    bom_sig_path = package_dir / "bom.json.sig"
    bom_path = package_dir / "bom.json"
    if bom_sig_path.exists() and bom_path.exists():
        try:
            bom_sig = base64.b64decode(bom_sig_path.read_text().strip(), validate=True)
            bom_signer = default_local_signer()
            if not bom_signer.verify(bom_path.read_bytes(), bom_sig):
                artifacts_ok = False
                issues.append("bom.json.sig does not verify against bom.json (tampered)")
        except ValueError as exc:
            artifacts_ok = False
            issues.append(f"bom.json.sig malformed: {exc}")

    # 3. control -> signed-policy chain: every attested control resolves to at least
    #    one policy reference, and MET controls carry an attestation outcome.
    chain_ok = True
    for c in manifest.get("controls", []):
        if c.get("evidence_backing") == "override":
            att = c.get("attestation", {})
            if not att.get("override_evidence"):
                chain_ok = False
                issues.append(f"{c['control']}: override without appended evidence")
        if c.get("status") == "MET" and not c.get("attestation", {}).get("outcome"):
            chain_ok = False
            issues.append(f"{c['control']}: MET without an attestation outcome")

    ok = signature_ok and artifacts_ok and chain_ok
    return PackageVerifyResult(ok, signature_ok, artifacts_ok, chain_ok, issues)
