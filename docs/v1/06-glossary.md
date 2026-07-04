# Chapter 06 - Glossary

Every term used in this tour, in alphabetical order. Each entry gives a plain definition first. Where a term corresponds to something concrete in the code or data, an "In this repo:" pointer names the exact file or directory.

If a definition mentions another term that has its own entry, you can read that entry for more detail. When a concept is developed at length elsewhere in the tour, the entry points you to the chapter that covers it: [00-what-is-this.md](00-what-is-this.md), [01-the-order.md](01-the-order.md), [02-the-factory.md](02-the-factory.md), [03-machine-vs-human.md](03-machine-vs-human.md), [04-the-proof.md](04-the-proof.md), or [05-try-it.md](05-try-it.md).

---

## A

### Affirming Official
The named human who carries the legal accountability for a compliance claim. The Affirming Official may attest any control, regardless of the control's required role. When this person signs a statement that a requirement is satisfied, they take on legal liability under the False Claims Act and under 18 U.S.C. section 1001 (false statements to the federal government). This is the person whose judgment turns evidence into a met control.
> In this repo: modeled as the role `Role_AffirmingOfficial`; see [03-machine-vs-human.md](03-machine-vs-human.md).

### apply (Terraform)
The Terraform step that actually creates or changes real infrastructure. In this engine, live apply is deferred. The runtime performs a mock apply instead, so nothing is deployed and no cloud is contacted. See also **plan (Terraform)** and **mock provider**.
> In this repo: `src/compliance_engine/pipeline/runner.py`.

### attestation
A signed human statement that a requirement is satisfied. An attestation is recorded as a manual assertion in the data model. A control is only marked met when a role-appropriate human attests it; evidence alone never marks a control met. In the graph, evidence "addresses" a control while a human attestation "attests" it, and that distinction is enforced by the shapes, not by policy. Attestation records now carry a real cryptographic signature (Ed25519), verified at load and failing closed on tamper; the demo runs `sig_algo=none`, where the trust anchor is the Git history of the record. See also **Ed25519 / attestation signing**.
> In this repo: attestation logic in `src/compliance_engine/traceability/attestation.py` and `src/compliance_engine/traceability/attestation_store.py`; the shipped demo records in `data/attestations/tier1.jsonl`.

### attested reference (the model)
The uniform verification model that lets the engine cover every control, not only the ones a machine can measure. Each control points at an authoritative source, carries a resolvable reference into that source, and names a required attestation role. The engine checks that the reference is registered, resolves, is within its freshness window, and is signed by a human in the required role. Because the same check applies to a machine-measurable control and a human-only control alike, all 110 controls can be handled the same way.
> In this repo: see [03-machine-vs-human.md](03-machine-vs-human.md).

### attested-reference oracle
The oracle that evaluates the attested-reference model. It walks a fixed decision sequence and stops at the first failure, returning a specific machine-readable reason. In order, it checks: reference not registered (`needsAction`, "reference-missing"); reference has no URI (`failed`, "reference-unresolvable"); reference never verified (`needsAction`, "reference-never-verified"); reference past its freshness window (`failed`, for example "stale:172d>90d"); no attestation covers the control (`needsAction`, "awaiting-attestation"); signer role neither Affirming Official nor the required role (`failed`, for example "signer-role-mismatch:Role_ITAdmin!=Role_SecurityOfficer"); attestation predates the reference's last verification (`failed`, "attestation-predates-reference"). Only if every condition holds does it return `passed`. A signer's own declined outcome (`failed`, `cantTell`, or `needsAction`) is propagated, not overridden.
> In this repo: `src/compliance_engine/oracles/attested_reference.py`.

### audit
The bidirectional check that the delivered result matches what the Order required. It confirms, forward and backward, that every required control maps to something in the Bill of Materials and that nothing in the Bill of Materials fails to trace back to a required control. The audit also produces the SPRS score, the POA&M-legality judgment, and the contradiction list.
> In this repo: `src/compliance_engine/traceability/audit.py`; outputs `audit.md` and `audit.json`. See [04-the-proof.md](04-the-proof.md).

### audit package
The signed manifest deliverable an assessor re-verifies offline. It bundles and signs the BOM, the SSP, the audit and SPRS score, the full-chain P-Plan provenance, a per-control control-to-attestation-to-signed-policy chain, and the signed-policy inventory. Re-verification checks the signature, re-hashes every artifact, and walks the chain, without contacting any live service. Built by `ce package`; re-verified by `ce verify-package`. See also **P-Plan** and **audit**.
> In this repo: `src/compliance_engine/traceability/package.py`.

### authoritative source
The system that owns the ground truth for a class of evidence: a cloud API, a learning-management system, an HR system, a document repository, or the engine's own run history. Every module names an authoritative source so that its reference points at the place where the truth of that control actually lives.
> In this repo: modeled as `ce:AuthoritativeSource`.

---

## B

### BOM (Bill of Materials)
The itemized record of the evidence supporting each required control. For every required control it records the module or modules that claim it, the evidence hashes, the oracle outcome, the attestation outcome, and the resulting status. The BOM is content-addressed by its own SHA-256, stored write-once, and inherits the weakest evidentiary status of its inputs.
> In this repo: `src/compliance_engine/traceability/bom.py`; output `bom.json`. See [04-the-proof.md](04-the-proof.md).

---

## C

### C3PAO
A Certified Third-Party Assessment Organization: the independent assessor that certifies a defense contractor against CMMC. An assessor uses proof by reproduction to re-resolve every artifact by its hash, re-hash it to confirm the fingerprint, and re-run the plan-level checks to confirm the record.
> In this repo: the step-by-step reproduction procedure is in `docs/AUDITOR-GUIDE.md`.

### cantTell
An oracle outcome meaning the answer is genuinely unknowable. It is distinct from `needsAction`: `cantTell` means "no way to know", while `needsAction` means "here is the specific next step". See also **oracle outcomes**.

### ce: namespace
One of the two local RDF namespaces. `ce:` holds the engine's instance data: orders, evidence, BOMs, attestations, references, authoritative sources, and roles. Contrast with the **cmmc: namespace**. In this repo: bound in `src/compliance_engine/ontology/prefixes.py`.

### CLI (ce)
The operator command line. Installed as `ce` (also `compliance-engine`, and runnable as `python -m compliance_engine`). Its commands are `compile-order`, `run-factory`, `attest`, `audit`, `bom`, `verify`, `ssp`, and `demo`. In this repo: `src/compliance_engine/cli.py`.

### CMMC Level 2
Cybersecurity Maturity Model Certification, Level 2: the certification level that requires the 110 security controls of NIST SP 800-171 Rev. 2. It is required of U.S. defense contractors that handle Controlled Unclassified Information (CUI). This engine targets CMMC Level 2.

### cmmc: namespace
One of the two local RDF namespaces. `cmmc:` holds the control catalog, the "law" layer: the 110 controls, their weights, and their POA&M eligibility. Contrast with the **ce: namespace**. In this repo: `data/ontology/cmmc-edit.ttl`, bound in `src/compliance_engine/ontology/prefixes.py`.

### config-check oracle
The oracle kind for machine-measurable controls. It evaluates evidence gathered from the environment (for example, from a Terraform plan or a config export) against the control's criteria, and records the result as an automatic assertion. Of the 110 controls, 65 are machine-verified by this kind of oracle.
> In this repo: `src/compliance_engine/oracles/criteria.py`.

### content-addressing
Naming an object by the hash of its contents, so that the name is a fingerprint of the exact bytes. Any change to the bytes changes the name, which makes tampering detectable and reproduction verifiable. Every automated check, piece of evidence, and human sign-off in the engine is content-addressed and cross-linked. See also **hash** and **SHA-256**.
> In this repo: the registry and hashing under `src/compliance_engine/pipeline/registry.py` and `src/compliance_engine/pipeline/evidence/hashing.py`.

### contradiction (R13)
A control that a human marked met while its machine oracle failed (or was absent), with no written override justification. The contradiction is surfaced separately from the SPRS score so that an unexplained human-over-machine call cannot hide inside a passing number. A written override justification clears it.
> In this repo: the contradiction dimension in `src/compliance_engine/traceability/audit.py`. See [03-machine-vs-human.md](03-machine-vs-human.md).

### control
One of the 110 security requirements in the catalog (the NIST SP 800-171 Rev. 2 controls that CMMC Level 2 requires). A control is either met or not met; it becomes met only when its evidence passes its oracle and a role-appropriate human attests it. All 110 controls now have a claiming module.
> In this repo: the catalog (the "law" layer) lives in `data/ontology/cmmc-edit.ttl` under the `cmmc:` namespace.

### control weight
The point value assigned to each control for scoring, either 1, 3, or 5. The SPRS score subtracts the weights of the controls that are not met. Weights also govern POA&M legality: only 1-point controls may be deferred.
> In this repo: used by `src/compliance_engine/traceability/sprs.py`.

### COP
The compiled statement of what the contract obliges the organization to do, produced upstream in the Order Compiler. Software drafts the obligations from the contract, and a Compliance Officer attests them; the required-control set is then derived from those obligations. The demo's COP draft is a fixture input.
> In this repo: `src/compliance_engine/order_compiler/cop.py`; demo draft `fixtures/nv012/cop_draft.ttl`. See [01-the-order.md](01-the-order.md).

### cosign + KMS
The deferred production signing path (`sig_algo="cosign-v1"`), where attestation signatures are produced by cosign against a FIPS-validated Key Management Service key rather than a local developer key. The Ed25519 developer signer works today; cosign + KMS is the production key path and is not yet wired. See also **Ed25519 / attestation signing** and **Rekor**.

### CUI (Controlled Unclassified Information)
Government information that is not classified but still requires safeguarding. Contractors that handle CUI must meet CMMC Level 2. A CUI (or ITAR) deliverable cannot silently drop a requirement: a spillover guard forces human review rather than dropping controls.

### custodian
The named person responsible for keeping a reference current. Every reference names a custodian alongside its URI, freshness window, and last-verified timestamp. See also **reference**.

---

## D

### demo
The CLI command that runs the whole chain in one step: `compile-order` to `run-factory` to `attest` to `audit` to `bom` to `ssp`. Invoked as `ce demo --evidence-set {all-covered | gap | contradiction} --auto --output-dir <dir>`. Exercised in [05 - Try it yourself](05-try-it.md).

### DFARS
The Defense Federal Acquisition Regulation Supplement: the contract clauses that require defense contractors to safeguard CUI and, through CMMC Level 2, to implement the NIST SP 800-171 controls this engine targets.

### Dublin Core
One of the standards the vocabulary is assembled from. Dublin Core supplies the general metadata terms (titles, dates, and similar descriptive fields). In this repo: bound in `src/compliance_engine/ontology/prefixes.py`.

---

## E

### EARL
The Evaluation and Report Language, one of the standards the vocabulary is assembled from. EARL supplies the assertion pattern (an assertion has a subject, a test, an outcome, and who made it) and the outcome values the oracles use.
> In this repo: assertion handling in `src/compliance_engine/oracles/assertion.py`.

### Ed25519 / attestation signing
The signing scheme now wired for attestation records. Each record carries a `sig_algo` in `{none, ed25519-v1, cosign-v1}`; an `ed25519-v1` record holds a real Ed25519 signature that is verified when the record is loaded and fails closed if the record has been tampered with. The demo ships with `sig_algo=none` (git-trust), which is still non-evidentiary. Cosign + a FIPS Key Management Service is the deferred production path. See also **cosign + KMS** and **attestation**.
> In this repo: `src/compliance_engine/signing/`.

### evidence
Machine-readable facts that address controls. Evidence supports a human judgment; it never marks a control met on its own. Today all evidence is fixture-backed and therefore non-evidentiary. In the data model, evidence "addresses" a control while a human attestation "attests" it.
> In this repo: evidence binding and generation under `src/compliance_engine/pipeline/evidence/`; demo fixtures in `fixtures/nv012/`.

### evidence backing
How each control's MET rests on evidence: machine (an oracle measured it), override (a human override that must carry appended justification evidence), or human-only (a role-appropriate attestation with no machine measurement). The audit and BOM report the split so that a MET is never presented without stating what backs it. See also **override evidence** and **contradiction (R13)**.

### evidentiary status (mock / mock-plan / attested-reference-mock)
A tag on each piece of evidence describing how real it is. "mock" is a fixture config export; "mock-plan" is derived from the real Terraform plan run against mock providers; "attested-reference-mock" is a fixture attestation for a Track B control. All three are non-evidentiary. If any weak status is present, the whole BOM and SSP are stamped NON-EVIDENTIARY and are not submittable, and there is no switch to remove the banner while mock inputs are present.
> In this repo: see [02-the-factory.md](02-the-factory.md) and **NON-EVIDENTIARY**.

---

## F

### Factory (the runtime)
The name used in the code for the runtime pipeline. The Factory consumes a signed Order and runs its stages in sequence: load the Order (recompute and re-check its hashes), fetch each module by hash, run a real Terraform plan against mock providers, run a policy-as-code check including the data-residency hard gate, run a mock apply, collect evidence, and run the oracles.
> In this repo: `src/compliance_engine/pipeline/runner.py`. See [02-the-factory.md](02-the-factory.md).

### Flexo (Flexo MMS)
The append-only, versioned RDF quadstore intended as the remote tier of record for stored artifacts. The backend is wired (`--store-backend flexo`), but a live in-enclave Flexo server is deferred; today it is offline-simulated by a deterministic, append-only `FakeFlexoStore`. The local write-once registry serves as the cache/fallback tier beside it. See also **registry**.
> In this repo: `src/compliance_engine/pipeline/backends/flexo.py`.

### freshness / freshness window
The maximum age a reference may reach before it is considered stale. Each reference carries a freshness window; the attested-reference oracle fails a reference that is past it. The named policies are annual = 365 days, semi-annual = 180, quarterly = 90, monthly = 30, and event-based = 0 (never expires on time alone, used for records that only need to exist per event).
> In this repo: `src/compliance_engine/oracles/freshness.py`.

---

## G

### Gate 1
The planning-coverage gate, run inside the Order Compiler before anything is built. It checks forward (every required control has at least one claiming module), backward (every included module traces back to a required control), and no-untestable-claim (every claiming module names a verification method). If Gate 1 fails, the Order is not emitted and the gap is named.
> In this repo: `src/compliance_engine/order_compiler/gate1.py`. See [01-the-order.md](01-the-order.md).

### Gate 2
The proven-fulfillment gate, run inside the runtime at BOM close. A control is met only when its evidence passes its oracle and a human attests it in the required role. The BOM's control-mapping is audited against the Order's required set, forward and backward.
> In this repo: `src/compliance_engine/traceability/audit.py`. See [03-machine-vs-human.md](03-machine-vs-human.md).

---

## H

### hash
A short, fixed-length fingerprint computed from the exact bytes of an object. If the bytes change, the hash changes, which is what makes content-addressing and reproduction possible. This engine uses SHA-256 throughout.
> In this repo: `src/compliance_engine/pipeline/evidence/hashing.py`.

### HCL
HashiCorp Configuration Language, the language Terraform configurations are written in. The Terraform under `infrastructure/terraform/tier1/` is HCL that the runtime plans against mock providers.
> In this repo: `infrastructure/terraform/tier1/`.

---

## I

### IL4 / IL5
Impact Levels 4 and 5 in the U.S. Department of Defense cloud framework, describing how sensitive a workload is and the safeguarding it requires. Handling CUI is what drives a contractor into this territory and toward CMMC Level 2.

### ITAR
The International Traffic in Arms Regulations, which govern defense-related technical data. Like a CUI deliverable, an ITAR deliverable cannot silently drop a requirement; the spillover guard forces human review instead of dropping controls.

---

## M

### MET / NOT MET
The two states a control can be in. A control is MET only when its evidence passes its oracle and a role-appropriate human attests it; otherwise it is NOT MET. NOT MET controls subtract their weight from the SPRS score.

### mock provider
A stand-in for a real cloud provider used when running Terraform, so that a real `terraform plan` executes but no cloud is contacted, no credentials are used, and nothing is deployed. Evidence derived from a mock-provider plan carries the "mock-plan" evidentiary status.
> In this repo: `src/compliance_engine/pipeline/runner.py`.

### module
A unit that claims one or more controls and names how each is verified. A module carries an authoritative source, a reference into it, and a required attestation role. There are 39 modules in total, and every one of the 110 controls now has a claiming module.
> In this repo: the structural model in `data/structural/tier1.ttl`. See **Track A / Track B**.

---

## N

### named graph
A partition of the RDF dataset, one per lifecycle layer (ontology, plan, structural, order, evidence, attestations, plan-execution, audit). Partitioning by layer keeps each stage of the lifecycle separable and traceable within one dataset.
> In this repo: `src/compliance_engine/ontology/prefixes.py`; the full run dataset is emitted as `engine.trig`.

### needsAction
An oracle outcome meaning there is a concrete, actionable gap, and it always carries a reason. It is distinct from `cantTell`: `needsAction` names the specific next step (register a reference, refresh a stale one, obtain a signature, fix a role), which is what turns the audit output into a work list. See also **oracle outcomes**.

### NIST SP 800-171
NIST Special Publication 800-171 Rev. 2, the standard whose 110 controls define what CMMC Level 2 requires for protecting CUI. The engine's catalog is these 110 controls.
> In this repo: the catalog in `data/ontology/cmmc-edit.ttl`.

### NON-EVIDENTIARY
The status stamped on the BOM and SSP whenever any weak evidentiary status (mock, mock-plan, or attested-reference-mock) is present. A NON-EVIDENTIARY document is not submittable, and there is no switch to remove the banner while mock inputs are present. Every run today is non-evidentiary. The banner is emitted structurally from the data, not added by hand.
> In this repo: the SSP banner is emitted by `src/compliance_engine/documents/ssp.py`.

### NV012
The shipped demonstration contract. Its Order requires a 22-control slice, and the SPRS score in the demo is computed over those 22 required controls. The structural model still claims all 110 controls; NV012 simply exercises a slice.
> In this repo: `fixtures/nv012/` (with `cop_draft.ttl`, and the `all-covered/`, `gap/`, and `contradiction/` evidence sets). See [05-try-it.md](05-try-it.md).

---

## O

### obligation
A single requirement drawn from the contract, produced in the Order Compiler. Software drafts the obligations and a Compliance Officer attests them; the required-control set is then derived from the obligations by the rule library.
> In this repo: obligation logic in `src/compliance_engine/order_compiler/`. See [01-the-order.md](01-the-order.md).

### oracle
The component that evaluates whether a control's evidence and attestations satisfy that control, returning one of the four outcomes. There are three oracle kinds (config-check, attested-reference, and signed-artifact), and across 39 modules the oracles cover all 110 controls: 65 machine-verified by config-check, 43 by attested-reference, and 2 CSP-inherited.
> In this repo: `src/compliance_engine/oracles/`. See [03-machine-vs-human.md](03-machine-vs-human.md).

### oracle kinds
The three families of oracle: config-check (machine-measurable controls), attested-reference (a reference plus a signature), and signed-artifact (a detached signature over an artifact, used for signed documents).
> In this repo: `src/compliance_engine/oracles/`.

### oracle outcomes
The four possible results an oracle can return: `passed`, `failed`, `cantTell` (genuinely unknowable), and `needsAction` (a concrete, actionable gap that always carries a reason). `needsAction` is distinct from `cantTell`: the first names a next step, the second says there is no way to know. See also the individual entries **cantTell** and **needsAction**.

### Order
The signed handoff from the planning side to the runtime. It carries the required-control set, the modules that claim those controls, and their references, and the runtime consumes it. "Signed" means hash-referenced by SHA-256; true cryptographic signing (Sigstore/cosign) is future work. Loading the Order in the runtime recomputes and re-checks its hashes.
> In this repo: produced by `src/compliance_engine/order_compiler/compiler.py`. See [01-the-order.md](01-the-order.md).

### Order Compiler
The upstream machine that turns a contract into a signed Order. It drafts obligations (software drafts, a Compliance Officer attests), derives the required-control set via the rule library, runs Gate 1, and emits the signed Order. If Gate 1 fails, no Order is emitted and the gap is named.
> In this repo: `src/compliance_engine/order_compiler/` (`gate1.py`, `compiler.py`, `cop.py`, `rule_library.py`). See [01-the-order.md](01-the-order.md).

### override evidence
The justification a human must append when overriding a machine result — for example attesting a control MET while its oracle failed. Modeled as `ce:overrideEvidence`: an override is not accepted on assertion alone; it must carry appended evidence for the override. Without it, the human-over-machine call is surfaced as a contradiction rather than cleared. See also **contradiction (R13)** and **evidence backing**.

---

## P

### plan (Terraform)
The Terraform step that computes what would change without changing anything. The runtime runs a real `terraform plan` against mock providers, so the plan is genuine but no cloud is contacted and nothing is deployed. Evidence derived from the plan carries the "mock-plan" status. See also **apply (Terraform)**.
> In this repo: `src/compliance_engine/pipeline/runner.py`; Terraform in `infrastructure/terraform/tier1/`.

### POA&M (Plan of Action and Milestones)
A record of a not-yet-met control with a plan to fix it, permitted for a Conditional submission. POA&M legality is strict: only 1-point controls may be deferred. Deferring a 3- or 5-point control, or one of six specifically excluded 1-pointers, sets `valid_submission=False` regardless of the numeric score.
> In this repo: `src/compliance_engine/traceability/sprs.py`.

### P-Plan
The plan-and-execution provenance ontology used to express the full compliance chain. Each step — contract, obligations, controls, COP, Order, evidence, oracle assertions, attestations, and the BOM/SSP — is modeled as a p-plan Variable realized by an Entity, giving an end-to-end, traceable provenance graph (with an upstream `ce:SOP-ORDER-COMPILE` plan). A `check_sop_adherence` deviation check flags divergence from the declared plan. See also **audit package** and **provisioning**.
> In this repo: `src/compliance_engine/traceability/provenance.py`; `plan.ttl`.

### PROV-O
The W3C Provenance Ontology, one of the standards the vocabulary is assembled from. PROV-O supplies the provenance model that records who or what produced each artifact and how.
> In this repo: assembled in `src/compliance_engine/ontology/prefixes.py`.

### provisioning
Building the environment. In this engine, provisioning and proving are the same action: the environment is described by a signed Order, and the proof of compliance is produced from that same description rather than gathered afterward by inspection. See [00-what-is-this.md](00-what-is-this.md).

---

## R

### reference
A resolvable pointer into an authoritative source. A reference carries a URI, a freshness window (`ce:freshnessDays`), a last-verified timestamp (`ce:lastVerified`), and a named custodian. References are not resolved live yet; today they resolve against local files and fixtures.
> In this repo: modeled as `ce:Reference`; demo references in `data/structural/references.ttl`.

### registry
The write-once, content-addressed object store, plus a two-level index (contract -> BOM -> artifact hashes). Every artifact is stored by its hash so it can be re-resolved and re-hashed during reproduction.
> In this repo: `src/compliance_engine/pipeline/registry.py`; output under `artifacts/registry/`.

### Rekor
The transparency-log component of the Sigstore toolchain, which would provide a tamper-evident public record of signatures. It is deferred, and would be self-hosted if ever adopted. See also **cosign + KMS** and **Sigstore**.

### residency gate
A hard policy gate in the runtime that halts the run before apply if any planned region is non-US, or if the plan carries no region signals at all. It is the safety valve that prevents building in a disallowed location. A residency-gate halt exits with code 1 and applies nothing.
> In this repo: enforced in `src/compliance_engine/pipeline/runner.py`. See [02-the-factory.md](02-the-factory.md).

### role (and the four roles)
The role a signer must hold for their attestation to count. A non-Affirming-Official signer must match the module's required role; the Affirming Official can attest regardless. The four roles are: Affirming Official (`Role_AffirmingOfficial`, may attest anything and carries the legal liability), Security Officer (`Role_SecurityOfficer`), IT Administrator (`Role_ITAdmin`), and Operations (`Role_OPs`: personnel, maintenance, records).
> In this repo: enforced by `src/compliance_engine/oracles/attested_reference.py`. See [03-machine-vs-human.md](03-machine-vs-human.md).

---

## S

### SBIR
The Small Business Innovation Research program, a U.S. federal program under which small contractors receive research awards. A contractor working such an award and handling CUI is exactly the kind of organization CMMC Level 2 applies to.

### SHA-256
The 256-bit hash function used throughout the engine to fingerprint objects. Orders, evidence, BOMs, and registry artifacts are all named by their SHA-256, which is what makes content-addressing and proof by reproduction work. See also **hash** and **content-addressing**.
> In this repo: `src/compliance_engine/pipeline/evidence/hashing.py`.

### SHACL
The Shapes Constraint Language, one of the standards the vocabulary is assembled from. SHACL shapes enforce well-formedness invariants on the data. For example: an attestation marked met must carry both an adequacy statement and a sufficiency statement, and only a 1-point control may carry a POA&M item.
> In this repo: shapes in `data/ontology/cmmc_shapes.ttl`.

### signed-artifact oracle
The oracle kind that checks a detached signature over an artifact, used for signed documents. It is one of the three oracle kinds alongside config-check and attested-reference.
> In this repo: `src/compliance_engine/oracles/`.

### Sigstore
The signing toolchain (with its `cosign` tool and its `Rekor` transparency log) intended to provide the production cryptographic-signing path for attestations. It is the deferred production path (`sig_algo="cosign-v1"`, cosign + KMS); Rekor is deferred. Attestation signing itself is already real today via Ed25519, not Sigstore. The Order, separately, is "signed" by SHA-256 hash-reference. See also **Ed25519 / attestation signing**, **cosign + KMS**, and **Rekor**.

### SPRS (Supplier Performance Risk System)
The government scoring system for supplier compliance. The engine computes an SPRS score as 110 minus the sum of the weights of the controls that are not met (weights are 1, 3, or 5). A score of 110 is Final; 88 to 109 is Conditional (permitted with a POA&M); below 88 is Ineligible. The score is computed over the Order's required set (22 controls for NV012), not all 110. The engine does not talk to SPRS; a human files the computed score at the government portal.
> In this repo: `src/compliance_engine/traceability/sprs.py`. See [04-the-proof.md](04-the-proof.md).

### SSP (System Security Plan)
The deterministic document that describes how the organization satisfies each requirement. It is compiled from the same dataset the BOM records, and its centerpiece is the per-control traceability matrix (also called the VCRM). When inputs are mock, it emits the NON-EVIDENTIARY banner structurally.
> In this repo: `src/compliance_engine/documents/ssp.py`; output `ssp.md`. See [04-the-proof.md](04-the-proof.md).

### SysML v2
One of the standards the vocabulary is assembled from. SysML v2 supplies the structural-model and requirements terms: a control is modeled as a requirement, and each module is a part usage that satisfies one or more controls. In this repo: used throughout `data/structural/tier1.ttl`; bound in `src/compliance_engine/ontology/prefixes.py`.

---

## T

### Terraform
The infrastructure-as-code tool used to describe and plan the environment. The runtime runs a real `terraform plan` against mock providers, so the plan is genuine but nothing is deployed; live apply is deferred.
> In this repo: `infrastructure/terraform/tier1/`.

### Tier 1
The baseline set of modules the engine ships with: 10 modules covering 22 controls (20 machine-verified plus 2 CSP-inherited). It is the foundation the Track A and Track B modules build on.
> In this repo: `data/structural/tier1.ttl`; Terraform in `infrastructure/terraform/tier1/`; demo attestations in `data/attestations/tier1.jsonl`.

### Track A / Track B
The two groups of modules added on top of the Tier 1 baseline. Track A is the machine-verified set: 13 modules covering 45 controls (for example VPC segmentation, endpoint detection, mobile-device management, Security Command Center, Workspace admin policy, BeyondCorp remote access, GitHub change management, operations MFA, Cloud Logging, Binary Authorization allowlisting, session control, VPC Service Controls, and IAM privileged-use). Track B is the attested-reference set: 16 modules covering the 43 policy-and-records controls (for example training, incident response, risk assessment, personnel security, configuration management, maintenance, media protection, audit procedure, security engineering, remote-access authorization, physical access, collaborative computing, separation of duties, continuous monitoring, and login banner).
> In this repo: modules in `data/structural/tier1.ttl`; the Track B policy scaffolding in `src/compliance_engine/documents/policies/`.

---

## V

### VCRM
The Verification Cross-Reference Matrix, another name for the per-control traceability matrix that is the centerpiece of the SSP. It maps each control to the module, evidence, oracle outcome, and attestation that support it.
> In this repo: emitted by `src/compliance_engine/documents/ssp.py`. See [04-the-proof.md](04-the-proof.md).

### verification vs validation
Two different questions. Verification asks whether the machine-measurable facts check out (an automatic assertion from an oracle). Validation asks whether a human judges the requirement to be satisfied (a manual assertion, an attestation). The founding principle sets the boundary between them: "Evidence does not verify requirements; evidence supports a human judgment that requirements are satisfied." A control is met only when both hold.
> In this repo: see [03-machine-vs-human.md](03-machine-vs-human.md).

---

## Summary

This glossary is the shared vocabulary for the rest of the tour. Two ideas anchor it: provisioning and proving are the same action, and every control (machine-measurable or human-only) is checked the same way through the attested-reference model. The founding principle sits underneath both: evidence supports a human judgment, and a named, role-appropriate human carries the accountability for the claim.

Back to the tour index: [README.md](README.md).
