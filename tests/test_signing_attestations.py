"""Cryptographically-signed attestations (Phase B).

The AttestationRecord is the Affirming Official's signed statement over a set of
policy references — the evidence node behind a human sign-off. These tests prove
the Ed25519 signing path is real: a signed record verifies, a tampered one is
rejected at load, and an unverifiable production (cosign) record fails closed.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from compliance_engine.traceability import attestation_store as store
from compliance_engine.traceability.attestation_store import (
    AttestationRecord,
    AttestationStoreError,
    sign_record,
    verify_record,
)


def _record(**over) -> AttestationRecord:
    base = dict(
        id="att-test-1",
        signer="ao@example.gov",
        signer_role="Role_AffirmingOfficial",
        signed_at="2026-06-15T12:00:00+00:00",
        covers=("REF_POL_IR_Plan_v1",),
        controls_attested=("IR.L2-3.6.1",),
        outcome="passed",
        adequacy="IR plan adopted and tested.",
        sufficiency="2026 tabletop report on file.",
    )
    base.update(over)
    return AttestationRecord(**base)


def test_ed25519_sign_then_verify_round_trip():
    signed = sign_record(_record())
    assert signed.sig_algo == "ed25519-v1"
    assert signed.sig
    verify_record(signed)  # does not raise


def test_tampered_signed_record_is_rejected():
    signed = sign_record(_record())
    # Keep the signature but change a covered field.
    tampered = replace(signed, controls_attested=("IR.L2-3.6.2",))
    with pytest.raises(AttestationStoreError):
        verify_record(tampered)


def test_garbage_signature_is_rejected():
    bad = replace(_record(), sig="bm90LWEtc2ln", sig_algo="ed25519-v1")
    with pytest.raises(AttestationStoreError):
        verify_record(bad)


def test_cosign_record_fails_closed_without_cosign():
    # No cosign binary / KMS in this environment: a cosign-v1 record must not be
    # silently trusted — verification fails closed.
    rec = replace(_record(), sig="c29tZS1zaWc=", sig_algo="cosign-v1")
    with pytest.raises(AttestationStoreError):
        verify_record(rec)


def test_none_record_needs_no_signature():
    verify_record(_record())  # sig_algo defaults to none — no-op


def test_signed_record_survives_jsonl_round_trip_and_loads(tmp_path):
    signed = sign_record(_record())
    path = tmp_path / "signed.jsonl"
    store.append_record(path, signed)
    loaded = store.load_file(path)  # load_file verifies signatures
    assert len(loaded) == 1
    assert loaded[0].sig_algo == "ed25519-v1"


def test_load_file_rejects_a_tampered_signed_line(tmp_path):
    signed = sign_record(_record())
    path = tmp_path / "bad.jsonl"
    store.append_record(path, signed)
    # Corrupt the covered content on disk while leaving the signature intact.
    text = path.read_text().replace("IR.L2-3.6.1", "IR.L2-3.6.9")
    path.write_text(text)
    with pytest.raises(AttestationStoreError):
        store.load_file(path)
