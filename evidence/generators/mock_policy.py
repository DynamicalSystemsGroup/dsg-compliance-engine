"""Mocked policy-as-code check generator.

Reads the same ``fixtures/nv012/<set>/*.json`` exports but re-expresses a
subset as ``ce:PolicyCheck`` evidence (the OPA/Checkov/Trivy analogue): a
pass/fail check result derived from the fixture's machine-readable ``summary``.

It deliberately **overlaps** :class:`MockConfigExportGenerator` on
``AC.L2-3.1.1`` (IAM) so U6's coverage query sees two independent generators
addressing one control. Every artifact is ``evidentiary_status="mock"`` (R12).
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

# summary key -> (comparator, threshold) for deriving a PASS/FAIL check result.
# Mirrors the machine criteria in oracles/criteria.py for the checked controls.
_CHECK_METRICS = {
    "AC.L2-3.1.1": ("unauthorized_principals", "eq", 0),
    "SC.L2-3.13.1": ("data_region", "eq", "US"),
}


def _passes(metric_value, comparator: str, threshold) -> bool:
    if comparator == "eq":
        return metric_value == threshold
    return False


class MockPolicyCheckGenerator:
    """Emit PolicyCheck artifacts for the policy-as-code-checkable controls.

    Implements the :class:`Generator` protocol. For each fixture whose declared
    controls intersect :attr:`controls`, derive a PASS/FAIL result from the
    fixture ``summary`` and emit one ``ce:PolicyCheck`` artifact per checked
    control.
    """

    tool = "opa"
    controls: list[str] = ["AC.L2-3.1.1", "SC.L2-3.13.1"]

    def collect(self, ctx: GeneratorContext) -> list[EvidenceArtifact]:
        artifacts: list[EvidenceArtifact] = []
        for path, doc in _load_fixture_files(ctx):
            summary = doc.get("summary", {})
            fixture_controls = set(doc.get("controls", []))
            for control_id in self.controls:
                if control_id not in fixture_controls or control_id not in _CHECK_METRICS:
                    continue
                metric_key, comparator, threshold = _CHECK_METRICS[control_id]
                if metric_key not in summary:
                    continue
                value = summary[metric_key]
                ok = _passes(value, comparator, threshold)
                result = {
                    "status": "PASS" if ok else "FAIL",
                    "detail": f"{metric_key}={value!r} {comparator} {threshold!r}",
                    "metrics": {metric_key: value},
                }
                raw = {"tool": self.tool, "control": control_id, "result": result}
                artifacts.append(
                    EvidenceArtifact(
                        raw_bytes=json.dumps(raw, sort_keys=True).encode("utf-8"),
                        summary={metric_key: value},
                        controls=[control_id],
                        collection_metadata=_metadata_from_envelope(doc),
                        evidentiary_status=doc.get("evidentiary_status", "mock"),
                        method="policy-check",
                        source_file=str(path.relative_to(ctx.fixtures_root.parent)),
                        tool=self.tool,
                        result=result,
                    )
                )
        return artifacts


assert isinstance(MockPolicyCheckGenerator(), Generator)
