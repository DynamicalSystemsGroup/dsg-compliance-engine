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
- [ ] Wire `GCSBackend` (IL4 registry) and the GitHub PR + OIDC approval gate as the Stage-6 boundary.
- [ ] First real attestation session: the Affirming Official walks the coverage matrix; MET/NOT MET recorded as EARL outcomes with gap notes. Output feeds the SPRS self-assessment.

**Exit:** a signed BOM mapping ≥50 controls to evidence hashes; no Tier 1 secret/state stored in Tier 0.

## Phase 2 — SPRS + C3PAO hardening (weeks 5–6)

- [ ] `traceability/sprs.py`: SPRS-score audit + **POA&M-legality gate** (hard-fail any 3-/5-point control on a POA&M).
- [ ] Bolt on Sigstore cosign + Rekor (content authenticity) — required before handing a C3PAO re-executable evidence.
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

~40 of 110 controls (policy, training, PS, IR, physical) are **not machine-checkable** and resolve to `earl:cantTell` — they must be human-attested from documentary evidence. The engine's value there is the audit trail and the always-current SSP, not automation. Do not oversell auto-coverage.
