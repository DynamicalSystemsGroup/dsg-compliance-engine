"""Tests for the content-addressed write-once registry.

Covers: round-trip, idempotent put, write-once/tamper detection, the two-level
index (contract → latest BOM → artifact hashes), deterministic index
persistence + reload, and fail-fast construction on an unwritable store root.
"""

from __future__ import annotations

import hashlib

import pytest

from compliance_engine.pipeline.backends.base import BackendUnavailable
from compliance_engine.pipeline.registry import ContentMismatch, Registry, content_hash


def _reg(tmp_path) -> Registry:
    return Registry(tmp_path / "store")


class TestRoundTrip:
    def test_put_get_has_verify(self, tmp_path):
        reg = _reg(tmp_path)
        data = b"evidence-export-bytes"
        h = reg.put(data, kind="evidence")

        assert h == hashlib.sha256(data).hexdigest()
        assert h == content_hash(data)
        assert len(h) == 64
        assert reg.has(h)
        assert reg.get(h) == data
        assert reg.verify(h) is True

    def test_get_missing_raises(self, tmp_path):
        reg = _reg(tmp_path)
        assert reg.has("0" * 64) is False
        assert reg.verify("0" * 64) is False
        with pytest.raises(KeyError):
            reg.get("0" * 64)

    def test_tiered_layout(self, tmp_path):
        reg = _reg(tmp_path)
        h = reg.put(b"x", kind="artifact")
        obj = tmp_path / "store" / "objects" / h[:2] / h[2:4] / h
        assert obj.is_file()

    def test_hash_reference_format(self, tmp_path):
        reg = _reg(tmp_path)
        h = reg.put(b"x")
        assert reg.hash_reference(h) == f"registry://{h}"
        assert "sign" not in reg.hash_reference(h)  # hash reference, not signature


class TestIdempotentWriteOnce:
    def test_put_same_bytes_twice_is_noop(self, tmp_path):
        reg = _reg(tmp_path)
        h1 = reg.put(b"same-bytes", kind="evidence")
        h2 = reg.put(b"same-bytes", kind="evidence")
        assert h1 == h2

        # Exactly one stored object.
        objects = list((tmp_path / "store" / "objects").rglob("*"))
        files = [p for p in objects if p.is_file()]
        assert len(files) == 1

    def test_different_content_under_existing_hash_rejected(self, tmp_path):
        reg = _reg(tmp_path)
        h = reg.put(b"original", kind="evidence")
        # Force divergent bytes onto the stored object (tamper), then re-put the
        # ORIGINAL: the key still hashes to h, but stored bytes differ → rejected.
        obj = reg._object_path(h)
        obj.write_bytes(b"tampered-different")
        with pytest.raises(ContentMismatch):
            reg.put(b"original", kind="evidence")

    def test_verify_detects_tampering(self, tmp_path):
        reg = _reg(tmp_path)
        h = reg.put(b"trustworthy", kind="evidence")
        assert reg.verify(h) is True

        reg._object_path(h).write_bytes(b"mutated-on-disk")
        assert reg.verify(h) is False  # re-hash mismatch detected


class TestTwoLevelIndex:
    def test_contract_to_bom_to_artifacts(self, tmp_path):
        reg = _reg(tmp_path)
        ev1 = reg.put(b"evidence-1", kind="evidence")
        ev2 = reg.put(b"evidence-2", kind="evidence")
        bom_hash = reg.put(b'{"bom":"nv012"}', kind="bom")

        reg.set_bom_artifacts(bom_hash, [ev1, ev2])
        reg.set_latest_bom("NV012", bom_hash)

        assert reg.latest_bom("NV012") == bom_hash
        assert reg.bom_artifacts(bom_hash) == [ev1, ev2]

    def test_unknown_lookups_return_defaults(self, tmp_path):
        reg = _reg(tmp_path)
        assert reg.latest_bom("UNKNOWN") is None
        assert reg.bom_artifacts("deadbeef") == []

    def test_latest_bom_updates(self, tmp_path):
        reg = _reg(tmp_path)
        b1 = reg.put(b"bom-v1", kind="bom")
        b2 = reg.put(b"bom-v2", kind="bom")
        reg.set_latest_bom("NV012", b1)
        reg.set_latest_bom("NV012", b2)
        assert reg.latest_bom("NV012") == b2


class TestIndexPersistence:
    def test_reload_across_fresh_instance(self, tmp_path):
        reg = _reg(tmp_path)
        ev = reg.put(b"evidence", kind="evidence")
        bom = reg.put(b"bom", kind="bom")
        reg.set_bom_artifacts(bom, [ev])
        reg.set_latest_bom("NV012", bom)

        # A brand-new Registry pointed at the same root reloads the index.
        reg2 = Registry(tmp_path / "store")
        assert reg2.latest_bom("NV012") == bom
        assert reg2.bom_artifacts(bom) == [ev]
        assert reg2.has(ev)

    def test_index_serialization_is_deterministic(self, tmp_path):
        # Two registries fed the SAME data in DIFFERENT insertion order produce
        # byte-identical index.json (sort_keys=True).
        ra = Registry(tmp_path / "a")
        rb = Registry(tmp_path / "b")

        ra.set_latest_bom("NV012", "aa")
        ra.set_latest_bom("NV001", "bb")
        rb.set_latest_bom("NV001", "bb")
        rb.set_latest_bom("NV012", "aa")

        bytes_a = (tmp_path / "a" / "index.json").read_bytes()
        bytes_b = (tmp_path / "b" / "index.json").read_bytes()
        assert bytes_a == bytes_b


class TestFailFast:
    def test_unwritable_root_raises_at_construction(self, tmp_path):
        # Root whose parent is a FILE → mkdir fails → clean BackendUnavailable
        # (independent of filesystem permissions / user).
        blocker = tmp_path / "not-a-dir"
        blocker.write_text("i am a file\n")
        with pytest.raises(BackendUnavailable):
            Registry(blocker / "store")


class _FakeRemote:
    """Minimal put_object/get_object stub — the duck-typed surface Registry
    feature-detects, independent of any real FlexoBackend."""

    def __init__(self, *, fail_put: bool = False):
        self.fail_put = fail_put
        self._store: dict[str, bytes] = {}

    def put_object(self, content: bytes) -> str:
        if self.fail_put:
            raise RuntimeError("remote unavailable")
        h = content_hash(content)
        self._store[h] = content
        return h

    def get_object(self, hash_: str) -> bytes:
        return self._store[hash_]


class TestRemoteComposition:
    def test_put_writes_through_to_remote(self, tmp_path):
        remote = _FakeRemote()
        reg = Registry(tmp_path / "store", remote=remote)
        h = reg.put(b"content-a")

        assert reg.degraded is False
        assert remote.get_object(h) == b"content-a"
        assert reg.get(h) == b"content-a"  # still readable locally

    def test_get_falls_back_to_remote_on_local_miss_and_backfills(self, tmp_path):
        remote = _FakeRemote()
        h = remote.put_object(b"remote-only")

        reg = Registry(tmp_path / "store", remote=remote)
        assert reg.has(h) is False  # not local yet

        assert reg.get(h) == b"remote-only"
        assert reg.has(h) is True  # backfilled into local cache

    def test_remote_put_failure_degrades_but_local_write_still_succeeds(self, tmp_path):
        remote = _FakeRemote(fail_put=True)
        reg = Registry(tmp_path / "store", remote=remote)

        h = reg.put(b"content-b")  # must not raise

        assert reg.degraded is True
        assert reg.get(h) == b"content-b"  # local write unaffected

    def test_no_remote_configured_behaves_exactly_as_before(self, tmp_path):
        reg = Registry(tmp_path / "store")
        h = reg.put(b"content-c")
        assert reg.degraded is False
        assert reg.get(h) == b"content-c"
