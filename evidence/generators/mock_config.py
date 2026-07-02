"""Mocked live-config export generator.

Reads the ``fixtures/nv012/<set>/*.json`` exports (shaped like real GCP /
Workspace config exports) and turns each into a ``ce:ConfigExport``
``EvidenceArtifact`` that **addresses** the control(s) named in the fixture.

This is the fixture-backed stand-in for the real config-export path (Workspace
2SV policy, GCP Org Policy, IAM bindings, Key Vault + CMVP cert, ...). Every
artifact is ``evidentiary_status="mock"`` (R12).
"""

from __future__ import annotations

import json

from evidence.generators import (
    EvidenceArtifact,
    Generator,
    GeneratorContext,
    _load_fixture_files,
    _metadata_from_envelope,
)


class MockConfigExportGenerator:
    """Emit one ConfigExport artifact per fixture export in the selected set.

    Implements the :class:`Generator` protocol. ``controls`` lists every control
    this path can address; the actual per-run set is whatever the fixtures
    present (so the ``gap`` set — missing the FIPS export — yields no evidence
    for ``SC.L2-3.13.11``, which is exactly what drives the U13 Gate-1 refusal).
    """

    # The live-config-export controls (Tier-1 mapping; see criteria.py).
    controls: list[str] = [
        "IA.L2-3.5.3",     # MFA enforced (workspace.2sv)
        "SC.L2-3.13.11",   # FIPS module present (gcp.kms + CMVP)
        "SC.L2-3.13.16",   # CUI encrypted at rest (gcp.storage CMEK)
        "AC.L2-3.1.1",     # no unauthorized principals (gcp.iam)
        "ITAR-120.54",     # data residency US-only (gcp.org_policy)
    ]

    def collect(self, ctx: GeneratorContext) -> list[EvidenceArtifact]:
        artifacts: list[EvidenceArtifact] = []
        for path, doc in _load_fixture_files(ctx):
            raw = doc.get("raw", {})
            artifacts.append(
                EvidenceArtifact(
                    raw_bytes=json.dumps(raw, sort_keys=True).encode("utf-8"),
                    summary=doc.get("summary", {}),
                    controls=list(doc.get("controls", [])),
                    collection_metadata=_metadata_from_envelope(doc),
                    evidentiary_status=doc.get("evidentiary_status", "mock"),
                    method="config-export",
                    source_file=str(path.relative_to(ctx.fixtures_root.parent)),
                )
            )
        return artifacts


# Protocol conformance smoke check (no cost at import beyond isinstance).
assert isinstance(MockConfigExportGenerator(), Generator)
