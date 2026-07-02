"""U2 (part A) — CMMC ontology TTL parse + closure invariants.

rdflib-only: does NOT import agent-1's modules. Validates that the hand-authored
Document-1 encoding and SHACL shapes parse and carry the required structure.
"""
from pathlib import Path

from rdflib import Graph, Namespace, RDF, Literal

ROOT = Path(__file__).resolve().parent.parent
EDIT_TTL = ROOT / "ontology" / "cmmc-edit.ttl"
SHAPES_TTL = ROOT / "ontology" / "cmmc_shapes.ttl"

CMMC = Namespace("http://dynamicalsystems.group/ontology/cmmc#")
SH = Namespace("http://www.w3.org/ns/shacl#")

# The six 1-point controls excluded from POA&M eligibility (32 CFR 170.21(a)(2)(iii)).
EXCLUDED_NONDEFERRABLE = {
    "AC.L2-3.1.20", "AC.L2-3.1.22", "CA.L2-3.12.4",
    "PE.L2-3.10.3", "PE.L2-3.10.4", "PE.L2-3.10.5",
}
VARIABLE = {"IA.L2-3.5.3", "SC.L2-3.13.11"}

EXPECTED_HISTOGRAM = {5: 42, 3: 14, 1: 52, "variable": 2}


def load(path: Path) -> Graph:
    g = Graph()
    g.parse(path, format="turtle")
    return g


def test_cmmc_edit_parses():
    g = load(EDIT_TTL)
    assert len(g) > 0


def test_exactly_110_controls():
    g = load(EDIT_TTL)
    controls = set(g.subjects(RDF.type, CMMC.Control))
    assert len(controls) == 110, f"expected 110 cmmc:Control, got {len(controls)}"


def _histogram(g: Graph) -> dict:
    hist = {5: 0, 3: 0, 1: 0, "variable": 0}
    for control in g.subjects(RDF.type, CMMC.Control):
        is_variable = (control, CMMC.variableWeight, Literal(True)) in g
        if is_variable:
            hist["variable"] += 1
            continue
        weight = int(g.value(control, CMMC.weight))
        hist[weight] += 1
    return hist


def test_weight_histogram():
    g = load(EDIT_TTL)
    hist = _histogram(g)
    assert hist == EXPECTED_HISTOGRAM, f"histogram mismatch: {hist}"


def test_variable_controls_marked():
    g = load(EDIT_TTL)
    marked = {
        str(g.value(s, CMMC.controlId))
        for s in g.subjects(CMMC.variableWeight, Literal(True))
    }
    assert marked == VARIABLE, f"variable-weight controls mismatch: {marked}"


def test_six_excluded_are_nondeferrable():
    g = load(EDIT_TTL)
    by_id = {str(g.value(s, CMMC.controlId)): s for s in g.subjects(RDF.type, CMMC.Control)}
    for cid in EXCLUDED_NONDEFERRABLE:
        node = by_id[cid]
        assert (node, CMMC.nonDeferrable, Literal(True)) in g, (
            f"{cid} must carry cmmc:nonDeferrable true"
        )
        # they are weight-1 yet excluded from POA&M
        assert int(g.value(node, CMMC.weight)) == 1, f"{cid} should be weight 1"
        assert (node, CMMC.poamEligible, Literal(False)) in g, (
            f"{cid} must not be POA&M-eligible"
        )


def test_shapes_parse_and_define_guardrails():
    g = load(SHAPES_TTL)
    assert len(g) > 0
    shape_local_names = {
        str(s).rsplit("#", 1)[-1].rsplit("/", 1)[-1]
        for s in g.subjects(RDF.type, SH.NodeShape)
    }
    for required in ("ControlShape", "PoamLegalityShape", "ContradictionShape"):
        assert required in shape_local_names, (
            f"cmmc_shapes.ttl must define {required}; found {sorted(shape_local_names)}"
        )
