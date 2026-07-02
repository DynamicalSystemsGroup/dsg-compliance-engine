# Compliance Engine

**A build system where "provision the cloud environment" and "prove it's compliant" are the same action.**

Every environment is *born* from a signed, policy-checked infrastructure Order and ships with a re-executable proof of compliance (a signed BOM that doubles as the SSP). Compliance is not gathered after the fact by inspecting an existing setup — it is a **byproduct of provisioning**.

> **Design of record.** Where any document under [`reference/`](reference/) conflicts with this repo, this repo wins.

---

## Two systems, one chain

The work splits into two decoupled systems (a deliberate seam — they hand a file over the fence):

```
   CONTRACT (SBIR topic + Q&A + DFARS clauses)
        │
        ▼
┌───────────────────────────┐   separate upstream tool
│   ORDER COMPILER           │   order-compiler/
│   contract → obligations   │   • AI drafts obligations, human attests (COP)
│   → controls → modules     │   • proves PLANNING COVERAGE (Gate 1)
│   → a signed ORDER file    │   • emits a proof-carrying Order
└───────────────────────────┘
        │  Order file (signed, hash-referenced)
        ▼
┌───────────────────────────┐   the engine (this repo's runtime)
│   THE FACTORY              │   pipeline/  + evidence/ oracles/ traceability/
│   fetch modules by hash    │   • terraform plan → policy-as-code check
│   → apply (BUILDS it)      │   • terraform apply → live compliance tests
│   → live tests → BOM       │   • proves FULFILLMENT (Gate 2), human attests
│   → sign → registry        │   • BOM = SSP, stored write-once (GCS/Azure Blob)
└───────────────────────────┘
        │  BOM hash
        ▼
   AUDITOR (C3PAO) re-executes the Order → rebuilds the identical
   environment → re-runs checks → confirms the fingerprints match.
   Proof by reproduction, not a folder of screenshots.
```

**The Order Compiler is a separate tool** (a chosen seam): its only output is a signed Order file. The Factory consumes Orders and doesn't care how they were made. See [`order-compiler/DESIGN.md`](order-compiler/DESIGN.md) and [`pipeline/DESIGN.md`](pipeline/DESIGN.md).

## The two coverage gates (why the mapping is *real*)

The engine's honesty rests on refusing to proceed unless traceability is complete in both directions:

- **Gate 1 — Planning coverage** (Order Compiler, before anything is built): every control the contract requires has ≥1 module *claiming* it, every module traces back to a required control, and no claim lacks a testable method. Missing coverage ⇒ **the Order won't emit.**
- **Gate 2 — Proven fulfillment** (Factory, at BOM close): a control is MET only when its claim's evidence *passes* and a human *attests*. The BOM's control-mapping is audited against the Order's required-control set. A claim whose live test fails ⇒ **the BOM is invalid.**

Planning-coverage is a promise; proven-fulfillment is the receipt. Both are content-addressed and bidirectionally audited.

## The founding principle (inherited from ADCS)

> **Evidence does not verify requirements; evidence supports a human judgment that requirements are satisfied.**

Machines provision, gather evidence, and run automated checks (`earl:automatic`). Only a human — the Affirming Official — attests a control MET (`earl:manual`), carrying the legal (False Claims Act) accountability. This same line governs the one judgment the Compiler makes: **AI drafts the contract's obligations; a Compliance Officer attests them.**

## Built on the ADCS substrate

The [`ADCS-lifecycle-demo`](../ADCS-lifecycle-demo) engine is the proven **back half**: content-addressed hashing, human attestation, bidirectional audit, and a deterministically-compiled document — all over an RDF named-graph store. This repo reuses that substrate and adds the **front half ADCS lacks: the Order → Factory → BOM provisioning loop.**

## The two authored documents

- **Document 1 — Control Requirements Catalog** ([`reference/control-catalog.md`](reference/control-catalog.md), machine form [`ontology/cmmc-edit.ttl`](ontology/cmmc-edit.ttl)): the 110 controls + weights. The "law."
- **Document 2 — Tier 1 Traceability Matrix** ([`reference/traceability-matrix.md`](reference/traceability-matrix.md)): control → resource → evidence → status. The "evidence," generated per build as the BOM's control-mapping.
- Binding of columns → graph facts: [`reference/document-binding.md`](reference/document-binding.md).

## Repo map

| Path | Role | Ports from ADCS |
| --- | --- | --- |
| [`order-compiler/`](order-compiler/) | **Separate upstream tool:** contract → COP → controls → modules → signed Order (Gate 1) | ADCS requirement-derivation model, extended up to the contract |
| [`pipeline/`](pipeline/) | **The Factory:** executes an Order — plan → policy → apply → live tests → BOM | `pipeline/runner.py`, `plan.ttl` |
| [`evidence/`](evidence/) | Hashing + binding + the Factory's evidence generators (policy-as-code, config export) | `evidence/hashing.py`, `binding.py`, `analysis/` |
| [`oracles/`](oracles/) | Pre-deployment policy checks + live compliance tests (metric vs criterion) | `analysis/oracle.py` |
| [`traceability/`](traceability/) | Attestation, bidirectional audit, **Gate 2 + SPRS score + POA&M-legality** | `attestation.py`, `audit.py` |
| [`structural/`](structural/) | Terraform-module ↔ control allocation (what each module claims) | `structural/satellite.ttl` |
| [`ontology/`](ontology/) | `cmmc:` TBox — controls (Doc 1) + obligation/derivation vocab | `ontology/`, `scripts/build_ontology.py` |
| [`documents/`](documents/) | Deterministic **SSP** compiler (the BOM as a human-readable doc) | `documents/design_description.py` |
| [`backends/`](backends/) | Tiered write-once registry: **GCS (Tier 1)**, **Azure Blob (Tier 2)** | `pipeline/backends/` |
| [`reference/`](reference/) | Migrated research: guides, contracts, requirements, concepts, standards | — |

## Key decisions

- **Order Compiler is a separate tool** (two systems; it hands a signed Order file to the Factory).
- **Obligation extraction is AI-drafts / human-attests.**
- **Content-addressing is SHA-256 into DSG's own tiered registry — not IPFS** (`reference/requirements/cats-compliance-engine-requirements.md` §16.2).

## Status

**Runnable.** The full chain is implemented and tested — ontology build, Order compilation + Gate 1, real Terraform plan-level provisioning (mock providers), evidence/oracles, Gate 2 attestation, audit + SPRS, BOM + registry, and the deterministic SSP/Matrix. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the loop in detail and [`ROADMAP.md`](ROADMAP.md) for the phased buildout.

**As-built:** [`docs/AS-BUILT.md`](docs/AS-BUILT.md) maps the shipped code to the architecture, the two gates, the named-graph/predicate component map, and R1–R13 requirements traceability.

*Design material, not legal advice. Verify all CMMC/ITAR interpretations with the contracting officer, C3PAO, and counsel.*
