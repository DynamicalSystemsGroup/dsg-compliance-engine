# Compliance Engine — As-Built Architecture

> **Status:** As-built snapshot, 2026-07-02. All pipeline layers committed
> including the operator CLI (`cli.py`) that drives the full chain in one
> command. Every predicate, path, and number below is taken from the
> committed tree.
>
> **R1–R13** are the thirteen requirements defined one-per-row in the
> [requirements traceability table below](#requirements-traceability-r1r13).

## Thesis: compliance is a provisioning artifact

The environment is **built** from a signed, policy-checked infrastructure **Order** —
not inspected after the fact. Real Terraform Tier-1 modules are driven at **plan
level** (offline providers, no live cloud apply); the compliance proof — a
content-addressed **BOM** that doubles as the **SSP** — is the byproduct of that
build, not a separate audit.

Two epistemically distinct steps produce a MET control:

- **Verification (machine).** Oracles compare a control's evidence metric to a
  criterion → an EARL outcome. Oracles **`ce:evaluatesAgainst`** a control; they
  **never** `ce:attests`. Evidence **`ce:addresses`** a control; it never attests.
- **Validation (human).** Only the Affirming Official's Gate-2 attestation
  (**`ce:attests` + `ce:hasOutcome earl:passed`**) makes a control MET. Where no
  machine criterion exists, the oracle returns `cantTell` → the control is
  human-only. _Evidence addresses, only attestation attests._

## The two systems and the seam

```
CONTRACT (SBIR topic + Q&A + DFARS clauses)
   │
   ▼  ── ORDER COMPILER (order-compiler/) ──────────────────────────────
   │     contract → obligations (AI-drafted, HUMAN-ATTESTED COP)
   │     → required controls (rule_library) → claiming modules
   │     → GATE 1 (planning coverage) → signed, hash-referenced ORDER
   │
   ▼  ── signed Order file  ◀── THE SEAM (a file handed over the fence) ──
   │
   ▼  ── THE FACTORY (pipeline/ + evidence/ oracles/ traceability/) ─────
         LoadOrder → FetchByHash → Plan (real terraform plan)
         → PolicyCheck (oracles on the plan; fail stops before Apply)
         → Apply (mock state) → CollectEvidence (generators)
         → Oracles (control checks) → GATE 2 (human attestation)
         → Audit + SPRS → BOM → SSP
```

The Order Compiler is a **separate upstream tool**: its only output is the signed
Order. The Factory consumes Orders and does not care how they were produced.

## The two gates

- **Gate 1 — planning coverage** (`order-compiler/gate1.py`). The Order emits
  _only if_: every required control has ≥1 claiming module (`cmmc:controlsSatisfied`),
  every module traces to a required control, and no claim lacks a testable method
  (`cmmc:verificationMethod`). Failure ⇒ no Order. This is **forward/backward over
  the plan**, before anything is built.
- **Gate 2 — proven fulfillment** (`traceability/attestation.py`). The Affirming
  Official's per-control MET / NOT MET call, recorded as a `ce:Attestation` with an
  adequacy `gsn:Assumption`, a sufficiency `gsn:Justification`, a
  `prov:qualifiedAssociation` to `ce:role-AffirmingOfficial`, an EARL outcome, and
  the backing-oracle link. **This is the only place a control becomes MET.**

## Component map

Named graphs (`ontology/prefixes.py`): `<ce:ontology> <ce:plan> <ce:structural>
<ce:order> <ce:evidence> <ce:attestations> <ce:plan-execution> <ce:audit>`.

| Package / module                                                                        | Role                                                                                                                     | Writes graph                                                                 | Key predicates / artifacts                                                                                                                                                                                   |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ontology/` + `scripts/build_ontology.py`                                               | The "law": 110 controls + SHACL closure suite; offline, reproducible build (`cmmc.ttl` + manifest, `TRIPLE_BUDGET=1200`) | `<ce:ontology>`                                                              | `cmmc:Control`, `cmmc:controlId/text/weight/poamEligible/nonDeferrable/family/inherited/variableWeight`; shapes `ControlShape`, `PoamLegalityShape`, `ContradictionShape`                                    |
| `order-compiler/`                                                                        | contract → attested COP → required controls → Gate 1 → signed Order                                                      | `<ce:order>`                                                                 | `cmmc:Obligation`, `cmmc:obligationType/dataMarker/sourceRef`, `ce:requiresControl`; `rule_library.resolve()`; `clause_library`; `gate1`                                                                     |
| `structural/tier1.ttl`                                                                   | module ↔ control allocation (the satisfy edge)                                                                           | `<ce:structural>`                                                            | `sysml:PartUsage`, `cmmc:controlsSatisfied`, `cmmc:verificationMethod` (`ce:oracle-*`), `sysml:SatisfyRequirementUsage`                                                                                      |
| `pipeline/` — `dataset/plan_execution/state/runner/provision/backends/registry`          | Factory orchestration, Terraform provisioning seam, write-once registry                                                  | `<ce:plan-execution>`                                                        | `p-plan:Activity`, `prov:*`, `step_iri(...)`; `terraform plan`; registry keyed by `content_hash(bytes)`                                                                                                      |
| `terraform/tier1/*.tf`                                                                   | Real HCL Tier-1 modules (IAM, KMS, logging, org-policy, Workspace) + `tftest`                                            | — (HCL)                                                                      | driven at **plan level**, providers configured offline (no live apply)                                                                                                                                       |
| `evidence/` — `hashing/binding/generators`                                               | Deterministic SHA-256 hashing + evidence binding; fixture-backed generators                                              | `<ce:evidence>`                                                              | `ce:Evidence` (`ce:ConfigExport`/`ce:PolicyCheck`), `ce:addresses`, `ce:contentHash`, `ce:modelHash`, `ce:evidentiaryStatus`, `ce:sourceFile`, `prov:wasGeneratedBy`                                         |
| `oracles/` — `criteria/assertion`                                                        | Verification (machine): metric vs criterion → EARL outcome                                                               | `<ce:audit>`                                                                 | `ce:ControlCheckAssertion`, `ce:evaluatesAgainst`, `earl:result`→`earl:TestResult`→`earl:outcome`, `earl:mode earl:automatic`, `ce:backedBy` — **never `ce:attests`**                                        |
| `traceability/attestation.py`                                                            | Gate 2 (human validation)                                                                                                | `<ce:attestations>`                                                          | `ce:Attestation`, `ce:attests`, `ce:hasOutcome`, `ce:attestationMode`, `ce:oracleOutcome`, `cmmc:overrideJustification`, `ce:hasEvidence`, `gsn:Assumption`/`gsn:Justification`, `prov:qualifiedAssociation` |
| `traceability/verification.py`                                                           | SHACL closure suite + evidence re-hash                                                                                   | — (reads)                                                                    | `verify(ds)` → `VerificationReport(conforms, shape_violations, reverification_mismatches)`                                                                                                                   |
| `traceability/audit.py`                                                                  | Bidirectional audit + R13 contradiction + proven-vs-attested + SPRS wiring                                               | `<ce:audit>`                                                                 | `ce:forwardPassed/backwardPassed/bidirectionalPassed/contradictionCount/metByMachine/metByHumanOnly/sprsScore/sprsStatus/validSubmission`                                                                    |
| `traceability/sprs.py`                                                                   | SPRS score + POA&M legality gate                                                                                         | —                                                                            | `ControlStatus`, `SprsResult(score,status,illegal_poam,unmet,valid_submission)`, `score()`, `load_control_statuses()`                                                                                        |
| `traceability/bom.py`                                                                    | BOM assembly, hash-reference, two-level registry store                                                                   | registry + `ce:BOM` RDF                                                      | `ce:BOM`, `ce:forContract`, `ce:derivedFromOrder`, `ce:bomHash`, `ce:evidentiaryStatus`, `ce:referencesArtifact`, `ce:hasControlMapping`                                                                     |
| `documents/ssp.py` + `documents/queries.py`                                              | Deterministic, byte-stable SSP + generated Traceability Matrix (Document 2); mandatory R12 banner                        | — (reads)                                                                    | `compile_ssp(ds, …)` / `compile_ssp_from_run(…)` → Markdown; `dataset_fingerprint` (sorted quads, bnode-stable); `document_date` = `MAX(prov:generatedAtTime)`; NON-EVIDENTIARY banner; `--check` drift gate |
| `cli.py`                                                                                 | Operator driver — the one-command NV012 `demo` chaining all stages over one shared Dataset; six standalone subcommands   | writes run artifacts under `output/` (`bom.json`, engine `.trig`, run state) | `demo` = compile-order → run-factory → attest → audit → bom → ssp-hook; `--evidence-set {all-covered\|gap\|contradiction}`, `--backend {fake\|terraform}`, `--auto`                                          |

## Requirements traceability (R1–R13)

The thirteen requirements **R1–R13** are defined by this table (one intent per
row; there is no R14).

| Req     | One-line intent                                                                        | Satisfied by                                                                                                                                                     | How                                                                                                                                                                     |
| ------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **R1**  | Order **compiled** from the contract via a human-attested COP                          | `order-compiler/rule_library.py`, `order-compiler/{cop.py,compiler.py}`                                                                                          | obligations resolve to controls; COP attested; `compiler` emits `ce:requiresControl`                                                                                    |
| **R2**  | **Gate 1** planning coverage (forward/backward + no untestable claim)                  | `order-compiler/gate1.py`, `structural/tier1.ttl`                                                                                                                | own SPARQL over the satisfy edge + `cmmc:verificationMethod`; no coverage ⇒ no Order                                                                                    |
| **R3**  | Factory executes an Order **end-to-end** (mock provision + fixture evidence) → BOM     | `pipeline/runner.py`+`provision/terraform.py`, `terraform/tier1`, `cli.py demo`                                                                                  | staged pipeline; real `terraform plan`, mock apply; fixture generators; `cli.py demo` chains it all (tested by `tests/test_cli.py`)                                     |
| **R4**  | MET **only when evidence passes AND a human attests**; no criterion → `cantTell`→human | `oracles/`, `traceability/attestation.py`                                                                                                                        | oracle `earl:{passed,failed,cantTell}`; MET requires `ce:attests`+`earl:passed`                                                                                         |
| **R5**  | **Bidirectional audit** against the Order's required set                               | `traceability/audit.py`                                                                                                                                          | forward (required→module+attestation), backward (attestation evidence `ce:addresses` same control)                                                                      |
| **R6**  | **SPRS score** + hard-fail illegal POA&M                                               | `ContradictionShape`/`PoamLegalityShape` (ontology), `traceability/sprs.py` + `audit.py`                                                                        | `110 − Σ weight(non-MET)`; any weight>1/excluded on a POA&M ⇒ `valid_submission False`                                                                                  |
| **R7**  | Deterministic, drift-checked **SSP** + generated **Matrix (Doc 2)**                    | `documents/ssp.py`+`documents/queries.py`                                                                                                                        | `compile_ssp` renders byte-stable Markdown; fingerprint over sorted quads (bnode-stable); `--check` drift gate; VCRM (all 110 controls) from the graph                  |
| **R8**  | **SHA-256 write-once registry**; BOM references artifacts by hash                      | `pipeline/registry.py`+`backends/`, `evidence/hashing.py`, `traceability/bom.py`                                                                                | content-addressing; `ContentMismatch` on rewrite; BOM `ce:referencesArtifact` by hash                                                                                   |
| **R9**  | **Reuse the ADCS substrate by porting** it                                             | `pipeline/`, `evidence/`, `oracles/`, `traceability/` (all ported from `ADCS-lifecycle-demo/`)                                                                   | dataset, hashing, oracle, attestation, audit, verification ported + retargeted `rtm:`→`ce:`/`cmmc:`                                                                     |
| **R10** | Encode **all 110 controls** with weights + POA&M eligibility                           | `ontology/cmmc-edit.ttl`                                                                                                                                         | 110 `cmmc:Control`; histogram `{5:42, 3:14, 1:52, variable:2}`; six excluded 1-pointers `nonDeferrable`                                                                 |
| **R11** | Separate **environment** vs **deliverable** obligations (attested, not silent)         | `order-compiler/obligations.ttl`+`rule_library.py`                                                                                                               | `cmmc:obligationType`; a CUI/ITAR-marked deliverable raises `SpilloverReviewRequired` (never silent `{}`)                                                               |
| **R12** | **Non-evidentiary marker** propagates; SSP refuses to omit it                          | `evidence/binding.py` (`ce:evidentiaryStatus "mock"`), `traceability/bom.py` propagation, `documents/ssp.py` banner                                              | any weak status ⇒ whole BOM `"mock"`; the SSP emits a NON-EVIDENTIARY banner + colophon stamp whenever a mock status is present — structurally forced, no suppress flag |
| **R13** | **Contradiction detector** + proven-vs-attested split, surfaced in the SSP             | `ContradictionShape` (ontology), `traceability/attestation.py` (`ce:oracleOutcome`/`cmmc:overrideJustification`), `traceability/audit.py`, `documents/ssp.py` (colophon) | MET over `failed`/absent oracle w/o override = violation; "N MET-by-machine / M MET-by-human-only" metric flows into the SSP colophon via `SprsSummary`           |

**Coverage: 13/13 requirements are satisfied by committed, tested code.** R7
(`documents/ssp.py`), the SSP half of R12, and R13's SSP surfacing are shipped;
R3's end-to-end chain runs via `cli.py demo` and is exercised by
`tests/test_cli.py`. The only outstanding item is the queued
`ForwardTraceabilityShape` scope fix (a shape refinement, not a requirement).

## SPRS + POA&M legality

`SPRS = 110 − Σ(weight of each control not MET)` (`traceability/sprs.py`):

- **110** → Final Level 2 · **88–109** → Conditional (POA&M, 180-day closeout) · **< 88** → Ineligible.
- **MET is attestation-authoritative** — `score()` reads `met` from the Gate-2
  outcome only (a passing oracle alone never yields MET). CSP-inherited-and-attested
  controls (the PE 5-pointers, `cmmc:inherited`) count MET when attested.
- **POA&M legality (32 CFR §170.21):** only 1-point controls are deferrable, and six
  specific 1-pointers are excluded (`nonDeferrable true`: AC.L2-3.1.20/3.1.22,
  CA.L2-3.12.4, PE.L2-3.10.3/3.10.4/3.10.5). Any weight>1 or excluded control on a
  POA&M ⇒ `illegal_poam` non-empty ⇒ `valid_submission False` **regardless of score**.

## Real vs deferred — be precise

| Capability                                          | State                                                                                                                                                                                                                                                                                   |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Terraform Tier-1 modules (`terraform/tier1/*.tf`)   | **Real HCL**, driven at **plan level** only. No live apply, no real cloud tenant/credentials (offline providers).                                                                                                                                                                       |
| Evidence generators (`evidence/generators/`)        | **Fixture-backed** until a live tenant exists. Fixture-sourced evidence carries `ce:evidentiaryStatus "mock"` (R12) and forces the SSP's NON-EVIDENTIARY banner — a mock BOM/SSP can never be mistaken for a submittable one.                                                           |
| Content-addressing                                  | **SHA-256** into a local write-once registry (the cache/fallback tier), plus an **append-only, versioned Flexo MMS store backend** (`pipeline/backends/flexo.py`, `--store-backend flexo`) that is **offline-simulated** via a deterministic `FakeFlexoStore` (a live in-enclave Flexo server is deferred). GCS Tier-1 / Azure Blob Tier-2 cloud backends remain deferred. `hash_reference` exposes the `registry://<hash>` seam.                                                                                 |
| Attestation signing (`compliance_engine.signing`) | **Real Ed25519** (`Ed25519LocalSigner` dev key; `NullSigner`; `CosignKmsSigner`). Attestation records carry `sig_algo` in `{none, ed25519-v1, cosign-v1}`; signed records are **verified at load and fail closed** (a tampered/unverifiable signed record is rejected). **cosign + FIPS-KMS is the deferred production key path** — implemented behind a probe that switches on when the cosign binary + KMS key are present; Rekor is deferred. The demo runs `sig_algo=none` (git-trust) and stays NON-EVIDENTIARY.                                                                                 |
| Full-chain provenance + signed audit package        | **Real.** Full-chain **P-Plan provenance** (`traceability/provenance.py`, `plan.ttl` + upstream `ce:SOP-ORDER-COMPILE` plan) models the whole lineage (contract → obligations → controls → COP → Order → evidence → oracle assertions → attestations → BOM/SSP) as p-plan Variables realized by Entities, with a `check_sop_adherence` deviation check. `ce package` builds and **signs** a manifest bundling BOM, SSP, audit + SPRS, provenance, the per-control control→attestation→signed-policy chain, and the signed-policy inventory; `ce verify-package` re-verifies it offline (manifest signature + artifact re-hash + chain). Code: `traceability/package.py`. `ce package` also renders the human report into `package/` (`documents/report.py`): a mixed-audience `report.html` (plain-language verdict + glossary + family-level coverage rollup first, dense per-control tables in appendices) plus a paged `report.pdf` when the `weasyprint` binary is present. `ce report` (and `ce demo --report`) re-renders it on demand; `ce demo --full` runs the entire 110-control catalog. Runs over mock evidence remain NON-EVIDENTIARY.                                                                                 |
| IL5 hosting overlay                                 | **Deferred to Phase II.** `OBL-IL5` / `IL5-OVERLAY` resolve to an **empty** control set in Phase I (Tier 1 / IL4) — tagged, not an error.                                                                                                                                               |
| SSP / Traceability Matrix (`documents/ssp.py`)       | **Real and byte-stable** (deterministic fingerprint, `--check` drift gate). But it renders over the **fixture-backed (mock) evidence** above, so its output carries the **NON-EVIDENTIARY** banner — a compiled demo SSP, never a submittable one.                                      |
| End-to-end acceptance                               | `cli.py demo` runs the full chain today, **including the SSP step** (`[6/6 ssp]` renders `ssp.md` via `compile_ssp_from_run`); tested by `tests/test_cli.py` and the acceptance scenarios in [`docs/ACCEPTANCE.md`](ACCEPTANCE.md). The SSP can also be rendered standalone via `documents.ssp build` over the run's `.trig`. |

## Running it

```
# The one-command NV012 demo (compile-order → run-factory → attest → audit → bom → ssp-hook):
uv run ce demo --evidence-set all-covered      # happy path: Order emits, chain completes, mock BOM
uv run ce demo --evidence-set gap              # Gate 1 REFUSES — Order not emitted, exit 2, no bom.json
uv run ce demo --evidence-set contradiction    # completes with an R13 contradiction in the audit

# Render the deterministic SSP + Traceability Matrix from a run's dataset (carries the NON-EVIDENTIARY banner):
uv run python -m compliance_engine.documents.ssp build --input output/engine.trig [--check]
```

`cli.py demo` writes `bom.json`, the engine `.trig`, and run state under
`output/`. See the README's **"Run the NV012 demo"** section for the operator
walkthrough. Individual stages are also available as subcommands (`compile-order`,
`run-factory`, `attest`, `audit`, `bom`, `ssp`).

---

_Design material, not legal advice. Verify all CMMC/ITAR interpretations with the
contracting officer, C3PAO, and counsel._
