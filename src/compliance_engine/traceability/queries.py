"""Shared SPARQL for CMMC dataset interrogation.

Ported from ADCS-lifecycle-demo/traceability/queries.py and retargeted:
requirement → cmmc:Control, and the attestation/evidence instance vocab
rtm: → ce:. Imported by traceability.attestation and later by documents/.

All queries assume the union view of the Dataset (default_union=True). Results
come back as lists of dicts via query_to_dicts().
"""

from __future__ import annotations

from rdflib import Graph

from compliance_engine.ontology.prefixes import CE, CMMC, EARL, GSN, PREFIXES, PROV, SYSML

_INIT_NS = {
    "sysml": SYSML,
    "cmmc": CMMC,
    "ce": CE,
    "prov": PROV,
    "earl": EARL,
    "gsn": GSN,
    "rdfs": PREFIXES["rdfs"],
    "rdf": PREFIXES["rdf"],
}

# ---------------------------------------------------------------------------
# Control queries
# ---------------------------------------------------------------------------

ALL_CONTROLS = """
SELECT ?control ?id ?text ?weight WHERE {
    ?control a cmmc:Control ;
             cmmc:controlId ?id ;
             cmmc:text ?text ;
             cmmc:weight ?weight .
}
ORDER BY ?id
"""

CONTROL_TEXT = """
SELECT ?text WHERE {
    ?control cmmc:controlId "%s" ;
             cmmc:text ?text .
}
"""

# ---------------------------------------------------------------------------
# Evidence queries
# ---------------------------------------------------------------------------

ALL_EVIDENCE = """
SELECT ?ev ?type ?hash ?summary WHERE {
    ?ev a ce:Evidence ;
        ce:contentHash ?hash ;
        ce:resultSummary ?summary .
    OPTIONAL { ?ev a ?type . FILTER(?type IN (ce:ConfigExport, ce:PolicyCheck)) }
}
ORDER BY ?ev
"""

EVIDENCE_FOR_CONTROL = """
SELECT ?ev ?type ?hash ?summary WHERE {
    ?ev a ce:Evidence ;
        ce:contentHash ?hash ;
        ce:resultSummary ?summary ;
        ce:addresses ?control .
    ?control cmmc:controlId ?controlId .
    OPTIONAL { ?ev a ?type . FILTER(?type IN (ce:ConfigExport, ce:PolicyCheck)) }
    FILTER(?controlId = "%s")
}
ORDER BY ?ev
"""

# Document-compiler view: full evidence detail grouped by control in Python.
EVIDENCE_DETAIL = """
SELECT ?controlId ?ev ?contentHash ?modelHash ?summary ?status ?genTime WHERE {
    ?ev a ce:Evidence ;
        ce:addresses ?control ;
        ce:contentHash ?contentHash ;
        ce:resultSummary ?summary .
    ?control cmmc:controlId ?controlId .
    OPTIONAL { ?ev ce:modelHash ?modelHash }
    OPTIONAL { ?ev ce:evidentiaryStatus ?status }
    OPTIONAL { ?ev prov:generatedAtTime ?genTime }
}
ORDER BY ?controlId ?ev
"""

# ---------------------------------------------------------------------------
# Attestation queries (Gate 2)
# ---------------------------------------------------------------------------

ALL_ATTESTATIONS = """
SELECT ?att ?controlId ?official ?adequacy ?sufficiency ?outcome ?mode ?timestamp WHERE {
    ?att a ce:Attestation ;
         ce:attests ?control ;
         ce:hasOutcome ?outcome ;
         prov:wasAssociatedWith ?agent .
    OPTIONAL { ?att prov:generatedAtTime ?timestamp }
    OPTIONAL { ?att ce:attestationMode ?mode }
    ?att gsn:inContextOf ?adequacyNode .
    ?adequacyNode a gsn:Assumption ; gsn:statement ?adequacy .
    ?att gsn:inContextOf ?sufficiencyNode .
    ?sufficiencyNode a gsn:Justification ; gsn:statement ?sufficiency .
    ?control cmmc:controlId ?controlId .
    ?agent rdfs:label ?official .
}
ORDER BY ?controlId
"""

# Document-compiler view: adds the outcome short-name, override justification,
# backing-oracle outcome, the cited evidence set (GROUP_CONCAT — split on "|"
# and sort in Python for determinism), and whether the attestation is backed by
# a machine-recorded document (ce:documentEvidence — the "attested-evidenced"
# Track B signal; see ssp.py's _backing_label()).
ATTESTATION_DETAIL = """
SELECT ?att ?controlId ?official ?adequacy ?sufficiency ?outcomeShort ?mode
       ?timestamp ?override ?overrideEvidence ?oracleOutcome ?documentEvidence
       (GROUP_CONCAT(STR(?ev); separator="|") AS ?evidence) WHERE {
    ?att a ce:Attestation ;
         ce:attests ?control ;
         ce:hasOutcome ?outcome ;
         prov:wasAssociatedWith ?agent .
    OPTIONAL { ?att prov:generatedAtTime ?timestamp }
    OPTIONAL { ?att ce:attestationMode ?mode }
    OPTIONAL { ?att cmmc:overrideJustification ?override }
    OPTIONAL { ?att ce:overrideEvidence ?overrideEvidence }
    OPTIONAL { ?att ce:oracleOutcome ?oracleOutcome }
    OPTIONAL { ?att ce:documentEvidence ?documentEvidence }
    OPTIONAL { ?att ce:hasEvidence ?ev }
    ?att gsn:inContextOf ?adequacyNode .
    ?adequacyNode a gsn:Assumption ; gsn:statement ?adequacy .
    ?att gsn:inContextOf ?sufficiencyNode .
    ?sufficiencyNode a gsn:Justification ; gsn:statement ?sufficiency .
    ?control cmmc:controlId ?controlId .
    ?agent rdfs:label ?official .
    BIND(REPLACE(STR(?outcome), "^.*[#/]", "") AS ?outcomeShort)
}
GROUP BY ?att ?controlId ?official ?adequacy ?sufficiency ?outcomeShort ?mode
         ?timestamp ?override ?overrideEvidence ?oracleOutcome ?documentEvidence
ORDER BY ?controlId ?att
"""

# Per-control EARL outcome short name; "" for controls with no attestation.
CONTROL_OUTCOMES = """
SELECT ?controlId ?outcomeShort WHERE {
    ?control a cmmc:Control ; cmmc:controlId ?controlId .
    OPTIONAL {
        ?att a ce:Attestation ;
             ce:attests ?control ;
             ce:hasOutcome ?outcome .
        BIND(REPLACE(STR(?outcome), "^.*[#/]", "") AS ?outcomeShort)
    }
}
ORDER BY ?controlId
"""

UNATTESTED_CONTROLS = """
SELECT ?controlId WHERE {
    ?control a cmmc:Control ; cmmc:controlId ?controlId .
    FILTER NOT EXISTS {
        ?att a ce:Attestation ; ce:attests ?control .
    }
}
ORDER BY ?controlId
"""

# ---------------------------------------------------------------------------
# Forward / backward trace (control ↔ evidence ↔ attestation)
# ---------------------------------------------------------------------------

BACKWARD_TRACE = """
SELECT ?controlId ?evHash ?evSummary ?official ?outcomeShort WHERE {
    ?att a ce:Attestation ;
         ce:attests ?control ;
         ce:hasEvidence ?ev ;
         ce:hasOutcome ?outcome ;
         prov:wasAssociatedWith ?agent .
    ?agent rdfs:label ?official .
    ?control cmmc:controlId ?controlId .
    ?ev ce:contentHash ?evHash ;
        ce:resultSummary ?evSummary .
    BIND(REPLACE(STR(?outcome), "^.*[#/]", "") AS ?outcomeShort)
}
ORDER BY ?controlId ?evHash
"""


def query_to_dicts(graph: Graph, sparql: str) -> list[dict[str, str | None]]:
    """Execute a SPARQL query and return results as a list of dicts.

    Pass a Dataset (union view, default_union=True) to walk the whole assembled
    dataset; pass a single named-graph view to restrict to one layer.
    """
    results = graph.query(sparql, initNs=_INIT_NS)
    rows: list[dict[str, str | None]] = []
    for row in results:
        d: dict[str, str | None] = {}
        for var in results.vars:
            val = getattr(row, str(var), None)
            d[str(var)] = str(val) if val is not None else None
        rows.append(d)
    return rows
