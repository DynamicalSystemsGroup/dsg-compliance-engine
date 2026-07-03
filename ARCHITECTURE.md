# Architecture

The engine is a **provisioning loop** — the environment is built from an Order and the proof falls out of the build — running on the [`ADCS-lifecycle-demo`](../ADCS-lifecycle-demo) traceability substrate. Per-module detail lives in each directory's `DESIGN.md`.

> **Design of record (end-state).** This document describes the full target architecture. For what is *implemented today* vs. deferred, see [`docs/AS-BUILT.md`](docs/AS-BUILT.md). In the diagrams below, **🟩 green = runs today** and **🟨 amber = Phase II (mocked or deferred today)**. Every current run is fixture-backed and stamped **NON-EVIDENTIARY**.

## 1. The two systems and the seam between them

```mermaid
flowchart TB
    subgraph OC["🧩 Order Compiler · order-compiler/ — separate upstream tool"]
        direction TB
        C["Contract artifacts<br/>(hashed)"] --> COP["Contract Obligation Profile (COP)<br/>AI drafts · human ATTESTS"]
        COP --> RC["Required control set<br/>clause library + rule library"]
        RC --> MOD["Module set<br/>control → claiming module"]
        MOD --> G1{{"GATE 1 — planning coverage<br/>forward · backward · testable"}}
        G1 -->|fail| X1["Order won't emit<br/>report names the gap"]
        G1 -->|pass| ORD["signed ORDER file"]
    end

    ORD ==>|"the seam: a signed, hash-referenced Order file"| AP

    subgraph FAC["🏭 The Factory · pipeline/ · evidence/ · oracles/ · traceability/"]
        direction TB
        AP["Approval gate<br/>GitHub PR + environment reviewer<br/>(separation of duties)"] --> F1["1 · fetch modules + policies<br/>from registry BY HASH"]
        F1 --> F2["2 · terraform plan<br/>→ plan hash"]
        F2 --> F3{"3 · policy-as-code on the plan<br/>region check today · OPA/Checkov/Trivy Phase II"}
        F3 -->|fail| STOP["STOP — before anything is built"]
        F3 -->|pass| F4["4 · terraform apply<br/>BUILDS the real environment → state hash"]
        F4 --> F5["5 · live compliance tests<br/>on what was built → test hashes"]
        F5 --> F6["6 · assemble BOM<br/>control-mapping: resource → control → evidence"]
        F6 --> G2{{"GATE 2 — fulfillment<br/>human ATTESTS each control MET"}}
        G2 --> F8["8 · store BOM write-once → BOM hash"]
        F8 --> F9["sign BOM (Sigstore)"]
    end

    classDef now fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef later fill:#fef9c3,stroke:#ca8a04,color:#713f12;
    classDef gate fill:#dbeafe,stroke:#2563eb,color:#1e3a8a;
    classDef stop fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    class C,COP,RC,MOD,ORD,AP,F1,F2,F6,F8 now;
    class F4,F5,F9 later;
    class G1,G2,F3 gate;
    class X1,STOP stop;
```

**Legend:** 🟩 runs today · 🟨 Phase II (mocked/deferred) · 🔷 gate · 🟥 hard stop. Today the Factory runs `terraform plan` at **preview level with mock providers** (no cloud, no credentials); **apply, live compliance tests, and Sigstore signing are Phase II**, and evidence is fixture-backed (→ NON-EVIDENTIARY).

The Compiler and the Factory are **decoupled by design** (chosen seam): the Factory's input is a signed Order file and nothing else. This keeps the Factory simple and lets Orders be produced, reviewed, and version-controlled independently.

## 2. Why the resources _actually_ fulfill the requirements — two gates

|              | Gate 1 — Planning coverage                                  | Gate 2 — Proven fulfillment                        |
| ------------ | ----------------------------------------------------------- | -------------------------------------------------- |
| **Where**    | Order Compiler, before anything is built                    | Factory, at BOM close                              |
| **Forward**  | every required control has a claiming module                | every required control comes back MET in the BOM   |
| **Backward** | every module traces to a required control (no orphan infra) | every attestation is backed by addressing evidence |
| **Guard**    | no claim without a testable method                          | MET only if evidence passes AND a human attests    |
| **Fail**     | Order won't emit                                            | BOM invalid                                        |

Bidirectional audit is the ADCS `traceability/audit.py` mechanism, applied at both gates. A control claim is a _promise_ at Gate 1 and a _receipt_ at Gate 2 — never a bare assertion.

## 3. The derivation chain (extends the ADCS model up to the contract)

ADCS derives `satellite req → ADCS req → design element → evidence → attestation`. We add the top segment (contract → module); the two segments form **one bidirectionally-audited chain**:

```mermaid
flowchart LR
    subgraph ADD["➕ Added here — extends the model up to the contract"]
        direction LR
        CC["Contract<br/>clause"] --> OB["Obligation"] --> RC2["Required<br/>control"] --> MOD2["Module"]
    end
    subgraph BASE["♻️ ADCS-style back half (reused substrate)"]
        direction LR
        PS["Provisioned<br/>state"] --> CT["check +<br/>live test"] --> AT["attestation"] --> BOM2["BOM"]
    end
    MOD2 ==> PS

    classDef added fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef base fill:#e0f2fe,stroke:#0284c7,color:#075985;
    class CC,OB,RC2,MOD2 added;
    class PS,CT,AT,BOM2 base;
```

Every arrow is an explicit, content-addressed link. A gap anywhere is a hard fail, not a silent pass. That property — not any single check — is what makes "the infra actually maps to fulfillment" true.

## 4. The named-graph substrate (the back half)

Everything is held as an `rdflib.Dataset` of named graphs (ADCS pattern), one per layer. Data flows left-to-right; the audit graph reads from all of them:

```mermaid
flowchart LR
    ONT["ce:ontology<br/>controls + vocab"] --> STR["ce:structural<br/>module ↔ control"]
    STR --> ORD3["ce:order<br/>Order + COP (Gate 1)"]
    ORD3 --> EV["ce:evidence<br/>plan/state/check/test hashes"]
    EV --> ATT["ce:attestations<br/>Affirming Official (Gate 2)"]
    PLN["ce:plan<br/>Order process model"] -.-> ORD3
    ONT -.-> AUD["ce:audit<br/>bidirectional audit + SPRS"]
    STR -.-> AUD
    ORD3 -.-> AUD
    EV -.-> AUD
    ATT -.-> AUD
```

_(named graphs shown without their `<…>` delimiters for diagram clarity; the table below uses the canonical `<ce:…>` form.)_

| Named graph         | Holds                                                  | Filled by                           |
| ------------------- | ------------------------------------------------------ | ----------------------------------- |
| `<ce:ontology>`     | `cmmc:` controls (Doc 1) + obligation/derivation vocab | `ontology/`                         |
| `<ce:plan>`         | the SOP/Order process model                            | `pipeline/plan.ttl`                 |
| `<ce:structural>`   | module ↔ control allocation                            | `structural/`                       |
| `<ce:order>`        | the Order + its COP derivation (Gate 1 record)         | `order-compiler/`                   |
| `<ce:evidence>`     | plan/state/check/test artifacts, hashed                | Factory steps 2–5                   |
| `<ce:attestations>` | Affirming Official determinations                      | Factory step 7                      |
| `<ce:audit>`        | bidirectional audit + SPRS scorecard                   | `traceability/audit.py` + `sprs.py` |

## 5. Verification vs. validation (the legal boundary)

- **Verification** = automated, fully-specified (policy checks, live tests, hash matches, SPRS math). `earl:automatic`. Safe to delegate to an agent; safe to re-run.
- **Validation** = human judgment (the Affirming Official's MET/NOT-MET call; the Compliance Officer's COP attestation). `earl:manual`. Carries FCA liability.

An agent may drive the entire Factory and draft the COP; it can never attest. Capability and accountability are separated by construction.

## 6. Tiered provisioning chain

Each tier provisions the next; sensitive data never flows _down_. Persistence is behind `backends/` with a fail-fast preflight, both write-once:

```mermaid
flowchart LR
    T0["Tier 0<br/>Workspace + GitHub · no CUI<br/>approves + dispatches Orders"]
    T1["Tier 1 · IL4 / CMMC L2<br/>builds CUI environments<br/>GCSBackend (write-once)"]
    T2["Tier 2 · IL5 / ITAR<br/>builds high-side environments<br/>AzureBlobBackend (write-once)"]
    T0 ==>|Order| T1
    T1 ==>|Order| T2
    T2 -.->|"returns ONLY a BOM hash — data never flows down"| T1

    classDef now fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef later fill:#fef9c3,stroke:#ca8a04,color:#713f12;
    class T0,T1 now;
    class T2 later;
```

Phase I is **Tier 1 (IL4/CMMC)**; **Tier 2 (IL5/ITAR)** is the deferred high-side overlay. Tier 2 returns only a BOM hash to Tier 1 — the proof crosses the boundary, the CUI never does.

## 7. Re-executability (proof by reproduction)

The Factory captures the exact module hashes, plan, and state. An auditor takes the Order + BOM and **re-runs it** — rebuilding the identical environment and re-running the checks — then digest-compares:

```mermaid
flowchart LR
    A["Order + BOM<br/>(delivered)"] --> B["re-fetch modules<br/>by hash"]
    B --> C4["re-run terraform plan<br/>+ re-run checks"]
    C4 --> D{"digest-compare<br/>fingerprints"}
    D -->|match| OK["✅ reproduced<br/>proof holds"]
    D -->|mismatch| BAD["❌ tampered / drifted"]

    classDef gate fill:#dbeafe,stroke:#2563eb,color:#1e3a8a;
    classDef now fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef stop fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    class D gate;
    class OK now;
    class BAD stop;
```

This is the ADCS `compute.reproduce` loop retargeted from Docker images to Terraform: rebuild at the recorded reference, compare fingerprints, emit a match/mismatch assertion. (Today the loop re-runs at **plan level**; live rebuild-and-compare is Phase II.)

## 8. Bare now vs. bolted on later

- **Now:** bare SHA-256 (content identity).
- **Phase 2:** Sigstore cosign + Rekor (authenticity / non-repudiation of Orders and BOMs) — required before a C3PAO re-executes.
- **Phase 2+:** authority/credential model binding the Affirming Official's SPRS identity + role to each attestation.
