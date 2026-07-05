# From ADCS to CMMC: Building the Compliance Engine on the Traceability Substrate

> **Status:** Design synthesis — draft for review
> **Date:** 2026-07-02
> **Inputs:** `ADCS-lifecycle-demo/` (working traceability engine), `cmmc-research/concepts/cmmc-as-a-CAT.md` (CATs Order/Factory/BOM vision), `cmmc-research/requirements/cats-compliance-engine-requirements.md` (the platform spec), and the two documents now being authored — the **Control Requirements Catalog** and the **Tier 1 Traceability Matrix**.
> **Thesis in one line:** The ADCS demo is already a running reference implementation of the compliance engine the requirements doc describes. We do not need to invent the architecture — we need to re-skin a proven one, swapping "satellite requirement" for "CMMC control" and "SymPy proof" for "policy-as-code check."

---

## 0. The core claim

Three separate documents in this repo describe the *same machine* from three angles:

| Document | Describes the machine as… |
| --- | --- |
| `concepts/cmmc-as-a-CAT.md` | An **Order → Factory → BOM** pipeline (CATs vocabulary) |
| `requirements/cats-compliance-engine-requirements.md` | A **content-addressed provisioning + attestation** platform (SHA-256, GitHub PR gates, Sigstore) |
| `ADCS-lifecycle-demo/` | A **bidirectional requirements-traceability engine** with hashed evidence, human attestation, and a deterministically-compiled design document (RDF named-graph vocabulary) |

The ADCS demo is the one that **actually runs, has 306 passing tests, and is deployed live**. Its central thesis — printed at the top of its README — is verbatim the thesis CMMC needs:

> **Evidence does not verify requirements; evidence supports a human judgment that requirements are satisfied.**

In CMMC terms: *config exports, scan results, and OPA checks do not make a control MET; they support the Affirming Official's legally-accountable judgment that it is MET, under False Claims Act exposure.* The demo already separates automated **verification** (machine, `earl:mode = earl:automatic`) from human **validation** (the accountable engineer, `earl:mode = earl:manual`). That is exactly the line CMMC draws between a scanning tool's output and the Affirming Official's SPRS attestation.

**So the build strategy is not "design a compliance engine." It is "instantiate the ADCS traceability engine with a CMMC ontology, CMMC evidence generators, and CMMC attestation roles."**

---

## 1. The structural isomorphism (ADCS ↔ CMMC)

Every load-bearing concept in the ADCS demo has a one-to-one image in the CMMC problem. This is the whole argument; everything else is mechanics.

| ADCS demo concept | Code location | CMMC / compliance image | Owned by which of your two docs |
| --- | --- | --- | --- |
| `sysml:RequirementDefinition` (REQ-003) | `structural/satellite.ttl` | A **CMMC control** (IA.L2-3.5.3) with weight, POA&M eligibility, assessment method | **Document 1 — Control Requirements Catalog** |
| Requirement derivation (satellite → ADCS) | `traceability/queries.py` | Framework layering (NIST 800-171 → CMMC L2 → DFARS 7012 → IL5 → ITAR) | Document 1 |
| SysMLv2 structural model (the satellite) | `structural/*.ttl` | The **Tier 1/2 cloud architecture** (Workspace OUs, GCP projects, Azure RGs) as declared infra | Document 2 (implementation column) |
| Design element allocation (`sysml:satisfyingElement`) | `traceability/attestation.py` | **Control → resource** mapping (`SC.L2-3.13.11` → `azurerm_key_vault.fips`) | Document 2 |
| Analysis engines: SymPy proof, scipy sim | `analysis/symbolic.py`, `analysis/numerical.py` | **Evidence generators**: OPA/Rego, Checkov, Trivy, Azure Policy, `terraform show`, config exporters | Document 2 |
| `rtm:Evidence` (`ProofArtifact`, `SimulationResult`) | `evidence/binding.py` | **Compliance evidence artifacts** (config export, scan result, MFA policy JSON, CMVP cert) | Document 2 (evidence location) |
| Hash chain: `model_hash → proof_hash → evidence_hash` | `evidence/hashing.py` | The **content-addressed BOM** (Merkle tree of proofs) | Document 2 (evidence hash column) |
| `rtm:Attestation` = adequacy `gsn:Assumption` + sufficiency `gsn:Justification` + EARL outcome | `traceability/attestation.py` | **Affirming Official's control determination** (MET / NOT MET) with rationale | Document 2 (status + gap notes) |
| Behavior oracle: metric vs machine-readable criterion → `earl:passed/failed` | `analysis/oracle.py` | **Automated control check** ("MFA enforced?", "region == US?", "FIPS module present?") → PASS/FAIL | Document 2 (feeds status) |
| `earl:needsAction` when no criterion exists (REQ-004) | `analysis/oracle.py` | A control with **no machine-checkable form** (policy/training) → must be attested from documentary evidence, never auto-passed | Both |
| Forward / backward / bidirectional audit | `traceability/audit.py` | **SPRS completeness + C3PAO traceability**: every control reached by evidence (forward), every attestation backed by addressing evidence (backward) | Document 2 |
| Coverage matrix (`covered+passed`, `uncovered`) | `traceability/audit.py` | **SPRS scorecard**: which of 110 controls are MET, which are gaps | Document 2 |
| `documents/design_description.py` → **DDVS-001**, compiled deterministically from the graph | `documents/` | The **System Security Plan (SSP)** compiled from the graph — "the BOM *is* the SSP" | Both (the join) |
| `p-plan:` process model + per-stage `p-plan:Activity` | `pipeline/plan.ttl` | The **Order / SOP** ("SOP-CMMC-017"), and the audit trail proving the SOP was followed | `concepts/cmmc-as-a-CAT.md` |
| Docker image provenance + `compute.reproduce` (rebuild, digest-compare) | `compute/`, `ARCHITECTURE.md` | **Terraform plan/state reproducibility**: a C3PAO re-executes the Order and diffs live state against recorded state | requirements doc §8.3 |
| EARL verification assertions (`ClosureRuleAssertion`, `DigestMatchAssertion`, `BehaviorOracleAssertion`) | `traceability/oracle_assertion.py` | First-class, queryable records of **each automated compliance check** beside the human attestation | Document 2 |
| Named-graph quadstore (git + Flexo + Docker + txnlog) | `ARCHITECTURE.md` | The **tiered content-addressed registry** (GCS IL4 / Azure Blob IL5) with per-substrate org auspices | requirements doc §13 |
| AI-aided engineering loop: agent works through narrow-waist CLIs; only a human attests | `ENGINEERING_LOOP.md` | An **agent provisions & gathers evidence; only the Affirming Official attests** — capability and accountability separated by construction | requirements doc §10.3 |

If you internalize one row, make it the attestation row. CMMC's entire legal theory — that a *named senior executive* certifies the score and carries FCA liability — is the Hawkins–Habli Assurance Claim Point split the demo already implements. The demo even models a **declined** attestation (REQ-001, `earl:failed`) so the audit distinguishes "no attestation" from "attested-but-not-passing." That is precisely a **NOT MET** control that has been honestly assessed rather than silently skipped — the difference between an accurate SPRS score and a false claim.

---

## 2. How the two documents become the two halves of the graph

Your two documents are not just *inputs* to this system — they are literally the two named-graph layers the demo already partitions.

### Document 1 — Control Requirements Catalog → the "law" layer

This is the demo's `<adcs:structural>` + `<rtm:ontology>` layers: the **RequirementDefinition** nodes and the TBox. It is stable, version-controlled, and edited by hand (like `structural/satellite.ttl`). Each of the 110 controls becomes one `cmmc:Control` individual carrying, as RDF properties, exactly the columns you're already writing:

```turtle
cmmc:IA.L2-3.5.3 a cmmc:Control ;
    cmmc:controlId        "IA.L2-3.5.3" ;
    sysml:text            "Use multifactor authentication for local and network access to privileged accounts…" ;
    cmmc:weight           5 ;                         # SPRS point value
    cmmc:poamEligible     false ;                     # non-deferrable
    cmmc:assessmentMethod cmmc:Examine, cmmc:Test ;   # 800-171A triad
    cmmc:evidenceType     cmmc:ConfigExport ;
    cmmc:family           cmmc:IA ;
    cmmc:derivedFrom      nist:3.5.3 .                 # framework layering
```

This is the "What do we have to do?" document, and it is the input a machine can *check against*: the `cmmc:weight` and `cmmc:poamEligible` properties are what a **SPRS-score oracle** reads to compute the 110-point total and flag illegal POA&M deferrals (a 3- or 5-point control on a POA&M is a hard error, per the bidding plan).

### Document 2 — Tier 1 Traceability Matrix → the "evidence" layer

This is the demo's `<adcs:evidence>` + `<adcs:attestations>` + `<adcs:audit>` layers, plus the compiled SSP. It is **generated at pipeline time**, not hand-written — and that is the single biggest upgrade over authoring a matrix in a spreadsheet. Each row of your matrix is the demo's per-requirement record:

| Your matrix column | Graph representation | Generated by |
| --- | --- | --- |
| Control ID | `rtm:addresses cmmc:IA.L2-3.5.3` | evidence binding |
| Implementation statement | `sysml:satisfyingElement` (control → Terraform resource) | structural model |
| Responsible party | `prov:qualifiedAssociation` → agent + `prov:hadRole` | attestation |
| Evidence location | `rtm:sourceFile`, `rtm:documentRef` into the registry | evidence binding |
| Evidence hash / artifact ID | `rtm:contentHash "sha256:…"` | `evidence/hashing.py` |
| Status (MET / NOT MET / N/A / PLANNED) | `rtm:hasOutcome` → `earl:passed / failed / inapplicable / untested` | attestation |
| Gap notes | `gsn:Justification` statement on a non-passed attestation | attestation |
| POA&M reference | `cmmc:poamItem` link (only legal if `cmmc:poamEligible = true`) | audit gate |

The demo's **VCRM** (Verification Cross-Reference Matrix) in `documents/design_description.py` *is* your traceability matrix, compiled deterministically so identical evidence bytes rebuild to byte-identical Markdown. Its `--check` drift gate means the matrix can never silently fall out of sync with the underlying evidence — which is the exact failure mode ("evidence collected last minute", "the SSP is a living document that isn't") called out as a top pitfall in `guides/cmmc-0-to-100-guide.md`.

### The join = the SSP and the SPRS submission

Run both layers through the demo's document compiler and you get the deterministic SSP. The "How these two documents relate" table you wrote already names the four downstream artifacts (SSP core, SPRS input, BOM structure, C3PAO package). All four are *views over the same graph* in the demo model — no re-keying, no drift, one source of truth.

---

## 3. What the ADCS demo settles for us (decisions we can stop debating)

Reading the demo resolves several open questions still live in the concept/requirements docs:

1. **IPFS is out; SHA-256 + a quadstore is in — and it works.** The demo uses bare SHA-256 content hashing (`evidence/hashing.py`) over git + a named-graph store, with zero IPFS. This is exactly the decision the requirements doc §5/§16 already made ("No IPFS") but the older `cmmc-as-a-CAT.md` concept doc still shows `bafybei…` CIDs. **The demo validates the requirements doc and supersedes the concept doc on this point.** Adopt SHA-256 + registry; retire the IPFS framing.

2. **Signing has a known, staged path.** The demo's own "Future Work #1" is *"Cryptographic envelopes & signatures — W3C VC Data Integrity + in-toto/SLSA + sigstore/Rekor. Today's hashes are bare SHA-256: content identity but not authenticity."* That is verbatim the requirements doc's Sigstore cosign / Rekor plan (NFR-3.4). So: **Phase 1 uses bare SHA-256 (identity); the authenticity layer is a bolt-on both projects already scoped identically.** No need to design it now.

3. **The Affirming Official model has a known path too.** Demo "Future Work #2" — *FOAF + W3C Org Ontology + `schema:hasCredential` + Verifiable Credentials on top of `prov:Agent`* — is exactly what you need to record *who* attested, *in what role*, and *under what authority* (the Affirming Official's SPRS identity). The attestation already carries `prov:qualifiedAssociation → prov:hadRole`; the credential layer is the documented next step.

4. **Reproducible re-execution for the C3PAO is already built.** `compute.reproduce` rebuilds an artifact at its recorded git ref and digest-compares, emitting a `DigestMatchAssertion`. Point the same mechanism at a Terraform module + plan and you have "the assessor re-executes the Order and verifies live state matches recorded state" (requirements doc §7.2 `/verify`, concept doc §5) — as running code, not a slide.

5. **The agent-safety story is solved by construction.** `ENGINEERING_LOOP.md` shows an LLM agent doing the heavy lifting through typed CLIs while *only a human can attest*. For a compliance system with FCA exposure this is the whole ballgame: automate provisioning and evidence collection aggressively; keep the attesting edge human and accountable, marked in the record (`earl:semiAuto` for scripted stand-ins, `earl:manual` for the real official).

---

## 4. The delta: what we add to turn ADCS into the CMMC engine

The architecture is done. The domain-specific work is four swaps and two additions.

### Swap 1 — Ontology: `cmmc:` beside `rtm:`
Author a thin `cmmc:` integration ontology the same way `rtm:` is built: subclasses/subproperties of established vocab, no novel epistemics. `cmmc:Control ⊑ sysml:RequirementDefinition`; `cmmc:weight`, `cmmc:poamEligible`, `cmmc:family`, `cmmc:assessmentMethod`. Reuse the ROBOT/ELK build + triple-budget discipline from `scripts/build_ontology.py`. **This ontology is Document 1 in machine form.**

### Swap 2 — Structural model: cloud architecture instead of a satellite
Replace `structural/satellite.ttl` with the Tier 1 topology as SysMLv2/RDF: Workspace CUI OU, GCP Assured Workloads IL4 folder, projects, IAM groups, Key Vault, NSGs — each a design element that *satisfies* one or more controls. This is the machine form of the "implementation statement" column of Document 2 and mirrors `guides/tier1-buildout-plan.md`.

### Swap 3 — Evidence generators: policy-as-code instead of SymPy/scipy
The demo's `analysis/` engines become `evidence/generators/`:
- **Static (pre-apply):** `terraform show -json`, Checkov, Trivy, OPA/Rego → `rtm:ProofArtifact`-style nodes.
- **Live (post-apply):** config exporters (Workspace 2SV policy JSON, GCP Org Policy, IAM bindings, CMVP cert lookups) → `rtm:Evidence` nodes.
Each generator hashes its output with `evidence/hashing.py` unchanged and binds `rtm:addresses cmmc:<control>` exactly as `evidence/binding.py` does today.

### Swap 4 — Oracles: control checks instead of eigenvalue budgets
`analysis/oracle.py` is the template. Author an `ACCEPTANCE_CRITERIA` table of machine-checkable controls:
```python
"IA.L2-3.5.3": Criterion(metric_key="mfa_enforced_privileged", comparator="eq", threshold=True),
"SC.L2-3.13.11": Criterion(metric_key="fips_module_present",  comparator="eq", threshold=True),
"ITAR-120.54":   Criterion(metric_key="key_admin_region",     comparator="eq", threshold="US"),
```
Controls with no machine-checkable form (policy documents, training records, IR tabletop) are routed to the attested-reference oracle, which returns `earl:passed`/`earl:needsAction`/`earl:failed` against a registered, resolving, fresh, role-signed document reference — the oracle *refuses to auto-pass what it cannot compute*, forcing a human attestation from documentary evidence. This is the guardrail against the "we say we do it vs. we can prove it" gap the guides warn about.

### Addition 1 — Registry backends: GCS (Tier 1) + Azure Blob (Tier 2)
The demo already abstracts persistence behind `pipeline/backends/` (Local / Flexo / Fuseki) with a preflight `probe()` and fail-fast. Add `GCSBackend` and `AzureBlobBackend` implementing the same interface, with write-once/immutable semantics (requirements doc §13.3). The tiered "Tier 2 returns only the BOM hash to Tier 1" flow is the demo's existing per-substrate `rtm:operatedBy` auspices + named-graph partitioning.

### Addition 2 — SPRS-score audit
Extend `traceability/audit.py` with a CMMC-specific pass: read `cmmc:weight` per control, subtract for every non-`earl:passed` control, and **hard-fail if any 3- or 5-point control is deferred to a POA&M** (32 CFR §170.21). Output the coverage matrix as the SPRS scorecard (110 = Final, 88–109 = Conditional, <88 = ineligible). This is the "What do we have to do vs. what have we proved" reconciliation, computed — not asserted.

Everything else — the named-graph store, the GitHub PR/approval gate (requirements doc §8.2 = the demo's engineer-in-the-loop), the deterministic document compiler, the bidirectional audit, the reproducibility loop, the trust queries, the CLI narrow-waist — carries over unchanged.

---

## 5. Buildout plan (fork the demo, don't greenfield)

This aligns with the requirements doc's phasing (§18) and the July 22 / Nov 10 deadlines in the bidding plan, but grounds each phase in concrete reuse of the ADCS repo.

**Phase 0 — Fork & re-skin (days 1–5, parallel to the `tier1-buildout-plan.md` 5-day enclave build).**
- Fork `ADCS-lifecycle-demo` → `cmmc-compliance-engine`.
- Author the `cmmc:` ontology from **Document 1** (all 110 controls, weights, POA&M flags). This is the highest-leverage day: Document 1 *is* the deliverable, in Turtle.
- Replace the structural model with the Tier 1 topology stub.
- Prove the loop end-to-end with *mocked* evidence generators (the demo's `--auto` path), producing a first compiled SSP + coverage matrix with everything `PLANNED`.

**Phase 1 — Real Tier 1 evidence (weeks 2–4).**
- Implement the config-export + policy-as-code generators for the ~50 controls the requirements doc's success criterion targets, starting with the 63 non-deferrable ones.
- Wire the `GCSBackend`. Wire GitHub PR approval + OIDC as the Stage-6 gate.
- First real attestation session: the Affirming Official walks the coverage matrix; MET/NOT MET recorded as EARL outcomes with gap notes. Output feeds the SPRS self-assessment.

**Phase 2 — SPRS + C3PAO hardening (weeks 5–6).**
- SPRS-score audit pass; POA&M legality gate.
- Bolt on Sigstore cosign (demo Future Work #1) so BOMs are authentic, not just content-identified — required before handing a C3PAO re-executable evidence.
- Wire `compute.reproduce` against Terraform so a C3PAO can rebuild-and-diff.

**Phase 3 — Tier 2 (IL5/ITAR) (weeks 7–10).**
- `AzureBlobBackend`, GCC High / Azure Gov structural model, ITAR/IL5 oracles (US-region, US-person key admin, FIPS HSM CMVP).
- Cross-tier flow: Tier 1 submits an Order; Tier 2 returns only the BOM hash — the demo's named-graph + auspices model, now across two clouds.

---

## 6. Risks & honest limits

- **Not every control is machine-checkable.** ~40 of 110 (policy, training, PS, IR, physical) run through the attested-reference oracle (`earl:passed`/`earl:needsAction`/`earl:failed`) and *must* be human-attested from documents. The engine's value there is the audit trail and the deterministic SSP, not automation. Don't oversell auto-coverage.
- **The oracle verifies a *model-level* claim, never physical satisfaction.** "Azure Policy reports MFA enforced" is evidence, not truth; the official still attests. Preserve this discipline verbatim — it is both the demo's ethic and CMMC's legal reality.
- **Reproducibility of *cloud* state is harder than rebuilding a Docker image.** Terraform re-apply against a live tenant has side effects; the `/verify` path should read-and-diff, not re-apply. Scope carefully in Phase 2.
- **This is research tooling, not a C3PAO-blessed product.** A C3PAO may still want a traditional PDF SSP alongside the compiled one (requirements doc risk table). The compiler gives you that PDF *for free and always current* — lead with that, don't fight the assessor's format.

---

## 7. The one-paragraph pitch

We already have a working, tested, deployed engine — `ADCS-lifecycle-demo` — that takes formal requirements, generates hashed evidence against them, separates automated verification from accountable human attestation, audits traceability in both directions, and compiles a deterministic, drift-checked design document from a content-addressed graph. CMMC Level 2 is the *same problem with a different requirement set*: 110 controls instead of 4, policy-as-code instead of SymPy, an Affirming Official instead of an attesting engineer. The **Control Requirements Catalog** is the requirement ontology; the **Traceability Matrix** is the evidence-and-attestation graph; the compiled join is the SSP and the SPRS input. We are not building a compliance platform from scratch — we are instantiating a proven traceability substrate with a CMMC ontology, CMMC evidence generators, and CMMC attestation roles, and we can have the loop running end-to-end (mocked evidence) inside a week.

---

## Appendix — file-level reuse map

| Need | Reuse directly | Adapt | Author new |
| --- | --- | --- | --- |
| Content hashing | `evidence/hashing.py` | — | — |
| Evidence → graph binding | `evidence/binding.py` | swap engine labels | — |
| Human attestation | `traceability/attestation.py` | roles → Affirming Official/Compliance Officer | — |
| Automated checks | `analysis/oracle.py` (pattern) | — | `cmmc` criteria table + control generators |
| Bidirectional audit | `traceability/audit.py` | — | SPRS-score + POA&M-legality pass |
| Compiled SSP / VCRM | `documents/design_description.py` | headings → SSP sections | — |
| Reproducibility | `compute/reproduce.py` | Docker → Terraform target | — |
| Persistence + preflight | `pipeline/backends/`, `pipeline/runner.py` | — | `GCSBackend`, `AzureBlobBackend` |
| Ontology build | `scripts/build_ontology.py`, `ontology/` | — | `cmmc-edit.ttl` (Document 1) |
| Agent-in-the-loop safety | `ENGINEERING_LOOP.md` | — | — |
| Trust / "how can I trust this" queries | `traceability/queries.py` | — | control-coverage queries |

*This is a synthesis document, not legal or compliance advice. Verify all CMMC/ITAR interpretations with the contracting officer, C3PAO, and counsel.*
