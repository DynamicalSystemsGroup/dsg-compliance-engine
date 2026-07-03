# Approachability Audit

**Date:** 2026-07-02 · **Branch:** `feat/nv012-engine`
**Method:** Four independent auditors, each adopting the persona of a competent engineer who has never seen this repo and knows nothing about CMMC: (1) first-contact experience + conceptual load, (2) structure + end-to-end flow traces, (3) documentation accuracy/layering/redundancy, (4) accidental vs. essential complexity. Findings were verified against code with file:line references; the demo was actually run by two auditors independently.
**Scope:** understandability only — not code style, test quality, or security.

---

## Verdict

**The repo is better than you fear, but it presents worse than it is.** The system itself is coherent, the code is mostly flat and well-commented, the quickstart is flawless (all three demo scenarios ran first try, deterministically, with output matching the docs byte-for-byte including hashes), and a genuinely excellent plain-English tour already exists in `docs/v1/`. The complexity is roughly **70% essential / 30% accidental** — the RDF/EARL/PROV core is the product, not ceremony.

The problem is **routing and rot, not writing**. Specifically:

1. **The front door hides the good material.** `docs/v1/README.md` says "Start here" — and nothing in the repo links to it. `grep -rn "docs/v1" README.md ARCHITECTURE.md ROADMAP.md` returns zero hits. A newcomer lands on `README.md:5` ("a signed BOM that doubles as the SSP" — neither acronym defined) and bounces.
2. **The layer newcomers reach for first is the least trustworthy.** All 10 per-module `DESIGN.md` files are frozen pre-implementation port plans: they call fully-built modules "stubs," name functions and files that don't exist, and use a retired `rtm:` vocabulary.
3. **Internal plan codenames (R13, U12, U1–U14) leak into user-facing docs, CLI help, and program output**, and the plan document that defined them was deleted on this branch.

Time-to-mental-model via the intended path (docs/v1 → run the demo): **~45–60 minutes.** Via the actual front door today: **3+ hours with backtracking**, with a real risk the reader wrongly concludes they must first study CMMC and a sibling repo (ADCS) that isn't even in this repo.

**Presentable as-is? Not to a fresh audience.** Presentable after one day of doc-only fixes (shortlist below)? **Yes, comfortably** — because the hard part (good explanatory material, a working demo) is already done.

---

## Findings, ranked by how badly each confuses a first-time reader

### Blockers

**F1. `docs/v1/` is undiscoverable.** The best onboarding asset in the repo (~1,240 lines of plain-English tour with a real glossary) is linked from nowhere. Same for `docs/AUDITOR-GUIDE.md` and `docs/ACCEPTANCE.md` — referenced zero times from any root doc.
*Fix:* One line at the top of `README.md`: "**New here? Read the [plain-English tour](docs/v1/README.md) first.**" Plus a short "Documentation" routing section (operator → README demo; newcomer → docs/v1; assessor → AUDITOR-GUIDE; developer → ARCHITECTURE + AS-BUILT). This is the single highest-leverage change in the repo.

### Major

**F2. The DESIGN.md layer is active misinformation.** All 10 module `DESIGN.md` files describe the *planned* system, not the built one: `pipeline/DESIGN.md:49-50` calls `runner.py` a "stub" (fully implemented); `oracles/DESIGN.md` says "criteria.py (stub present)" (7 real criteria); `evidence/DESIGN.md` names functions (`bind_check_evidence`) that don't exist (actual: `bind_evidence`) and uses the retired `rtm:` vocabulary; `evidence/generators/DESIGN.md` lists nine generator files (`checkov.py`, `trivy.py`, `opa.py`…) where three exist. A newcomer opens a module directory, reads DESIGN.md first (the obvious move), builds a wrong model, then distrusts *all* the docs.
*Fix (10 minutes):* add a banner to each: "⚠️ Historical design note (pre-implementation). For what actually exists, see `docs/AS-BUILT.md`." Better: delete them — AS-BUILT's component map already does their job accurately.

**F3. README opens at insider altitude and never defines its own headline terms.** BOM and SSP used at `README.md:5` before definition; the diagram block (`README.md:16-36`) introduces SBIR, DFARS, COP, Gate 1/2, C3PAO, EARL with no definitions and no glossary link. **NV012 — the name of the demo — is never defined in the README or the glossary** (first definition: `docs/v1/01-the-order.md:6`). SBIR is never defined anywhere in the repo. The glossary (`docs/v1/06-glossary.md`) covers ~35 of the ~40 concepts in the README path — but the README never routes to it.
*Fix:* one parenthetical per acronym at first use; "NV012 (an example DoD SBIR contract — the demo's input)"; add NV012, SBIR, ADCS to the glossary; link the glossary under the diagram.

**F4. ADCS is load-bearing and never explained.** Two README sections (`README.md:52-60`) and five spots in ARCHITECTURE.md lean on "the ADCS substrate." ADCS is never expanded, is not in the glossary, and the link `../ADCS-lifecycle-demo` points outside the repo — dead for anyone who clones only this one. A newcomer cannot tell whether they must read that other repo first (they don't).
*Fix:* one sentence: "ADCS-lifecycle-demo is a prior internal project (satellite requirements traceability) whose engine this repo reuses; you don't need it to understand or run this repo."

**F5. Internal plan codenames leak everywhere, and their defining document is deleted.** R1–R13 / U1–U14 appear ~70+ times: in README (`:93,114,124,133,140,151,156`), docs/v1/05 output, module docstrings, CLI `--help` ("graceful skip if U12 absent"), and even **program output** (`Contradictions (R13): 1`). The plan that defined them (`docs/plans/2026-07-02-001-…`) is deleted on this branch; `docs/AS-BUILT.md:89` still says "The plan defines R1–R13," pointing at nothing, and `AS-BUILT.md:6` cites a `results/agent-*.md` directory that doesn't exist.
*Fix:* user-facing text and program output say the plain name ("unjustified human-over-machine contradiction" instead of "R13"); add a 15-line R#/U# legend to AS-BUILT; strip "U12" from CLI help.

**F6. Status docs contradict each other and the code.** `docs/AS-BUILT.md:137` says the demo's SSP step "is currently a stub hook"; `cli.py:253-279` renders the real SSP every run (verified live), and same-day `docs/ACCEPTANCE.md:26` says the opposite ("SSP wiring has landed — not a stub"). `AS-BUILT.md:6-9` describes a SHACL shape fix as "queued" that is already in `ontology/cmmc_shapes.ttl:298-307`. README's artifact table (`:137-143`) omits `ssp.md`, which the demo writes. ROADMAP.md has every checkbox unchecked, including shipped, acceptance-verified items — while README:91 says "Runnable. The full chain is implemented and tested." Two contradicting status docs kill trust in both.
*Fix:* update AS-BUILT's two stale claims, add `ssp.md` to the README table, delete the U12 caveat at `README.md:156`, check off ROADMAP items that shipped.

**F7. README/ARCHITECTURE overstate the storage backends.** `README.md:80` repo map: "`backends/` — Tiered write-once registry: GCS (Tier 1), Azure Blob (Tier 2)." Reality: top-level `backends/` contains **only a DESIGN.md**; the only backend code is `pipeline/backends/{base,local}.py`; no GCS/Azure backend exists anywhere (grep-verified). `ARCHITECTURE.md:132` colors the "GCSBackend" node **green = runs today**.
*Fix:* README row → "write-once registry (local today; GCS/Azure planned)"; recolor the diagram node amber; delete the top-level `backends/` directory (fold its tier table into `pipeline/registry.py`'s docstring or ROADMAP).

**F8. ARCHITECTURE.md contradicts itself on the Gates — the repo's most important concept.** The §1 mermaid (`:26-31`) labels the pre-apply policy check "GATE 2" and attestation "GATE 3"; §2's table, the README, plan.ttl, and all code call attestation "Gate 2." A newcomer using the architecture diagram as their map mislearns the central concept pair.
*Fix:* relabel the diagram nodes ("policy safety valve" / "GATE 2: fulfillment attestation").

**F9. `order-compiler/` is unimportable-by-name and reached via a sys.path hack.** The hyphen forces `cli.py:28-29` to do `sys.path.insert(...)` followed by bare `import compiler`, `import cop`, `import gate1` — un-greppable to source, invisible to IDE go-to-definition, and it puts shadow-risk generic names (`compiler`) on the global path.
*Fix (code, post-presentation):* rename to `order_compiler/` with `__init__.py`. Zero conceptual loss; removes the single most disorienting mechanism in the codebase.

**F10. `pipeline/plan.ttl` looks like it drives execution — it never runs.** Execution is ten hardcoded calls at `pipeline/runner.py:404-413`. plan.ttl is never loaded into the runtime dataset; the emitted `p-plan:correspondsToStep` IRIs dangle (no `ce:step-*` nodes in `output/engine.trig`), so the advertised "SPARQL can confirm every required step executed" (`plan_execution.py:5-7`) cannot work on a run's output. The stage list is maintained in **three synchronized copies** (plan.ttl, `plan_execution.py:45-56`, `state.py:134-145`) with "MUST stay in lockstep" comments.
*Fix:* load plan.ttl into `<ce:plan>` during `run_factory` (one call) so the provenance joins — or mark it documentation-only. Longer term, make it the single source the other two derive from.

**F11. "Why did control X pass?" has a surprising answer that no artifact explains.** In the demo, **every required control is attested MET unconditionally** by CLI code (`cli.py:204-218` hardcodes `OUTCOME_PASSED`); the oracle result never gates the attestation — it only feeds the R13 contradiction check afterwards. This is philosophically intended (humans attest; machines inform) and the design is honest about it — but the audit output doesn't say so, and the human-judgment logic lives in `cli.py`, not `traceability/` where a reader would look. Meanwhile "passed" means three different things (oracle `earl:passed`, attestation MET, audit forward-PASS) across four files, and the flagship SHACL shapes (`ontology/cmmc_shapes.ttl`) are **not in the runtime verdict path at all** — they run only in tests; the runtime R13 check is a Python reimplementation (`audit.py:266-302`).
*Fix:* one sentence in `audit.md`'s rendered header: "MET reflects human attestation; in demo mode all required controls are auto-attested — oracle results inform but do not gate." Longer term: wire `traceability/verification.py` (SHACL) into the demo/audit path, since machine-checkable shapes are the product's pitch.

### Minor (grouped)

**F12. Opaque or colliding names.** `oracles/` (testing term-of-art — earned, but a newcomer guesses "data feeds"), `structural/` (one data file; says nothing), `documents/` vs `docs/` near-collision (one is a document *compiler*), `cop.py` (opaque; "COP" collides with common usage), four names for two documents ("Document 1" = control catalog = "the law"; "Document 2" = traceability matrix = "VCRM" = "the evidence" — `README.md:62-66`). Keep the domain vocabulary (Order/Factory/Gate/oracle carry real content); pick one name per document and note aliases once in the glossary.

**F13. Dead-weight abstractions with one no-op implementation.** `StoreBackend` protocol (`pipeline/backends/base.py:22-90`): at runtime only `probe()`/`describe()` are called; `persist()` is test-only (the CLI persists via `_save_ds` directly); `get_backend()` is never called. ~140 lines a newcomer reads before discovering nobody persists through this interface. Contrast: `ProvisionBackend` (Fake/Terraform) is the *right* version of this seam — used every run. Simplify or wait for GCS to exist.

**F14. Triple state bookkeeping.** Run facts live in the RDF dataset, `PipelineState` dataclasses, *and* `run_state.json`, with a lossy reconstruction path (`cli.py:100-142`) that fabricates placeholder objects. Audit reads the graph; BOM reads state+graph; SSP reads graph+report+bom. Document per-artifact source-of-truth, or rehydrate from the graph (which was designed to be exactly this record).

**F15. Runtime-looking modules only tests execute.** `traceability/verification.py` (SHACL closure), `evidence/generators/terraform_plan.py`, `order-compiler/clause_library.py` — none called by the pipeline. A newcomer can't tell the live spine from the parked future without grepping call sites. One-line "RUNTIME: not called by the pipeline yet" docstring notes fix this cheaply.

**F16. Misc drift (each small, all easy).** Fixture README lists 5 oracle metric keys; `oracles/criteria.py` has 7; demo prints "6 oracle outcomes" — nothing reconciles the counts. `reference/document-binding.md` binds columns to the dead `rtm:` vocabulary. `reference/contracts/NV012-QA.md` actually contains **NV011's** Q&A. Preflight prints "persisted as output/engine.ttl + output/engine.trig" — `engine.ttl` is never written and the path ignores `--output-dir` (`pipeline/backends/local.py:47`). `README.md:78` "TBox" and `:87` "DSG" never defined. Duplicated `_local()` helper ×5 and EARL outcome-label maps ×3. Module→control mapping written up to four times (tier1.ttl satisfy-bnode + `cmmc:controlsSatisfied` + `_TIER1_PLAN` + Terraform labels) with no consistency check — Gate 1 queries one edge, the audit queries the other.

**What's genuinely good (checked, not vibes):** the quickstart runs perfectly and deterministically — even the hashes in `docs/v1/05-try-it.md` reproduce; runtime-behavior claims in the docs are accurate (CLI names/flags, test counts, control counts, exit codes all verified); `output/` is properly gitignored; `reference/` is correctly fenced as background ("not design of record"); the evidence-addresses / oracle-evaluates / human-attests vocabulary discipline is consistently enforced in code; the independent hash re-derivation in `runner.py:56-58` is deliberate and documented; and adding a new evidence source is refreshingly un-abstracted (fixture + small class + one tuple entry — no plugin registry where none was needed).

---

## Conceptual load (summary)

~40 concepts on the README-first path. ~10 are undefined at point of use in the README; **5 are undefined anywhere**: SBIR, ADCS, NV012 (no glossary entry), TBox, DSG. The glossary covers ~35 — the problem is routing, not coverage. Full inventory: the terms that must survive first contact are CMMC L2, CUI, 800-171, control, Order, Factory, COP, Gate 1/Gate 2, obligation, oracle, attestation, BOM, SSP, SPRS, NV012 — fifteen concepts, all of which `docs/v1/` teaches in order. Everything else can be deferred to the glossary.

---

## Essential vs. accidental complexity

The domain forces: the RDF named-graph substrate (the audit/BOM/SSP are *views over the graph* — traceability is the product), EARL/PROV/GSN for auditor-facing records, the compiler/factory seam with independent hash re-verification, the two-gate refusal design, the machine-informs/human-attests split, content-addressed storage. **Keep all of it.**

The implementation added: the sys.path import hack (F9), the never-executed plan.ttl + triple stage-list (F10), triple run-state bookkeeping (F14), the dead `StoreBackend` shell + doc-only top-level `backends/` (F7, F13), test-only "runtime" modules (F15), duplicate helpers and a 4×-copied module→control mapping (F16), and the R#/U# vocabulary tax (F5). Removing it all ≈ **~400–500 lines (~7%) and one directory**, but the real win is flatness: representations a newcomer must hold drops from ~10 to ~6.

**Change-cost reality check** ("add one new machine-checked control"): 5–8 files across four representation layers, with the module→control mapping hand-written up to four times. The layers are essential (law / topology / check / evidence have different owners); two of the four mapping copies are not.

---

## Fix-before-presenting shortlist (one day, doc-only)

1. **Route the front door** (~30 min, F1+F3): "Start here → docs/v1" banner atop README; a 5-line Documentation section routing by audience; glossary link under the diagram; define NV012, BOM, SSP, SBIR at first use; the one-sentence ADCS disclaimer (F4).
2. **Quarantine the DESIGN.md layer** (~30 min, F2): one warning banner in each of the 10 files pointing to AS-BUILT — or just delete them.
3. **Fix the self-contradictions** (~1 hr, F6+F8): AS-BUILT's SSP-stub and shape-fix claims; the Gate 2/3 mislabel in ARCHITECTURE's diagram; add `ssp.md` to README's artifact table; check off shipped ROADMAP items.
4. **De-jargon user-facing output** (~1 hr, F5): "Contradictions (R13)" → plain name in program output and README; strip U12 from CLI help; add the R#/U# legend to AS-BUILT.
5. **Correct the backend overstatement** (~15 min, F7): README repo-map row + ARCHITECTURE node color; delete top-level `backends/`.

Post-presentation (code, ~1–2 days when convenient): rename `order-compiler/` → `order_compiler/` (F9); load plan.ttl at runtime or demote it (F10); one-sentence auto-attest disclosure in audit.md's header (F11); collapse duplicate helpers (F16).

---

## Suggested 5-minute presentation arc

The order that makes the system feel simple — each step is one sentence of setup and one visual:

1. **The problem (30s).** "DoD contracts require CMMC compliance: 110 controls, human attestations, a signed System Security Plan. Today that's spreadsheets and consultants. We treat it as a build artifact instead."
2. **One sentence of architecture (30s).** "Two halves: a **compiler** that turns a contract into a signed, hash-addressed **Order** (which controls apply, what evidence each needs), and a **factory** that executes the Order — provisions infrastructure, collects evidence, runs machine checks — and emits a **BOM of proof**."
3. **The one safety idea (60s).** "Machines never attest. Oracles verify facts (`earl:automatic`); only a human can say MET (Gate 2). The engine's job is to make the human's signature *checkable*: if a human attests MET while the machine check failed, the audit flags the contradiction. And Gate 1 refuses to even compile an Order it can't cover — the system says 'no' rather than emitting paper claims." *(This is the differentiator — spend the time here.)*
4. **Live demo (2 min).** Three commands, pre-run: `all-covered` (SPRS 110, BOM hash), `gap` (Gate 1 refuses, names the uncovered control, exit 2, writes nothing), `contradiction` (flags the human-over-machine conflict). Point at one line of `audit.md` and one hash in `bom.json`. Mention determinism: "same inputs, byte-identical BOM — the hashes in our docs reproduce on your machine."
5. **Why RDF (30s) — pre-empt the complexity question.** "Every fact — evidence, check result, human signature — is a node in one provenance graph, so the audit is a *query*, not a report someone wrote. An assessor can re-verify the whole chain from the BOM alone. That's the part spreadsheets can't do."
6. **Honest status (30s).** "Runnable end-to-end today with mock evidence — every artifact says NON-EVIDENTIARY. Real collectors, real attestation UI, and cloud storage are the roadmap. 293 tests, three acceptance scenarios."

Do **not** open with the repo tree, the ontology, ADCS lineage, or any R/U numbers. Lead with the Gate 1 refusal demo — a compliance tool that *refuses to lie* is the memorable thirty seconds.

---

*Audit synthesized from four parallel agent reports; every finding carries file:line references verified against the working tree as of 2026-07-02. Two auditors independently executed the demo; all runtime claims above were observed, not inferred.*
