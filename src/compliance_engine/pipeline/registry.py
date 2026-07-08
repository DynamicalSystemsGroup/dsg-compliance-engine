"""Content-addressed, write-once artifact registry (the local tier).

Every artifact the engine produces — evidence bytes, the Order, oracle results,
and later the BOM — is stored **write-once by its SHA-256 hash**. The key IS the
content hash, so:
- storing identical bytes again is a no-op (idempotent),
- an object can never be silently overwritten (write-once),
- a stored object can be re-hashed to detect tampering (`verify`).

This is the "tiered GCS/Azure Blob registry" from the design, backed locally for
now. It is built ON TOP of the `StoreBackend` abstraction (`pipeline.backends`):
construction runs the backend's `probe()` so an unwritable store root fails fast
(exit-2 style) rather than at the last stage. A future object-store backend
would provide native put/get; today the local tier persists object bytes and the
index under the store root.

Hashing reuses the SAME SHA-256 discipline as `evidence/hashing.py` (a registry
key equals the `ce:contentHash` other units already emit) — no new hash is
invented. The index is serialized deterministically via `_serialize_for_hash`
(`json.dumps(sort_keys=True)`), so it byte-reproduces and reloads cleanly.

Two-level index (only these two — the `control_id → BOMs` reverse index is
deliberately deferred, no consumer yet):
    contract_id → latest BOM hash
    bom_hash    → [artifact hashes]
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from compliance_engine.pipeline.backends.base import BackendUnavailable
from compliance_engine.pipeline.backends.local import LocalBackend
from compliance_engine.pipeline.evidence.hashing import _serialize_for_hash

_OBJECTS_DIR = "objects"
_INDEX_FILE = "index.json"

# Re-exported so consumers can `from compliance_engine.pipeline.registry import BackendUnavailable`
# — the error a caller catches when a store root is unwritable at construction.
__all__ = ["Registry", "ContentMismatch", "BackendUnavailable", "content_hash"]


class ContentMismatch(RuntimeError):
    """Stored bytes under a hash do not match the key.

    Signals either a write-once violation (different content forced under an
    existing hash) or on-disk tampering discovered at write time. A SHA-256
    collision is the only other (infeasible) cause.
    """


def content_hash(content: bytes) -> str:
    """SHA-256 hex of raw bytes — the registry key primitive."""
    return hashlib.sha256(content).hexdigest()


class Registry:
    """Write-once, content-addressed store with a two-level index.

    Construct from a store root (and optionally an explicit backend). The
    backend's `probe()` runs immediately: an unwritable root raises
    `BackendUnavailable` at construction.
    """

    def __init__(
        self,
        root: str | Path,
        backend: LocalBackend | None = None,
        remote: object | None = None,
    ) -> None:
        self.root = Path(root)
        self.backend = backend or LocalBackend()
        # Fail-fast: the backend probe creates + write-tests the root.
        self.backend.probe(self.root)

        # `remote` is an optional write-through/read-through tier (e.g. a
        # FlexoBackend), duck-typed to put_object(bytes) -> str /
        # get_object(str) -> bytes. Feature-detected via hasattr rather than a
        # formal Protocol, since LocalBackend does not (and need not)
        # implement this narrower object-store surface. `local` remains the
        # cache/fallback tier regardless: a remote failure never fails a
        # write, it only sets `degraded`.
        self.remote = remote
        self.degraded = False

        self.objects_dir = self.root / _OBJECTS_DIR
        self.index_path = self.root / _INDEX_FILE
        self._index = self._load_index()

    # -- object store -------------------------------------------------------

    def _object_path(self, hash_: str) -> Path:
        """Tiered layout: objects/<h[:2]>/<h[2:4]>/<h> (fans out millions)."""
        return self.objects_dir / hash_[:2] / hash_[2:4] / hash_

    def put(self, content: bytes, *, kind: str = "artifact") -> str:
        """Store `content` write-once; return its SHA-256 hex key.

        Idempotent: identical bytes → same hash, single stored object, no error.
        Write-once: if an object already exists at the key, its bytes are
        verified to match `content`; a mismatch raises `ContentMismatch` and the
        object is never overwritten.

        If a `remote` tier is configured (e.g. a FlexoBackend), the content is
        also write-through'd there first. A remote failure never fails the
        local write — it sets `self.degraded = True` and the local object is
        still stored, so local remains the durable cache/fallback tier.
        """
        h = content_hash(content)
        path = self._object_path(h)
        if path.exists():
            if path.read_bytes() != content:
                raise ContentMismatch(
                    f"object {h} exists with different bytes (write-once violation "
                    f"or tampering)"
                )
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_bytes(content)
            tmp.replace(path)  # atomic publish

        put_object = getattr(self.remote, "put_object", None)
        if put_object is not None:
            try:
                put_object(content)
            except Exception:
                self.degraded = True

        # Record the artifact kind for observability (does not affect the key).
        if self._index["objects"].get(h) != kind:
            self._index["objects"][h] = kind
            self._persist_index()
        return h

    def has(self, hash_: str) -> bool:
        """True if an object with this hash is stored locally."""
        return self._object_path(hash_).exists()

    def get(self, hash_: str) -> bytes:
        """Return the stored bytes for `hash_`.

        Reads locally first; on local miss, falls back to the `remote` tier
        (if configured) and backfills the local cache on success. Raises
        `KeyError` if the object is absent from both.
        """
        path = self._object_path(hash_)
        if path.exists():
            return path.read_bytes()

        get_object = getattr(self.remote, "get_object", None)
        if get_object is not None:
            try:
                content = get_object(hash_)
            except Exception:
                pass
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_name(path.name + ".tmp")
                tmp.write_bytes(content)
                tmp.replace(path)
                return content

        raise KeyError(hash_)

    def verify(self, hash_: str) -> bool:
        """Re-hash the stored bytes and confirm they match the key (tamper check).

        Returns False if the object is missing or its bytes no longer hash to
        the key.
        """
        path = self._object_path(hash_)
        if not path.exists():
            return False
        return content_hash(path.read_bytes()) == hash_

    def hash_reference(self, hash_: str) -> str:
        """Bare content reference for a stored hash.

        The seam where content signing (Sigstore) slots in later. This is a
        HASH REFERENCE, not a signature — no "sign" naming here on purpose.
        """
        return f"registry://{hash_}"

    # -- two-level index ----------------------------------------------------

    def set_latest_bom(self, contract_id: str, bom_hash: str) -> None:
        """Point a contract at its latest BOM hash (level 1)."""
        self._index["latest_bom"][contract_id] = bom_hash
        self._persist_index()

    def latest_bom(self, contract_id: str) -> str | None:
        """Resolve a contract to its latest BOM hash, or None."""
        return self._index["latest_bom"].get(contract_id)

    def set_bom_artifacts(self, bom_hash: str, artifact_hashes: list[str]) -> None:
        """Record the artifact hashes a BOM references (level 2)."""
        self._index["bom_artifacts"][bom_hash] = list(artifact_hashes)
        self._persist_index()

    def bom_artifacts(self, bom_hash: str) -> list[str]:
        """Resolve a BOM hash to its artifact hashes ([] if unknown)."""
        return list(self._index["bom_artifacts"].get(bom_hash, []))

    def set_bom_signature(self, bom_hash: str, sig_hash: str) -> None:
        """Point a BOM hash at the registry object hash of its detached signature."""
        self._index["bom_signatures"][bom_hash] = sig_hash
        self._persist_index()

    def bom_signature(self, bom_hash: str) -> str | None:
        """Resolve a BOM hash to its signature's registry object hash, or None."""
        return self._index["bom_signatures"].get(bom_hash)

    # -- index persistence --------------------------------------------------

    @staticmethod
    def _empty_index() -> dict:
        return {
            "latest_bom": {}, "bom_artifacts": {}, "bom_signatures": {}, "objects": {},
        }

    def _load_index(self) -> dict:
        if self.index_path.exists():
            loaded = json.loads(self.index_path.read_text(encoding="utf-8"))
            # Merge over the skeleton so older/partial indexes gain new keys.
            index = self._empty_index()
            index.update({k: loaded.get(k, index[k]) for k in index})
            return index
        return self._empty_index()

    def _persist_index(self) -> None:
        """Write the index deterministically (sort_keys) via the backend root."""
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.index_path.with_name(self.index_path.name + ".tmp")
        tmp.write_text(_serialize_for_hash(self._index) + "\n", encoding="utf-8")
        tmp.replace(self.index_path)

    def describe(self) -> str:
        return f"Content-addressed registry at {self.root} (backend: {self.backend.describe()})"
