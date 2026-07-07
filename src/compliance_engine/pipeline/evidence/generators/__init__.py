"""Evidence generators — the compliance analogues of the ADCS analysis engines.

Each generator honors the contract in ``evidence/DESIGN.md``:
1. Emit a raw artifact (JSON/text) whose bytes are content-hashed.
2. Carry a machine-readable ``summary`` whose keys match ``oracles/criteria.py``.
3. Bind a ``ce:Evidence`` node (via ``evidence/binding.py``) that **addresses**
   its control(s), never attests them.

This module is the **live-tenant config-export path** (MFA / region / FIPS /
at-rest / IAM). It stays **fixture-backed** (``fixtures/nv012/<set>/``) until a
real cloud exists — every artifact is flagged ``evidentiary_status="mock"``
(R12). The plan-time Terraform/OPA evidence path lives in
``evidence/generators/terraform_plan.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from compliance_engine.pipeline.evidence.binding import CollectionMetadata

# Repo-root/fixtures/nv012 — generators/__init__.py → generators → evidence → pipeline → compliance_engine → src → root.
_DEFAULT_FIXTURES_ROOT = Path(__file__).resolve().parents[5] / "fixtures" / "nv012"

# The three labelled fixture sets (see fixtures/nv012/README.md).
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


_BASE_SET = "all-covered"


def _load_fixture_files(ctx: GeneratorContext) -> list[tuple[Path, dict]]:
    """Read the ``*.json`` exports for the selected set, sorted for determinism.

    Scenario sets LAYER over the ``all-covered`` base: a scenario is "all-covered
    but with these files changed". The base set's files load first, then the
    selected set's files override by filename (so ``contradiction/workspace_2sv.json``
    replaces the base's, flipping just the one metric while every other control keeps
    its passing evidence). ``all-covered`` itself is the base and uses no overlay.

    Returns ``(path, parsed_json)`` pairs. A missing set dir yields the base alone.
    """
    import json

    root = Path(ctx.fixtures_root)
    merged: dict[str, tuple[Path, dict]] = {}

    def _read_dir(d: Path) -> None:
        if not d.is_dir():
            return
        for path in sorted(d.glob("*.json")):
            with path.open(encoding="utf-8") as fh:
                merged[path.name] = (path, json.load(fh))

    if ctx.evidence_set != _BASE_SET:
        _read_dir(root / _BASE_SET)      # base coverage
    _read_dir(ctx.set_dir())             # scenario overrides (by filename)

    return [merged[name] for name in sorted(merged)]


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
