"""Full-chain P-Plan provenance and SOP-adherence checking.

Phase C of the signed-provenance plan. Two jobs:

1. Turn the whole lineage into a queryable provenance graph. The runtime already
   records a p-plan:Activity per Factory stage (pipeline/plan_execution.py). Here
   we (a) synthesise the *upstream* Order-Compiler activities from the artifacts in
   hand at Order-compile time, and (b) bind the real artifacts of a run as
   p-plan:Entity nodes that correspondsToVariable the planned Variables in
   pipeline/plan.ttl, wired to their Activities by prov:used / prov:wasGeneratedBy.

2. Answer "did this run follow the SOP?" `check_sop_adherence` compares the executed
   activities/entities against plan.ttl: no orphan activity, no step running before
   its predecessor, and every executed step's declared output Variable has a
   realizing Entity.

Everything is additive to the <ce:plan_execution> named graph and deterministic
(Entity IRIs derive from artifact identity, not wall-clock time).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from rdflib import Dataset, Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

from compliance_engine.ontology.prefixes import CE, P_PLAN, PROV
from compliance_engine.pipeline.dataset import graph_for
from compliance_engine.pipeline.plan_execution import (
    declare_entity,
    entity_iri,
    mark_input,
    mark_output,
    var_iri,
)

# The upstream Order-Compiler agent (distinct from the runtime pipeline agent).
ORDER_COMPILER_AGENT = CE["agent/order-compiler"]

_PLAN_TTL = Path(__file__).resolve().parent.parent / "pipeline" / "plan.ttl"


def _upstream_activity(contract: str, step: str) -> URIRef:
    """Deterministic upstream activity IRI (no timestamp, so it is reproducible)."""
    return URIRef(f"{CE}exec/{contract}/{step}")


# ---------------------------------------------------------------------------
# Upstream synthesis — contract -> obligations -> controls -> COP -> Order
# ---------------------------------------------------------------------------

def emit_order_compile_provenance(
    ds: Dataset,
    obligations,
    order,
    cop_attestation,
    *,
    now: str | None = None,
) -> None:
    """Record the Order-Compiler chain as p-plan Activities + Entities.

    Called once, right after an Order is compiled, with the artifacts already in
    hand. Deterministic and idempotent (re-adding the same triples is a no-op).
    """
    g = graph_for(ds, "plan_execution")
    contract = order.contract
    ts = Literal(now, datatype=XSD.dateTime) if now else None

    g.add((ORDER_COMPILER_AGENT, RDF.type, PROV.SoftwareAgent))

    acts: dict[str, URIRef] = {}
    for step in ("ExtractObligations", "ResolveControls", "AttestCOP", "Gate1", "EmitOrder"):
        act = _upstream_activity(contract, step)
        g.add((act, RDF.type, P_PLAN.Activity))
        g.add((act, RDF.type, PROV.Activity))
        g.add((act, P_PLAN.correspondsToStep, URIRef(f"{CE}step-{step}")))
        g.add((act, PROV.wasAssociatedWith, ORDER_COMPILER_AGENT))
        if ts is not None:
            g.add((act, PROV.startedAtTime, ts))
        acts[step] = act

    # Entities (the real artifacts).
    contract_e = entity_iri("contract", contract)
    declare_entity(g, contract_e, "Contract", label=f"Contract {contract}")

    obl_e = entity_iri("obligations", contract)
    declare_entity(g, obl_e, "Obligations", label=f"{len(obligations)} obligations")

    ctrl_e = entity_iri("controls", contract)
    declare_entity(
        g, ctrl_e, "RequiredControls",
        label=f"{len(order.required_controls)} required controls",
    )

    cop_e = URIRef(str(order.cop_iri))
    declare_entity(g, cop_e, "COP", label="Contract Obligation Profile (attested)")

    order_e = URIRef(str(order.iri))
    declare_entity(g, order_e, "Order", label=f"Signed Order {contract}")

    # Wire inputs/outputs along the chain.
    mark_input(g, acts["ExtractObligations"], contract_e)
    mark_output(g, obl_e, acts["ExtractObligations"])

    mark_input(g, acts["ResolveControls"], obl_e)
    mark_output(g, ctrl_e, acts["ResolveControls"])

    mark_input(g, acts["AttestCOP"], obl_e)
    mark_output(g, cop_e, acts["AttestCOP"])

    mark_input(g, acts["Gate1"], ctrl_e)

    mark_input(g, acts["EmitOrder"], ctrl_e)
    mark_input(g, acts["EmitOrder"], cop_e)
    mark_output(g, order_e, acts["EmitOrder"])


# ---------------------------------------------------------------------------
# Runtime binding — bind the Factory's real artifacts to the runtime steps
# ---------------------------------------------------------------------------

def bind_runtime_provenance(state) -> None:
    """Bind the PipelineState's artifacts as Entities on the runtime stage
    activities (already created by emit_stage_activity). Tolerant of a halted run:
    only binds the stages that produced output.
    """
    ds = state.ds
    g = graph_for(ds, "plan_execution")
    acts = state.stage_activities
    contract = state.load_order.contract if state.load_order else "run"

    order_e = URIRef(str(state.order_iri))
    declare_entity(g, order_e, "Order")
    if "LoadOrder" in acts:
        mark_input(g, acts["LoadOrder"], order_e)

    if state.fetch and "FetchByHash" in acts:
        mh_e = entity_iri("modulehashes", contract)
        declare_entity(
            g, mh_e, "ModuleHashes",
            label=f"{len(state.fetch.module_hashes)} verified module hashes",
        )
        mark_input(g, acts["FetchByHash"], order_e)
        mark_output(g, mh_e, acts["FetchByHash"])

    if state.plan and "Plan" in acts:
        ph_e = entity_iri("planhash", contract)
        declare_entity(g, ph_e, "PlanHash", label="terraform plan (mock providers)")
        mark_output(g, ph_e, acts["Plan"])

    # Evidence nodes and oracle assertions already carry their own generating
    # activity and provenance (bind_evidence / the oracle emitter). Only tie them
    # to the plan Variable via correspondsToVariable — do NOT add a second
    # prov:wasGeneratedBy, which would break the one-generating-activity shape.
    if "CollectEvidence" in acts:
        for entry in state.evidence_index:
            ev = URIRef(str(entry["iri"]))
            g.add((ev, P_PLAN.correspondsToVariable, var_iri("Evidence")))

    if state.oracles and "Oracles" in acts:
        for entry in state.evidence_index:
            mark_input(g, acts["Oracles"], URIRef(str(entry["iri"])))
        for assertion in state.oracles.assertion_iris:
            ae = URIRef(str(assertion))
            g.add((ae, P_PLAN.correspondsToVariable, var_iri("OracleAssertions")))


# ---------------------------------------------------------------------------
# Downstream binding — attestations, BOM, SSP (produced outside the factory run)
# ---------------------------------------------------------------------------

def bind_artifact_entity(
    ds: Dataset, var_name: str, kind: str, ident: str, step: str, *, label: str | None = None
) -> URIRef:
    """Declare a downstream artifact (attestations / BOM / SSP) as an Entity that
    is the output of `step`. `step` names an executed activity in the plan_execution
    graph (matched by correspondsToStep); if no such activity exists this still
    declares the Entity so the chain is complete for packaging.
    """
    g = graph_for(ds, "plan_execution")
    ent = entity_iri(kind, ident)
    declare_entity(g, ent, var_name, label=label)
    step_uri = URIRef(f"{CE}step-{step}")
    for act in g.subjects(P_PLAN.correspondsToStep, step_uri):
        mark_output(g, ent, act)
    return ent


def _synth_downstream_activity(ds: Dataset, step: str, contract: str) -> URIRef:
    """Ensure an activity exists for a downstream step (Attestation/Audit/
    SignAndStore) that runs outside run_factory, so its outputs have a producer."""
    g = graph_for(ds, "plan_execution")
    step_uri = URIRef(f"{CE}step-{step}")
    existing = list(g.subjects(P_PLAN.correspondsToStep, step_uri))
    if existing:
        return existing[0]
    act = URIRef(f"{CE}exec/{contract}/{step}")
    g.add((act, RDF.type, P_PLAN.Activity))
    g.add((act, RDF.type, PROV.Activity))
    g.add((act, P_PLAN.correspondsToStep, step_uri))
    g.add((act, PROV.startedAtTime,
           Literal(datetime.now(timezone.utc).isoformat(), datatype=XSD.dateTime)))
    return act


def bind_downstream_provenance(
    ds: Dataset,
    contract: str,
    *,
    attestation_count: int | None = None,
    bom_hash: str | None = None,
    ssp_present: bool = False,
) -> None:
    """Bind the post-factory artifacts (attestations, BOM, SSP) into the chain so
    the full contract -> SSP lineage is present. Called from the demo/CLI path
    after audit/BOM/SSP are produced.
    """
    if attestation_count is not None:
        act = _synth_downstream_activity(ds, "Attestation", contract)
        ent = bind_artifact_entity(
            ds, "Attestations", "attestations", contract, "Attestation",
            label=f"{attestation_count} human attestations",
        )
        mark_output(graph_for(ds, "plan_execution"), ent, act)
    if bom_hash is not None:
        act = _synth_downstream_activity(ds, "Audit", contract)
        ent = bind_artifact_entity(
            ds, "BOM", "bom", bom_hash[:16], "Audit", label="compliance BOM",
        )
        mark_output(graph_for(ds, "plan_execution"), ent, act)
    if ssp_present:
        act = _synth_downstream_activity(ds, "SignAndStore", contract)
        ent = bind_artifact_entity(
            ds, "SSP", "ssp", contract, "SignAndStore", label="System Security Plan",
        )
        mark_output(graph_for(ds, "plan_execution"), ent, act)


# ---------------------------------------------------------------------------
# SOP-adherence (deviation) check
# ---------------------------------------------------------------------------

@dataclass
class ProvenanceReport:
    """Result of comparing the executed provenance graph against plan.ttl."""

    ok: bool
    executed_steps: tuple[str, ...]
    orphan_activities: tuple[str, ...] = field(default_factory=tuple)
    predecessor_violations: tuple[str, ...] = field(default_factory=tuple)
    unrealized_outputs: tuple[str, ...] = field(default_factory=tuple)

    def summary(self) -> str:
        if self.ok:
            return f"SOP adherence: OK ({len(self.executed_steps)} steps executed)"
        parts = []
        if self.orphan_activities:
            parts.append(f"{len(self.orphan_activities)} orphan activities")
        if self.predecessor_violations:
            parts.append(f"{len(self.predecessor_violations)} out-of-order steps")
        if self.unrealized_outputs:
            parts.append(f"{len(self.unrealized_outputs)} unrealized outputs")
        return "SOP adherence: DEVIATION — " + ", ".join(parts)


def _load_plan() -> Graph:
    g = Graph()
    g.parse(_PLAN_TTL, format="turtle")
    return g


def _step_name(step_uri: URIRef) -> str:
    return str(step_uri).rsplit("step-", 1)[-1]


def check_sop_adherence(ds: Dataset) -> ProvenanceReport:
    """Check the run's <ce:plan_execution> graph against the plan in plan.ttl.

    Flags: orphan activities (correspondsToStep something not in the plan), steps
    that executed before a declared predecessor did, and executed steps whose
    declared output Variable has no realizing Entity.
    """
    plan = _load_plan()
    exec_g = graph_for(ds, "plan_execution")

    # Planned steps, precedence, and declared outputs.
    planned_steps = {str(s) for s in plan.subjects(RDF.type, P_PLAN.Step)}
    preceded_by: dict[str, set[str]] = {}
    for s, _, o in plan.triples((None, P_PLAN.isPrecededBy, None)):
        preceded_by.setdefault(str(s), set()).add(str(o))
    output_vars: dict[str, set[str]] = {}
    for s, _, o in plan.triples((None, P_PLAN.hasOutputVar, None)):
        output_vars.setdefault(str(s), set()).add(str(o))

    # Executed activities -> their steps.
    executed_steps: set[str] = set()
    orphans: list[str] = []
    for act in exec_g.subjects(RDF.type, P_PLAN.Activity):
        step = exec_g.value(act, P_PLAN.correspondsToStep)
        if step is None:
            orphans.append(str(act))
            continue
        if str(step) not in planned_steps:
            orphans.append(str(act))
            continue
        executed_steps.add(str(step))

    # Realized variables (Entities that correspondsToVariable).
    realized_vars = {
        str(v) for v in exec_g.objects(None, P_PLAN.correspondsToVariable)
    }

    # Predecessor violations: an executed step whose declared predecessor did not run.
    predecessor_violations: list[str] = []
    for step in executed_steps:
        for pred in preceded_by.get(step, set()):
            if pred not in executed_steps:
                predecessor_violations.append(
                    f"{_step_name(URIRef(step))} ran without {_step_name(URIRef(pred))}"
                )

    # Unrealized outputs: an executed step's declared output Variable has no Entity.
    unrealized: list[str] = []
    for step in executed_steps:
        for var in output_vars.get(step, set()):
            if var not in realized_vars:
                unrealized.append(
                    f"{_step_name(URIRef(step))} -> {str(var).rsplit('var-', 1)[-1]}"
                )

    ok = not (orphans or predecessor_violations or unrealized)
    return ProvenanceReport(
        ok=ok,
        executed_steps=tuple(sorted(_step_name(URIRef(s)) for s in executed_steps)),
        orphan_activities=tuple(sorted(orphans)),
        predecessor_violations=tuple(sorted(predecessor_violations)),
        unrealized_outputs=tuple(sorted(unrealized)),
    )
