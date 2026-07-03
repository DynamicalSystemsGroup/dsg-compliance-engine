"""Adapter layer between the marimo walkthrough notebook and the real engine.

The notebook is a *viewport* onto the running compliance engine, not a fork of it.
Every function here calls the same code the operator CLI (`ce`, i.e.
`compliance_engine.cli`) calls — it just exposes each stage at a finer grain and
returns plain data (dicts / dataclasses / engine objects) so the notebook cells
can render the intermediate artifacts.

Nothing in this module builds UI. It is import-safe and unit-testable on its own:
`run_pipeline(scenario)` drives the whole chain and returns a structured record.

Path setup: importing this module puts `src/` on the path, then imports
`compliance_engine.cli`, which is the single source of truth for how the stages
wire together over one shared rdflib Dataset with a fixed run seed for determinism.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

# --- make the engine importable regardless of the caller's working directory ---
_REPO_ROOT = Path(__file__).resolve().parent.parent
_src = str(_REPO_ROOT / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from compliance_engine import cli  # noqa: E402
from compliance_engine.order_compiler import compiler  # noqa: E402
from compliance_engine.order_compiler import cop  # noqa: E402
from compliance_engine.order_compiler import gate1  # noqa: E402
from compliance_engine.order_compiler import rule_library as rl  # noqa: E402
from compliance_engine.pipeline.dataset import export_trig, triples_by_graph  # noqa: E402
from compliance_engine.ontology.prefixes import NAMED_GRAPHS  # noqa: E402

# --- constants pulled straight from the CLI so the notebook can't drift from it ---
SCENARIOS: tuple[str, ...] = cli.EVIDENCE_SETS          # ("all-covered", "gap", "contradiction")
SEED: str = cli.RUN_SEED_TS                             # fixed timestamp → deterministic hashes
GAP_CONTROL: str = cli._GAP_CONTROL                     # the required-but-unclaimed control


class _UnknownControlAsGate1Report:
    """Minimal Gate1Report shim for the "unknown control id" refusal path.

    Provides just enough surface (`.passed`, `.gap_controls()`) for callers
    that treat a Gate 1 refusal uniformly. The real path is exercised by
    tests/test_gate1.py; here we only need the message to flow through.
    """

    def __init__(self, message: str) -> None:
        self._message = message
        self.passed = False

    def gap_controls(self) -> list[str]:
        return [GAP_CONTROL]

    def render(self) -> str:
        return f"Gate 1 REFUSED (unknown control id): {self._message}"
CONTRACT_ID: str = cli.CONTRACT_ID                      # "NV012"

# The eight named-graph layers, in the order data flows through them.
LAYER_ORDER: tuple[str, ...] = (
    "ontology", "plan", "structural", "order",
    "evidence", "attestations", "plan_execution", "audit",
)


# ---------------------------------------------------------------------------
# Stage 0 — build the shared dataset for a scenario
# ---------------------------------------------------------------------------

def check_scenario(scenario: str) -> None:
    """Raise a clear error for an unknown scenario (instead of a downstream KeyError)."""
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario must be one of {SCENARIOS!r}, got {scenario!r}")


def build_dataset(scenario: str):
    """Fresh `(ds, obligations)` for a scenario — the single reactive root.

    Rebuilds from the committed catalog/structural/COP fixtures each call, so
    switching scenarios never leaks stale state. For the `gap` scenario we inject
    a required-but-unclaimed control exactly as `cli._do_compile` does, so Gate 1
    has a real hole to refuse on.
    """
    check_scenario(scenario)
    ds, obligations = compiler.load_pipeline_dataset()
    obligations = dict(obligations)
    if scenario == "gap":
        obligations["OBL-DEMO-GAP"] = rl.Obligation(
            "OBL-DEMO-GAP", rl.DATA, derives=frozenset({GAP_CONTROL})
        )
    return ds, obligations


# ---------------------------------------------------------------------------
# Stages 1–2 — obligations → required controls
# ---------------------------------------------------------------------------

def obligation_rows(obligations: dict[str, Any]) -> list[dict[str, Any]]:
    """Per-obligation view of the contract: type, data marker, and the controls
    it resolves to via `rule_library.resolve` (the real resolver the compiler uses).
    """
    rows: list[dict[str, Any]] = []
    for name, obl in sorted(obligations.items()):
        row: dict[str, Any] = {
            "obligation": name,
            "type": obl.obligation_type,
            "data_marker": obl.data_marker or "",
            "controls": [],
            "note": "",
        }
        try:
            controls = rl.resolve(obl)
            row["controls"] = sorted(controls)
            markers = sorted(getattr(controls, "markers", ()) or ())
            if markers:
                row["note"] = "policy markers: " + ", ".join(markers)
        except rl.SpilloverReviewRequired:
            row["note"] = "CUI/ITAR deliverable — requires explicit spillover ack"
        except rl.UnknownControlError:
            # The `gap` scenario injects an obligation citing a control that is not
            # in the catalog. Surface it as a note rather than crashing the view;
            # Gate 1 is where the refusal is meant to land.
            row["note"] = "cites a control outside the 110-control catalog — Gate 1 refuses"
        rows.append(row)
    return rows


def required_control_set(obligations: dict[str, Any]) -> tuple[list[str], list[str]]:
    """The authoritative required-control union + policy markers the Order is built
    from (`compiler.resolve_required_controls`). Sorted for stable display.

    For the `gap` scenario, an obligation cites a non-catalog control id so
    the resolver raises UnknownControlError before Gate 1. Return an empty
    required set with a synthetic marker so downstream callers still get a
    well-shaped tuple; compile_order_or_refusal produces the refusal.
    """
    try:
        required, markers = compiler.resolve_required_controls(obligations)
    except rl.UnknownControlError:
        return [], []
    return sorted(required), sorted(markers)


# ---------------------------------------------------------------------------
# Stage 3 — COP attestation (AI drafts / human attests)
# ---------------------------------------------------------------------------

def attest_cop_step(ds, obligations: dict[str, Any]):
    """Attest the Contract Obligation Profile. `auto=True` records the AI-assisted
    (`earl:semiAuto`) path used by the demo; a real run would be `earl:manual`.
    Returns the `COPAttestation`.
    """
    return cop.attest_cop(ds, obligations, auto=True, now=SEED)


# ---------------------------------------------------------------------------
# Stage 4 — Gate 1 (planning coverage) preview
# ---------------------------------------------------------------------------

def gate1_preview(required: list[str], ds):
    """Run the real Gate 1 check and return its `Gate1Report` (forward / backward /
    untestable, plus `gap_controls()` / `orphan_modules()` / `paper_claim_modules()`).
    This is the same `run_gate1` the compiler runs authoritatively at Stage 5.
    """
    return gate1.run_gate1(set(required), ds)


# ---------------------------------------------------------------------------
# Stage 5 — compile the signed Order (or catch Gate 1's refusal)
# ---------------------------------------------------------------------------

def compile_order_or_refusal(ds, obligations: dict[str, Any], cop_attestation):
    """Return `(order, None)` on success, or `(None, gate1_report)` when Gate 1
    refuses (the `gap` scenario). Mirrors `cli._do_compile`'s refusal handling.
    """
    try:
        order = compiler.compile_order(ds, obligations, cop_attestation, now=SEED)
        return order, None
    except compiler.Gate1Failed as exc:
        return None, exc.report
    except rl.UnknownControlError as exc:
        # The gap demo cites a syntactically-valid but non-catalog control id
        # so the rule_library's pre-Gate-1 validator raises. Return it as a
        # Gate1Failed-shaped shim so downstream callers can treat it as a
        # refusal uniformly.
        return None, _UnknownControlAsGate1Report(str(exc))


# ---------------------------------------------------------------------------
# Stage 6–9 — thin pass-throughs to the CLI's stage helpers (identical wiring)
# ---------------------------------------------------------------------------

def new_output_dir() -> Path:
    """A throwaway temp dir for run artifacts — never the repo's own `output/`."""
    return Path(tempfile.mkdtemp(prefix="ce-notebook-"))


def run_factory_step(ds, order, scenario: str, output_dir: Path):
    """Stage 6 — the Factory: fetch-by-hash → plan → policy → mock apply → evidence
    → oracles. Returns the populated `PipelineState`. Uses the fake provisioner
    (no terraform binary, no cloud), exactly like the default demo.
    """
    return cli._do_run_factory(ds, order.iri, scenario, "fake", output_dir)


def attest_step(ds, state) -> int:
    """Stage 7 — Gate 2: auto-attest MET across the full required set, carrying the
    real oracle outcome so a MET-over-failed-oracle surfaces as a contradiction.
    Returns the number of controls attested.
    """
    return cli._do_attest(ds, state)


def audit_step(ds, output_dir: Path):
    """Stage 8 — bidirectional audit + SPRS. Returns the `AuditReport`
    (`.sprs`, `.proven`, `.contradictions`, forward/backward).
    """
    return cli._do_audit(ds, output_dir)


def bom_step(state, ds, output_dir: Path):
    """Stage 9a — assemble + store the content-addressed BOM. Returns the `BOM`."""
    return cli._do_bom(state, ds, output_dir)


def save_dataset(ds, output_dir: Path) -> Path:
    """Persist the whole `<ce:*>` dataset as TriG (so the SSP's fingerprint path
    resolves). Returns the file path.
    """
    path = output_dir / "engine.trig"
    export_trig(ds, path)
    return path


def ssp_step(ds, audit_report, bom, output_dir: Path) -> str:
    """Stage 9b — render the deterministic, byte-stable SSP markdown (with the
    forced NON-EVIDENTIARY banner for mock runs). Returns the markdown string.
    """
    from compliance_engine.documents.ssp import compile_ssp_from_run
    dataset_path = save_dataset(ds, output_dir)
    return compile_ssp_from_run(
        ds, audit_report=audit_report, bom=bom, dataset_path=dataset_path
    )


# ---------------------------------------------------------------------------
# Substrate inspection
# ---------------------------------------------------------------------------

def named_graph_counts(ds) -> list[dict[str, Any]]:
    """Per-layer triple counts across the eight `<ce:*>` named graphs, in flow order.
    Returns `[{layer, iri, triples}, ...]`.
    """
    raw = triples_by_graph(ds)  # {graph_iri_str: count}
    by_iri = {str(iri): name for name, iri in NAMED_GRAPHS.items()}
    rows: list[dict[str, Any]] = []
    for layer in LAYER_ORDER:
        iri = str(NAMED_GRAPHS[layer])
        rows.append({"layer": layer, "iri": iri, "triples": int(raw.get(iri, 0))})
    # surface any populated graph not in the canonical eight (defensive)
    for iri, count in raw.items():
        if iri not in {str(NAMED_GRAPHS[l]) for l in LAYER_ORDER}:
            rows.append({"layer": by_iri.get(iri, "(other)"), "iri": iri, "triples": int(count)})
    return rows


# ---------------------------------------------------------------------------
# Structural model — how each of the 110 controls is verified
# ---------------------------------------------------------------------------
#
# Every fact below is read from the graph at call time (tier1.ttl + references.ttl
# + the attestation-refs vocabulary), never hardcoded. The *kind* of verification
# for a control is derived purely from its claiming module's cmmc:verificationMethod:
#   - an  ce:oracle-attested-reference  IRI  -> "attested"  (Track B: reference into
#     an authoritative source, signed by a role)
#   - any other ce:oracle-* IRI               -> "machine"   (Track A / Tier-1:
#     config-check oracle over a config export)
#   - an  "inherited:…"  literal              -> "inherited" (CSP handles it)

# The 6 non-deferrable 1-point controls (cannot be on POA&M even though weight=1).
_NON_DEF_ONE_POINTERS: frozenset[str] = frozenset({
    "AC.L2-3.1.20", "AC.L2-3.1.22", "CA.L2-3.12.4",
    "PE.L2-3.10.3", "PE.L2-3.10.4", "PE.L2-3.10.5",
})

# Verification kinds, with the plain labels the notebook prints.
KIND_LABEL: dict[str, str] = {
    "machine": "Machine-verified",
    "attested": "Attested-reference",
    "inherited": "CSP-inherited",
    "unclaimed": "Unclaimed",
}


def _cid(node: Any) -> str:
    """Bare control id from a cmmc: IRI (e.g. cmmc:AC.L2-3.1.1 -> AC.L2-3.1.1)."""
    return str(node).split("#")[-1].split("/")[-1]


def _freshness_label(days: int) -> str:
    """Plain-English name for a freshness window in days."""
    return {
        0: "event-based (per event)",
        30: "monthly",
        90: "quarterly",
        180: "semi-annual",
        365: "annual",
    }.get(days, f"every {days} days")


def _load_structural_graph():
    """tier1.ttl (module topology) + references.ttl + the attestation-refs
    vocabulary, merged into one Graph so module -> reference -> source -> role
    resolves in a single pass. Read-only; independent of any pipeline run.
    """
    from rdflib import Graph

    g = Graph()
    g.parse(_REPO_ROOT / "data" / "structural" / "tier1.ttl", format="turtle")
    g.parse(_REPO_ROOT / "data" / "structural" / "references.ttl", format="turtle")
    g.parse(_REPO_ROOT / "data" / "ontology" / "ce-attestation-refs.ttl", format="turtle")
    return g


def _module_verification_kind(g, module) -> str:
    """Classify one module by its cmmc:verificationMethod (see module header)."""
    from compliance_engine.ontology.prefixes import CMMC

    vm = g.value(module, CMMC.verificationMethod)
    vm_str = str(vm) if vm is not None else ""
    if vm_str.endswith("oracle-attested-reference"):
        return "attested"
    if vm_str.startswith("inherited"):
        return "inherited"
    return "machine"


def get_reference_data() -> list[dict[str, Any]]:
    """The attested-reference records: for every Track B control, the full chain
    the attested-reference oracle checks — authoritative source, resolvable
    reference URI, freshness window, last-verified timestamp, custodian ("bob"),
    and the required signer role.

    Returns one row per control, sorted by family then id. This is the concrete
    face of the attested-reference model: the same four-part check (registered,
    resolves, fresh, signed-by-role) that lets the engine cover policy-and-records
    controls on the same footing as machine ones.
    """
    from compliance_engine.ontology.prefixes import CE, CMMC
    from rdflib import RDFS

    g = _load_structural_graph()
    rows: list[dict[str, Any]] = []

    for module in g.subjects(CMMC.verificationMethod, CE["oracle-attested-reference"]):
        module_label = str(g.value(module, RDFS.label) or _cid(module))
        controls = sorted(_cid(c) for c in g.objects(module, CMMC.controlsSatisfied))

        src = g.value(module, CE.authoritativeSource)
        src_label = str(g.value(src, RDFS.label) or _cid(src)) if src else ""
        src_comment = str(g.value(src, RDFS.comment) or "") if src else ""

        ref = g.value(module, CE.reference)
        uri = str(g.value(ref, CE.uri) or "") if ref else ""
        try:
            fresh_days = int(str(g.value(ref, CE.freshnessDays) or "0")) if ref else 0
        except (ValueError, TypeError):
            fresh_days = 0
        last_verified = str(g.value(ref, CE.lastVerified) or "") if ref else ""
        custodian = str(g.value(ref, CE.custodian) or "") if ref else ""

        role = g.value(module, CE.attestationRole)
        role_label = str(g.value(role, RDFS.label) or _cid(role)) if role else ""

        for cid in controls:
            rows.append({
                "control": cid,
                "family": cid.split(".")[0],
                "module": module_label,
                "source": src_label,
                "source_note": src_comment,
                "uri": uri,
                "freshness_days": fresh_days,
                "freshness": _freshness_label(fresh_days),
                "last_verified": last_verified,
                "custodian": custodian,
                "role": role_label,
            })

    rows.sort(key=lambda r: (r["family"], r["control"]))
    return rows


def authoritative_sources() -> list[dict[str, Any]]:
    """The distinct authoritative sources cited by attested-reference modules —
    the systems where the ground truth actually lives ("where bob logs it").
    Returns `[{source, note, controls}]`, controls = how many controls draw on it.
    """
    from collections import Counter

    counts: Counter[str] = Counter()
    notes: dict[str, str] = {}
    for r in get_reference_data():
        counts[r["source"]] += 1
        notes.setdefault(r["source"], r["source_note"])
    return [
        {"source": s, "note": notes.get(s, ""), "controls": n}
        for s, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


def get_coverage_data() -> list[dict[str, Any]]:
    """All 110 CMMC L2 controls, each classified by how it is verified.

    Status values (derived from the claiming module's verificationMethod):
      "machine"    — a config-check oracle measures it from configuration.
      "attested"   — a registered, fresh, role-signed reference into an
                     authoritative source (the attested-reference model).
      "inherited"  — satisfied by the cloud service provider and inherited.
      "unclaimed"  — no claiming module (should not occur; all 110 are claimed).
    """
    from rdflib import Graph, RDF
    from compliance_engine.ontology.prefixes import CMMC

    catalog = Graph()
    catalog.parse(_REPO_ROOT / "data" / "ontology" / "cmmc-edit.ttl", format="turtle")

    struct = _load_structural_graph()

    # control id -> set of verification kinds across all claiming modules
    kinds: dict[str, set[str]] = {}
    for module, _p, ctrl in struct.triples((None, CMMC.controlsSatisfied, None)):
        kinds.setdefault(_cid(ctrl), set()).add(_module_verification_kind(struct, module))

    def classify(cid: str) -> str:
        ks = kinds.get(cid)
        if not ks:
            return "unclaimed"
        if "attested" in ks:
            return "attested"
        if "inherited" in ks and ks == {"inherited"}:
            return "inherited"
        return "machine"

    rows: list[dict[str, Any]] = []
    for ctrl in catalog.subjects(RDF.type, CMMC.Control):
        cid = str(catalog.value(ctrl, CMMC.controlId) or "")
        if not cid:
            continue
        text = str(catalog.value(ctrl, CMMC.text) or "")
        try:
            weight = int(str(catalog.value(ctrl, CMMC.weight) or "1"))
        except (ValueError, TypeError):
            weight = 1
        status = classify(cid)
        rows.append({
            "id": cid,
            "family": cid.split(".")[0],
            "weight": weight,
            "status": status,
            "non_deferrable": weight > 1 or cid in _NON_DEF_ONE_POINTERS,
            "inherited": status == "inherited",
            "text": text,
        })

    rows.sort(key=lambda r: (r["family"], r["id"]))
    return rows


# ---------------------------------------------------------------------------
# Whole-chain driver (used by the smoke test; available to the notebook)
# ---------------------------------------------------------------------------

def run_pipeline(scenario: str, output_dir: Path | None = None) -> dict[str, Any]:
    """Drive the entire chain for one scenario and return a structured record.

    Keys always present: `scenario`, `refused` (bool). On refusal (`gap`):
    `gate1` (the report), `order` is None, and no downstream keys. On success:
    `order`, `required_controls`, `cop`, `gate1`, `factory_state`, `halted`,
    `attested`, `audit`, `bom`, `ssp`, `output_dir`.
    """
    check_scenario(scenario)
    ds, obligations = build_dataset(scenario)
    required, markers = required_control_set(obligations)
    cop_att = attest_cop_step(ds, obligations)
    g1_preview = gate1_preview(required, ds)
    order, refusal = compile_order_or_refusal(ds, obligations, cop_att)

    if order is None:
        return {
            "scenario": scenario,
            "refused": True,
            "gate1": refusal or g1_preview,
            "order": None,
            "ds": ds,
        }

    out = Path(output_dir) if output_dir else new_output_dir()
    out.mkdir(parents=True, exist_ok=True)
    state = run_factory_step(ds, order, scenario, out)
    result: dict[str, Any] = {
        "scenario": scenario,
        "refused": False,
        "required_controls": required,
        "markers": markers,
        "cop": cop_att,
        "gate1": order.gate1 or g1_preview,
        "order": order,
        "factory_state": state,
        "halted": bool(state.halted),
        "output_dir": out,
        "ds": ds,
    }
    if state.halted:
        return result

    result["attested"] = attest_step(ds, state)
    result["audit"] = audit_step(ds, out)
    result["bom"] = bom_step(state, ds, out)
    result["ssp"] = ssp_step(ds, result["audit"], result["bom"], out)
    return result
