# Roadmap

Phased buildout. Reconciles the requirements doc §18 phasing with the fork-the-demo strategy from `reference/concepts/adcs-to-cmmc-compliance-engine.md` §5, against the hard dates in `reference/guides/cmmc-bidding-plan.md` (proposals due **2026-07-22**; CMMC Phase 2 / mandatory C3PAO **2026-11-10**).

Strategy: **fork the ADCS engine, don't greenfield.** Each phase names concrete reuse.

## Phase 0 — Fork & re-skin the Factory (days 1–5)

Runs parallel to the 5-day Tier 1 enclave build (`reference/guides/tier1-buildout-plan.md`).

- [ ] Fork `ADCS-lifecycle-demo` structure into this repo's module layout.
- [ ] Author `ontology/cmmc-edit.ttl` from the **Control Catalog** — all 110 controls, weights, POA&M flags. _Highest-leverage day: Document 1 becomes Turtle._
- [ ] Replace the satellite structural model with the Tier 1 topology stub (`structural/tier1.ttl`), tagging each module with the controls it claims.
- [ ] Stand up the Factory (`pipeline/`) with **mocked** provisioning steps (mocked terraform + mocked evidence generators — ADCS `--auto` path): feed a hand-written Order, run the loop, produce a first compiled SSP + BOM with every control `PLANNED`.

**Exit:** the Factory consumes an Order and emits a byte-deterministic SSP + BOM listing all 110 controls, with the **Gate 2** audit running against the Order's required-control set.

## Phase 0.5 — Order Compiler skeleton (days 3–7, overlaps)

The separate upstream tool (`order-compiler/`).

- [ ] Clause library: DFARS/ITAR clause → obligation (7012 ⇒ CUI/800-171, 7021 ⇒ CMMC status, ITAR ⇒ US-person/residency/e2e).
- [ ] Rule library: obligation → required control set.
- [ ] COP flow for **NV012**: AI drafts obligations from the contract, Compliance Officer attests → resolve controls → resolve modules → **Gate 1** coverage → emit a signed Order.
- [ ] Reusable Contract Profile `DLA-SBIR-CUI-ITAR-Phase1`; instantiate NV011 from it (deltas only).

**Exit:** an Order for NV012 is _compiled_ (not hand-written) and passes Gate 1; the Factory runs it end-to-end.

## Phase 1 — Real Tier 1 evidence (weeks 2–4)

- [ ] Implement config-export + policy-as-code generators for the **63 non-deferrable** controls first, then toward the 50+ success-criterion target.
- [x] Attested-reference oracle wired into the run path with teeth (`oracles/attested_reference.py`, `pipeline/runner.py` `_run_attested_reference_pass`): Track B (policy/human) controls are now gated MET on the oracle passing (reference registered, resolves to a real file, fresh, role-signed), emitting `passed`/`needsAction`/`failed`. `pipeline/evidence/doc_evidence.py` resolves each control's `ce:Reference` to the real document on disk, SHA-256 hashes it, captures the git commit that last changed it, and signs an upload receipt (local Ed25519 dev signer), binding a `ce:DocumentEvidence` node into the evidence graph. This adds the BOM `attested-evidenced` backing. Evidence remains fixture/mock (runs stay NON-EVIDENTIARY).
- [x] No control is MET without a concrete result: every machine control now has both a config criterion **and** a mock evidence fixture feeding it (`oracles/criteria.py` + `fixtures/nv012/all-covered/`), CSP-inherited controls carry an explicit `ce:inherited` outcome, and any control that would otherwise have no result is attested `needsAction` (never silently MET). Scenario fixture sets **layer** over `all-covered` (a scenario is "all-covered but these files changed"). Over `ce demo --full` the backing distribution is 65 machine / 43 attested-evidenced / 2 CSP-inherited; the default NV012 slice scores 110/Final with 20 machine-proven + 2 inherited.
- [x] Append-only, versioned Flexo MMS store backend landed (`pipeline/backends/flexo.py`, `--store-backend flexo`) — **offline-simulated** via a deterministic `FakeFlexoStore`; a live in-enclave Flexo server is still deferred. The local write-once registry remains the cache/fallback tier.
- [ ] Wire `GCSBackend` (IL4 registry) and the GitHub PR + OIDC approval gate as the Stage-6 boundary.
- [ ] First real attestation session: the Affirming Official walks the coverage matrix; MET/NOT MET recorded as EARL outcomes with gap notes. Output feeds the SPRS self-assessment.

**Exit:** a signed BOM mapping ≥50 controls to evidence hashes; no Tier 1 secret/state stored in Tier 0.

## Phase 2 — SPRS + C3PAO hardening (weeks 5–6)

- [ ] `traceability/sprs.py`: SPRS-score audit + **POA&M-legality gate** (hard-fail any 3-/5-point control on a POA&M).
- [x] Cryptographic attestation signing landed: real Ed25519 signatures via the `compliance_engine.signing` package (`Ed25519LocalSigner` dev key, `NullSigner`, `CosignKmsSigner`). Attestation records carry `sig_algo` in `{none, ed25519-v1, cosign-v1}`; signed records are verified at load and **fail closed** (a tampered/unverifiable signed record is rejected). The demo still runs `sig_algo=none` (git-trust) and stays NON-EVIDENTIARY.
- [ ] Bolt on Sigstore cosign + FIPS-KMS signing (the production key path) + Rekor (content authenticity) — required before handing a C3PAO re-executable evidence. cosign+KMS is implemented behind a probe (switches on when the cosign binary + KMS key are present); Rekor remains deferred (and if adopted would be self-hosted in-enclave for CUI, never the public instance).
- [x] Full-chain P-Plan provenance landed (`traceability/provenance.py`, `plan.ttl` extended with an upstream `ce:SOP-ORDER-COMPILE` plan + Variables): the whole lineage (contract → obligations → controls → COP → Order → evidence → oracle assertions → attestations → BOM/SSP) is modeled as p-plan Variables realized by Entities, with a `check_sop_adherence` deviation check.
- [x] Signed audit package landed: `ce package` builds and signs a manifest bundling the BOM, SSP, audit + SPRS, full-chain provenance, the per-control control→attestation→signed-policy chain, and the signed-policy inventory; `ce verify-package` re-verifies it offline (manifest signature + artifact re-hash + chain). Code: `traceability/package.py`.
- [x] Audit-package report landed: `ce package` renders the human report into `package/` (a mixed-audience `report.html` that opens with a plain-language verdict, glossary, and family-level coverage rollup, then moves the per-control tables to appendices), plus a paged `report.pdf` when the `weasyprint` binary is present. `ce report` (and `ce demo --report`) re-renders it on demand. Code: `documents/report.py`.
- [x] Full-catalog demo: `ce demo --full` requires the entire 110-control NIST SP 800-171 catalog (ALL-110 expansion) instead of the NV012 22-control slice, scoring 110/Final over all 110.
- [ ] Wire the Terraform reproducibility loop (ADCS `compute.reproduce` retargeted): rebuild + diff live state vs. recorded state for the `/verify` path.

**Exit:** an internal SPRS score ≥88 (target 110) with a legal POA&M; a C3PAO can retrieve a BOM and re-execute.

## Phase 3 — Tier 2 (IL5 / ITAR) (weeks 7–10)

- [ ] `AzureBlobBackend`; GCC High / Azure Gov structural model; IL5/ITAR oracles (US-region, US-person key admin, FIPS HSM CMVP).
- [ ] Cross-tier flow: Tier 1 submits an Order; Tier 2 returns only the BOM hash (named-graph + auspices model across two clouds).

**Exit:** architecture supports Tier 2 without redesign; first Tier 2 Order provisions a GCC High workspace + Azure Gov resource group.

## Phase 4 — Continuous compliance (weeks 11+)

- [ ] Drift detection + re-provisioning on policy change.
- [ ] KOI-Net ingestion of BOMs as knowledge-graph nodes for real-time posture queries.
- [ ] Extend to FedRAMP High / other frameworks via new Order types + module sets.

---

### Honest limits

~40 of 110 controls (policy, training, PS, IR, physical) are **not machine-measurable** in the config-check sense — their substance is the human's judgment, not a metric. The attested-reference oracle gates them on a machine-recorded document reference (resolved, hashed, git-tracked, role-signed), so a stale or missing reference produces a real `needsAction`/`failed` and a non-MET control, and the BOM records them as `attested-evidenced` rather than bare `human-only`. What the engine still does not do there is judge whether the policy is actually good — it checks the bureaucratic facts, not the substance. And every "passing" machine control passes over **mock fixture evidence**, not a live system: the demo proves the pipeline end to end, not a real posture. Do not oversell auto-coverage.
