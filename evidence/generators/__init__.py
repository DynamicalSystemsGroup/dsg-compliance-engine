"""Evidence generators — the compliance analogues of the ADCS analysis engines.

Each generator honors the contract in ``evidence/DESIGN.md``:
1. Emit a raw artifact (JSON/text) whose bytes are content-hashed.
2. Carry a machine-readable ``summary`` whose keys match ``oracles/criteria.py``.
3. Bind a ``ce:Evidence`` node (via ``evidence/binding.py``) that **addresses**
   its control(s), never attests them.

This module is the **live-tenant config-export path** (MFA / region / FIPS /
at-rest / IAM). It stays **fixture-backed** (``fixtures/nv012/<set>/``) until a
real cloud exists — every artifact is flagged ``evidentiary_status="mock"``
(R12). The plan-time Terraform/OPA evidence path is a separate unit (U14).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from evidence.binding import CollectionMetadata

# Repo-root/fixtures/nv012 — generators/__init__.py → generators → evidence → root.
_DEFAULT_FIXTURES_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "nv012"

# The three labelled fixture sets seeded in U6a (see fixtures/nv012/README.md).
FIXTURE_SETS = ("all-covered", "gap", "contradiction")


@dataclass(frozen=True)
class EvidenceArtifact:
    """A collected evidence artifact, before it is bound into the graph.

    ``raw_bytes`` are the exact bytes hashed; ``summary`` is the machine-readable
    metric dict the oracles read; ``controls`` are the control ids this artifact
    **addresses**; ``collection_metadata`` records how/where it was collected;
    ``evidentiary_status`` is ``"mock"`` for fixture-sourced artifacts (R12).
    """

    raw_bytes: bytes
    summary: dict
    controls: list[str]
    collection_metadata: CollectionMetadata
    evidentiary_status: str = "mock"
    # --- binding hints (optional) ---------------------------------------
    method: str = "config-export"   # "config-export" | "policy-check"
    source_file: str = ""           # fixture path → ce:sourceFile / documentRef
    tool: str = ""                  # policy-check only (e.g. "opa", "checkov")
    result: dict | None = None      # policy-check only: {status, detail, ...}


@dataclass
class GeneratorContext:
    """Runtime context for a generator run.

    ``evidence_set`` selects which fixture subdir to read (default the happy
    path). ``fixtures_root`` is overridable for tests.
    """

    fixtures_root: Path = _DEFAULT_FIXTURES_ROOT
    evidence_set: str = "all-covered"

    def set_dir(self) -> Path:
        return Path(self.fixtures_root) / self.evidence_set


@runtime_checkable
class Generator(Protocol):
    """A source of evidence artifacts addressing a known set of controls."""

    controls: list[str]

    def collect(self, ctx: GeneratorContext) -> list[EvidenceArtifact]:
        ...


def _load_fixture_files(ctx: GeneratorContext) -> list[tuple[Path, dict]]:
    """Read every ``*.json`` export in the selected set, sorted for determinism.

    Returns ``(path, parsed_json)`` pairs. A missing set dir yields ``[]`` so a
    ``gap`` set that omits a file simply produces less evidence (no raise).
    """
    import json

    set_dir = ctx.set_dir()
    if not set_dir.is_dir():
        return []
    out: list[tuple[Path, dict]] = []
    for path in sorted(set_dir.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            out.append((path, json.load(fh)))
    return out


def _metadata_from_envelope(doc: dict) -> CollectionMetadata:
    """Lift a fixture envelope into a CollectionMetadata."""
    return CollectionMetadata(
        source_system=doc.get("source_system", "unknown"),
        export_command=doc.get("export_command", ""),
        collected_at=doc.get("collected_at", ""),
        collector_version=doc.get("collector_version", "mock-0.1.0"),
    )


__all__ = [
    "EvidenceArtifact",
    "GeneratorContext",
    "Generator",
    "CollectionMetadata",
    "FIXTURE_SETS",
    "_load_fixture_files",
    "_metadata_from_envelope",
]
