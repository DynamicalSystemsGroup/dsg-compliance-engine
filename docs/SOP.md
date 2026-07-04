# Practical guide: how your org would actually run this

Setting aside architecture and code, here's what daily life looks like if you adopted this repo. I'll assume you've never used it and don't do compliance for a living.

## 1. What this repo actually IS

Two things, glued together:

**(a) A signed record of every claim your organization makes** about how it satisfies CMMC L2. Not the SSP as a Word document — the underlying data the SSP is _derived from_. Modules ("we do 2FA on the CUI OU"), references ("the training records live in KnowBe4 at this URL"), attestations ("the Affirming Official signed off on 2026-06-20 that this is true"). Everything content-hashed and cross-linked in RDF.

**(b) A one-command pipeline** that takes a signed contract obligation profile (COP) as input and produces a submittable SSP + BOM (Bill of Materials of evidence) + SPRS score as output. Deterministic — same inputs, byte-identical outputs.

The point isn't "we replaced the SSP writer." It's "we turned compliance from a periodic-scramble-with-Word-templates into a git-tracked artifact your engineers can reason about like code, and your auditor can re-execute."

## 2. Where it lives

**Physically:**

- **One private GitHub repo per environment.** For DSG that's likely one repo covering the Tier-1 IL4 CUI enclave. If you later win a Tier-2 (IL5/GCC High) contract, that becomes a _separate_ repo with its own tier2.ttl, its own attestations, its own signed run history. Cross-tier only exchanges BOM hashes.
- **Branches:** `main` (submittable state), feature branches for policy churn (`add-ir-plan-v2`, `refresh-training-records-2027`), and a `submissions/YYYY-QQ` tag for every SPRS filing.
- **Not a monorepo with your product code.** This lives alongside your product code but stays out of it. Compliance state changes on a very different clock than product state.
- **Runs on your laptop or a CI runner.** No servers. `uv run ce demo` produces the output directory. CI can re-run on every commit to catch drift.

**Who has access:**

- Full commit access: you (AO), Security Officer, IT Admin. Small circle.
- Read access: Ops, contract managers.
- Read access at audit time: your C3PAO. They clone the repo and re-run it.

**Not in the repo:**

- Real credentials (GCP service account keys, GitHub tokens). Those live in a secrets manager and get injected as env vars for the "live evidence" resolvers when they run.
- The authoritative sources themselves. KnowBe4 completion records live in KnowBe4. The repo just points at them via `ce:Reference`.
- Employee PII. Background checks, offboarding tickets — those live in your HRIS. The repo references them by URL/ID + a custodian name.

## 3. The workflow — who does what, when

Four rhythms, each on a different clock. Everyone's in the same repo but nobody touches everything.

### 3a. Every commit (product engineers) — automatic

You've committed a config change. CI runs `uv run ce demo --evidence-set all-covered`. If your commit introduced a non-US GCP region, or dropped a firewall rule, or removed a module claim, the residency + Gate-1 gates halt and CI turns red. This catches drift _when it happens_, not at audit time.

Engineers don't need to know CMMC. They see a red build; they revert; done.

### 3b. When a policy changes (Security Officer / Ops) — event-driven

Training curriculum revised. IR plan updated. Vendor list refreshed. The workflow:

1. Edit the Markdown file under `documents/policies/` (or update the URL in `structural/references.ttl` if the doc moved).
2. Update the reference's `ce:lastVerified` timestamp.
3. Append a new AO attestation record to `attestations/tier1.jsonl` — one JSON line, signed. The old record stays; you never mutate history.
4. Commit. CI reruns the pipeline. If the policy still passes the oracle (fresh, attested by the right role), the build is green.

Cycle time: 20 minutes if the policy is already written.

### 3c. Every quarter (Security Officer) — proactive

Run `uv run ce demo` locally with today's date. Any references past their freshness window flip to `NEEDS_ACTION` with a specific reason ("stale: 172d>90d"). You get an actionable list of what needs a refresh. Fix them, get attestations, commit. This is the "keep the SSP always current" loop.

For your event-based references (offboarding tickets, media sanitization records), you're not on a clock — you re-attest when the event happens. But the quarterly run surfaces missing events too (e.g., "the offboarding for last month's contractor termination has no attestation record yet").

### 3d. Every three years, or at contract award (AO) — submission

This is the big one — SPRS filing.

1. Confirm your contract's COP is up to date (the `cop_draft.ttl` for this contract).
2. Run `uv run ce demo --evidence-set all-covered` one more time with a locked timestamp.
3. Run `uv run ce verify` — it does a hard tamper check (re-hashes evidence) plus the SHACL closure suite (advisory on NON-EVIDENTIARY runs).
4. Run `uv run ce package` to build and sign the audit deliverable (the signed manifest over BOM, SSP, audit + SPRS, full-chain provenance, and per-control chains); `uv run ce verify-package` re-verifies it offline.
5. Copy `output/ssp.md`, `output/bom.json`, the signed audit package, and the score to a submission tag: `git tag submissions/2026-Q3`.
6. Go to sprs.pmrt.mil, enter the score. Retain the SSP in contractor records. Notify the CO per DFARS 252.204-7020.

The engine produces the artifacts. You still have to click the buttons at sprs.pmrt.mil — no way around that.

## 4. What you hand the auditor

CMMC L2 self-assessment: you submit your own score, the C3PAO is optional (until the contract requires it). Even the self-assessment gets audited eventually. Here's what you show them.

**The digest (5 minutes):**

- `output/ssp.md` — the generated System Security Plan, all 110 controls, plain English.
- `output/bom.json` — the Bill of Materials. For each control: what module claims it, what evidence, what attestation, hashes.
- SPRS score printout with the date and Affirming Official name.

**The proof (2 hours):**

- Read access to the repo. They browse it themselves.
- Show them the git log: every reference update, every attestation, every module change is a commit with an author and a timestamp.
- Run `uv run ce demo` in front of them. It's deterministic; they see the same hashes you signed.
- Every `ce:Reference` URI resolves — they click the training LMS link, they see the report; they open the IR plan Markdown, they see the plan.
- Every `attestations/tier1.jsonl` line names a signer, a role, a date, and carries a cryptographic signature (Ed25519 today) that is verified at load and fails closed on tamper. Cosign + KMS (Phase 2) adds the production key path.
- You hand them the signed audit package: run `uv run ce package` to build and sign a manifest (BOM, SSP, audit + SPRS, full-chain provenance, per-control control-attestation-policy chain, signed-policy inventory), and they run `uv run ce verify-package` to re-verify it offline (signature + artifact re-hash + chain).

**The re-execution (their comfort level):**

- A C3PAO who wants to be thorough clones the repo, runs `uv run ce demo`, compares byte-for-byte against what you submitted. Any drift is a red flag. This is the whole point of the deterministic build.
- For contested claims (they say "prove this Firewall rule was deployed on 2026-05-14"), they trace the module → reference → the git commit that updated the reference → the authoritative source at that commit's URL/RID.

**What auditors specifically care about that this handles well:**

- Traceability. Every "MET" has a signed statement pointing to a resolvable artifact, dated, by a named signer in a role.
- Separation-of-duties smells. They can see IT-Admin never signed HR-domain evidence, HR never signed technical config claims.
- Non-repudiation. Attestations are signed; the git history is immutable; hashes chain.
- Freshness. They see your training records are inside the 365-day window; they see your log-review cadence is inside 90 days.

**What they'll still want that this doesn't produce:**

- Face time with the AO. They'll interview you. The engine won't answer questions.
- Sample tests. They'll spot-check individual controls end-to-end. The engine tells them where to look; they still look.

## 5. Multi-contract, multi-repo scaling

You'll have more than one contract. Sometimes across tiers. Here's the model.

**One repo per compliance environment, one COP per contract.**

- The Tier-1 IL4 CUI enclave is one environment. All CMMC-L2 CUI contracts you run there share the same tier1.ttl, the same modules, the same attestations. What differs per contract is the _COP_: which obligations that contract imposes.
- NV012 has its `cop_draft.ttl`. Contract NV013 gets its own `cop_NV013.ttl`. The rule library resolves NV013's obligations to a required-control set (may be a subset of the 110 if it's not full CMMC-L2, may add ITAR markers if it's ITAR-covered). You run `cli run --order cop_NV013.ttl`; you get NV013's SSP + BOM + score against the SAME environment attestations.
- The environment work (attestations, references, module updates) is done ONCE and reused across every contract in that environment. This is the compounding value — attestations amortize.

**When you win a Tier-2 contract (IL5, GCC High, ITAR-heavy):**

- New repo: `compliance-engine-tier2`. Different structural model, different provider modules, different attestations. The engine machinery (ontology, oracles, freshness, store) is shared as a Python dependency or a shared vendored copy.
- Cross-tier: a Tier-1 contract that submits work into a Tier-2 environment references the Tier-2 BOM hash only. Named-graph model in the RDF — you never leak Tier-2 state into Tier-1 or vice versa.

**Multiple product repos:**

- Product code stays in product repos. The compliance repo watches specific hashes / branch-protection settings on those product repos via the GitHub API (that's what `ChangeManagement_GitHub` module already does).
- One compliance repo can attest across many product repos. The reference `ce:REF_ChangeMgmt` points at "the branch-protection config on this list of repos"; the resolver checks all of them.

**Automation for many contracts:**

- Scheduled CI job (nightly): pull latest state from every authoritative source, refresh references, run the pipeline against every COP in `cops/*.ttl`, publish updated SSP/BOM/SPRS to an internal dashboard.
- Contract-award workflow (event-driven): a new contract lands, contract manager files the DFARS/ITAR clauses into a new COP TTL, the Order Compiler emits a required-control set, Gate 1 tells you within seconds whether your environment already covers it. If yes, you're compliant on day one. If no, you get a precise list of gaps and can decline the contract, negotiate scope, or add environment controls before signing.

That last part is where this stops being a compliance tool and starts being a contract-underwriting tool. A five-second answer to "can we take this contract without new investment" is worth more than any SSP.

## 6. What this does NOT do (honest limits)

Read this section twice.

- **It does not make you compliant.** It records claims. If you claim training is complete and it isn't, the engine passes and the C3PAO catches you. § 1001 liability is on the AO signature, not on the tool.
- **It does not resolve references live yet.** Today all references resolve against `file://` paths or a fixture URI. The "call the KnowBe4 API and confirm this report exists" resolver is a phase-2 build.
- **It signs attestations cryptographically.** Real Ed25519 signing (`sig_algo="ed25519-v1"`) is wired via the `compliance_engine.signing` package; signed records are verified at load and fail closed on tamper. The demo runs `sig_algo="none"` (trust the git history), which is still NON-EVIDENTIARY. Cosign + FIPS-KMS (`sig_algo="cosign-v1"`) is the deferred production signing path.
- **It does not talk to SPRS.** SPRS has no public API. You still copy-paste the score into their web form.
- **It doesn't handle contracts across CMMC L1 or L3.** Just L2 today. The framework generalizes; the catalog doesn't.
- **It doesn't write your policies.** The Markdown documents under `documents/policies/` are placeholder scaffolding a subagent generated. YOU need to replace each with your organization's actual, adopted, followed policy. If your training program is real, the doc reflects real curriculum; if it isn't, no signature makes it real.
- **It doesn't fix bureaucratic decay.** If Ops stops updating offboarding tickets, the engine reports `NEEDS_ACTION`, then eventually stale references, then failing controls. Green builds require ongoing discipline. The tool amplifies discipline; it doesn't create it.
- **It cannot substitute for a real security program.** If you actually don't run backups, don't segment your network, don't offboard people — you'll fail the audit even with beautiful signed attestations. The engine is a bookkeeping system for an organization that is already doing the work.

## 7. If you started today (a real plan)

Assuming you (DSG) decide to adopt this on 2026-07-04:

**Week 1 — Fork and calibrate.**

- Fork the repo. Rename to `dsg-compliance`.
- Replace the 16 placeholder policy docs under `documents/policies/` with your _actual_ current policies. Some of these may not exist yet — that's data. Track them as gaps.
- Update `structural/references.ttl` custodians with real people, not "Operations lead."
- Update `attestations/tier1.jsonl` — remove the fixture AO signatures. You'll write real ones as policies are actually adopted.
- Delete Track A fixture JSONs for services you don't actually use (CrowdStrike, BeyondCorp, etc.). The engine will report `NEEDS_ACTION` for those controls. Good — that's honest.

**Week 2–4 — Fill in the real state.**

- For each policy module: either write the missing policy, adopt an existing draft, or decide to POA&M it. Attest what's real; don't attest what isn't.
- For each Track A machine module: confirm the underlying configuration is actually deployed. If your VPC segmentation is really default-deny, keep the module; if not, either fix the config or drop the module and POA&M the controls.
- Update `cop_draft.ttl` (or write a per-contract COP) reflecting your actual current contracts.

**Week 4 — First honest run.**

- Run `uv run ce demo` with your real data. Look at the SPRS score. It's probably NOT 110. That's the point — you now know exactly where you stand.
- Every `NEEDS_ACTION` and `FAIL` is a punch list. Work it.

**Week 6 — Wire the automation.**

- GitHub Actions running `uv run ce demo` on every commit.
- A nightly job that refreshes references (once resolvers exist) and pings you if anything went stale.

**Month 3 — Consider first live evidence resolver.**

- Pick your highest-value reference (probably LMS training records) and write a Python resolver that calls its API, updates `lastVerified`, and commits.
- Now that reference is truly live and self-freshening.

**Month 6 — Self-assessment.**

- Fresh run. Real score. File it in SPRS.
- You now have quarterly cadence baked in and a repo any auditor can re-execute.

**Month 9+ — Second contract.**

- New COP, existing environment. Instant Gate-1 answer on whether your compliance posture covers it. This is the moment the compounding kicks in.

---
