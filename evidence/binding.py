"""Bind hashed evidence into the ``<ce:evidence>`` graph.

Creates ``ce:Evidence`` nodes (subtypes ``ce:ConfigExport`` / ``ce:PolicyCheck``)
linked to:
- the collection activity that produced them (``prov:wasGeneratedBy`` → a
  ``CollectEvidence`` step activity),
- the control(s) they **address** (``ce:addresses`` → a ``cmmc:Control``).

Core principle (regression-tested): evidence **addresses** a control, it never
**attests** one. This module NEVER emits ``ce:attests`` / ``ce:hasOutcome`` —
those belong to attestation (U9). Fixture-sourced evidence is flagged
``ce:evidentiaryStatus "mock"`` (R12).

Adapted from ``ADCS-lifecycle-demo/evidence/binding.py``. The ADCS compute
``ExecutionMetadata`` type is dropped; ``_bind_execution_metadata`` is rewritten
against the ``CollectionMetadata`` dataclass below (where/how a config export
was collected).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

from ontology.prefixes import CE, CMMC, PROV, P_PLAN
from pipeline.plan_execution import step_iri

from evidence.hashing import hash_check_result, hash_config_export, hash_evidence

if TYPE_CHECKING:
    from evidence.generators import EvidenceArtifact

_SLUG_RE = re.compile(r"[^A-Za-z0-9]+")


def _slug(text: str) -> str:
    """Stable slug for IRI construction (deterministic — no timestamps)."""
    return _SLUG_RE.sub("-", text).strip("-").lower() or "x"


@dataclass(frozen=True)
class CollectionMetadata:
    """How/where a live-config export was collected.

    Replaces the ADCS compute ``ExecutionMetadata``: there is no container /
    host / image here — a config export is pulled from a cloud/tenant API. The
    four fields answer "which system, via what command, when, with what
    collector version" — the audit trail for a mocked-then-real generator run.
    """

    source_system: str        # e.g. "workspace.2sv", "gcp.kms", "gcp.iam"
    export_command: str       # the (illustrative) command that produced the export
    collected_at: str         # ISO-8601 timestamp (xsd:dateTime)
    collector_version: str    # mock/real collector version

    def collector_uri(self) -> URIRef:
        """Stable IRI for the collector software agent."""
        return CE[f"collector/{_slug(self.source_system)}"]


def _bind_execution_metadata(
    graph: Graph,
    activity_uri: URIRef,
    metadata: CollectionMetadata | None,
) -> None:
    """Attach collection-context PROV triples to a CollectEvidence activity.

    Records WHICH system produced the export (source_system), HOW
    (export_command), WHEN (collected_at), and the collector agent + its
    version. This is the compliance analogue of the ADCS "which machine /
    toolchain produced this proof" provenance.

    Emitted shape::

        <activity>
            prov:wasAssociatedWith <ce:collector/...> ;
            ce:sourceSystem "..." ;
            ce:exportCommand "..." ;
            ce:collectedAt "..."^^xsd:dateTime .

        <ce:collector/...> a prov:SoftwareAgent ;
            ce:collectorVersion "..." ;
            rdfs:label "..." .
    """
    if metadata is None:
        return

    collector = metadata.collector_uri()
    graph.add((activity_uri, PROV.wasAssociatedWith, collector))
    graph.add((activity_uri, CE.sourceSystem, Literal(metadata.source_system)))
    graph.add((activity_uri, CE.exportCommand, Literal(metadata.export_command)))
    if metadata.collected_at:
        graph.add((activity_uri, CE.collectedAt,
                   Literal(metadata.collected_at, datatype=XSD.dateTime)))

    graph.add((collector, RDF.type, PROV.SoftwareAgent))
    graph.add((collector, CE.collectorVersion, Literal(metadata.collector_version)))
    graph.add((collector, RDFS.label,
               Literal(f"{metadata.source_system} collector {metadata.collector_version}")))


def _summary_text(summary: dict) -> str:
    """Deterministic human-readable rendering of a metric summary dict."""
    if not summary:
        return "no machine-readable metrics"
    return "; ".join(f"{k}={summary[k]!r}" for k in sorted(summary))


def _bind_activity(graph: Graph, activity_uri: URIRef,
                   metadata: CollectionMetadata | None) -> None:
    """Emit the CollectEvidence collection activity node.

    Typed ``prov:Activity`` and pinned to the ``CollectEvidence`` plan step via
    ``p-plan:correspondsToStep`` (so rerun/audit can walk evidence → activity →
    step → stage). Deliberately NOT typed ``p-plan:Activity`` here: the plan
    graph (which types the step) is a separate named graph, so we avoid the
    plan-instantiation shape firing on an evidence-graph-only validation.
    """
    graph.add((activity_uri, RDF.type, PROV.Activity))
    graph.add((activity_uri, P_PLAN.correspondsToStep, step_iri("CollectEvidence")))
    if metadata is not None and metadata.collected_at:
        graph.add((activity_uri, PROV.startedAtTime,
                   Literal(metadata.collected_at, datatype=XSD.dateTime)))
    _bind_execution_metadata(graph, activity_uri, metadata)


def _bind_evidence_common(
    graph: Graph,
    ev_uri: URIRef,
    act_uri: URIRef,
    *,
    subtype: URIRef,
    content_hash: str,
    model_hash: str,
    controls: list[str],
    result_summary: str,
    source_file: str,
    evidentiary_status: str,
    metadata: CollectionMetadata | None,
) -> None:
    """Shared triple emission for both evidence subtypes."""
    graph.add((ev_uri, RDF.type, CE.Evidence))
    graph.add((ev_uri, RDF.type, subtype))
    graph.add((ev_uri, RDF.type, PROV.Entity))
    graph.add((ev_uri, CE.contentHash, Literal(content_hash)))
    graph.add((ev_uri, CE.modelHash, Literal(model_hash)))
    graph.add((ev_uri, CE.resultSummary, Literal(result_summary)))
    graph.add((ev_uri, CE.sourceFile, Literal(source_file)))
    graph.add((ev_uri, CE.documentRef, Literal(f"registry://evidence/{content_hash}")))
    # R12 — fixture-sourced evidence is non-evidentiary; mark it as such.
    graph.add((ev_uri, CE.evidentiaryStatus, Literal(evidentiary_status)))
    # Evidence ADDRESSES controls — never attests them (core principle).
    for control_id in controls:
        graph.add((ev_uri, CE.addresses, CMMC[control_id]))
    graph.add((ev_uri, PROV.wasGeneratedBy, act_uri))
    if metadata is not None and metadata.collected_at:
        graph.add((ev_uri, PROV.generatedAtTime,
                   Literal(metadata.collected_at, datatype=XSD.dateTime)))

    _bind_activity(graph, act_uri, metadata)


def _iris(evidence_id: str | None, content_hash: str) -> tuple[URIRef, URIRef]:
    """Derive deterministic (evidence, activity) IRIs.

    Default keys off the content hash, so re-binding identical evidence is
    idempotent (same node) — the write-once registry invariant.
    """
    key = evidence_id or content_hash[:16]
    return CE[f"evidence/{key}"], CE[f"exec/CollectEvidence-{key}"]


def bind_config_evidence(
    graph: Graph,
    artifact: "EvidenceArtifact",
    *,
    evidence_id: str | None = None,
) -> URIRef:
    """Bind a live-config export as a ``ce:ConfigExport`` evidence node.

    ``content_hash`` chains the ADCS way: the config export is the *model*
    (``model_hash = hash_config_export(...)``); the combined evidence hash is
    ``content_hash = hash_evidence(model_hash)``.

    Returns the evidence node IRI.
    """
    md = artifact.collection_metadata
    config = json.loads(artifact.raw_bytes.decode("utf-8"))
    control0 = artifact.controls[0] if artifact.controls else ""
    model_hash = hash_config_export(md.source_system, control0, config)
    content_hash = hash_evidence(model_hash)

    ev_uri, act_uri = _iris(evidence_id, content_hash)
    _bind_evidence_common(
        graph, ev_uri, act_uri,
        subtype=CE.ConfigExport,
        content_hash=content_hash,
        model_hash=model_hash,
        controls=artifact.controls,
        result_summary=f"config export from {md.source_system}: "
                       f"{_summary_text(artifact.summary)}",
        source_file=artifact.source_file or md.source_system,
        evidentiary_status=artifact.evidentiary_status,
        metadata=md,
    )
    return ev_uri


def bind_check_evidence(
    graph: Graph,
    artifact: "EvidenceArtifact",
    *,
    evidence_id: str | None = None,
) -> URIRef:
    """Bind a policy-as-code check result as a ``ce:PolicyCheck`` evidence node.

    ``model_hash = hash_check_result(tool, control, result)``;
    ``content_hash = hash_evidence(model_hash)``.

    Returns the evidence node IRI.
    """
    md = artifact.collection_metadata
    control0 = artifact.controls[0] if artifact.controls else ""
    tool = artifact.tool or "opa"
    result = artifact.result if artifact.result is not None else {
        "status": "PASS", "detail": _summary_text(artifact.summary),
        "metrics": artifact.summary,
    }
    model_hash = hash_check_result(tool, control0, result)
    content_hash = hash_evidence(model_hash)

    ev_uri, act_uri = _iris(evidence_id, content_hash)
    _bind_evidence_common(
        graph, ev_uri, act_uri,
        subtype=CE.PolicyCheck,
        content_hash=content_hash,
        model_hash=model_hash,
        controls=artifact.controls,
        result_summary=f"{tool} check ({result.get('status', '?')}) for "
                       f"{control0}: {_summary_text(artifact.summary)}",
        source_file=artifact.source_file or md.source_system,
        evidentiary_status=artifact.evidentiary_status,
        metadata=md,
    )
    return ev_uri


def bind_evidence(
    graph: Graph,
    artifact: "EvidenceArtifact",
    *,
    evidence_id: str | None = None,
) -> URIRef:
    """Dispatch on ``artifact.method`` to the right binder.

    ``"policy-check"`` → :func:`bind_check_evidence`; anything else (default
    ``"config-export"``) → :func:`bind_config_evidence`.
    """
    if artifact.method == "policy-check":
        return bind_check_evidence(graph, artifact, evidence_id=evidence_id)
    return bind_config_evidence(graph, artifact, evidence_id=evidence_id)
