# Auditor's Guide — Re-verifying a Delivered BOM

**Audience:** a C3PAO assessor / DIBCAC reviewer holding a delivered Bill of
Materials (BOM) hash for a contract (e.g. `NV012`).

**The claim being audited:** *proof by reproduction.* A delivered BOM is not a
folder of screenshots. Every artifact it references is content-addressed by
SHA‑256, stored write-once in a registry, and re-derivable: you resolve each
artifact by hash, re-hash it to confirm nothing changed, re-run the plan-level
checks, and confirm the fingerprints match what the BOM records. **The hash IS
the content** — a single changed byte changes the key.

> **Phase I scope (read first).** This build is *mocked-then-real-ready*.
> Provisioning runs at **`terraform plan` level with mock providers** (no cloud,
> no live `apply`) and evidence is **fixture-backed**, so a delivered run is
> flagged **NON-EVIDENTIARY** and is **not a submittable SSP**. Content
> references are content-addressed by SHA‑256 (`registry://<hash>`). Attestation
> records and the audit-package manifest are now **cryptographically signed**
> (real Ed25519 today; the production **cosign + FIPS-KMS** path is wired behind a
> probe and deferred). See "What the auditor cannot yet do" at the end.

Everything below is verified against the committed code — the modules cited are
`pipeline/registry.py`, `traceability/bom.py`, `evidence/hashing.py`,
`documents/ssp.py`, `traceability/audit.py`, `traceability/sprs.py`,
`traceability/package.py`, and `terraform/tier1/` + `pipeline/provision/terraform.py`.

---

## The one-command paths (start here)

Two commands do the whole re-verification for you before you drop to the manual
steps below:

- **`ce verify-package --output-dir <delivered-dir>`** re-verifies the signed
  **audit package** offline. It checks the manifest's Ed25519 signature, re-hashes
  every bundled artifact (BOM, SSP) against the recorded hashes, and confirms the
  per-control **control → attestation → signed-policy** chain is complete. The
  manifest (`package/manifest.json`, produced by `ce package`) bundles the BOM, the
  SSP, the audit + SPRS verdict, the full-chain provenance (the SOP-adherence
  result), the signed per-control chain, and the signed-policy inventory. A single
  altered byte, a broken signature, or a broken chain link fails the check.
- **`ce verify --output-dir <delivered-dir>`** runs the tamper check (re-hash every
  evidence node — always a hard failure on a mismatch) plus the SHACL closure
  suite. On a NON-EVIDENTIARY (mock) run, closure findings for human-only controls
  (which carry no addressing evidence yet) are reported as an expected advisory,
  not a failure; on real evidence they are hard failures.

- The **human-readable report** is written into `package/` automatically by
  `ce package` (and by `demo`): a self-contained `report.html`, plus a paged
  `report.pdf` when the `weasyprint` binary is installed. `ce report --output-dir
  <delivered-dir>` re-renders it on demand. It is written for a mixed audience: it
  opens with a plain-language verdict and a glossary so a contracting officer can
  read the first pages and know what the package says and whether to trust it, then
  a family-level coverage rollup, the integrity/verification block, and the
  provenance result; the dense per-control matrix, signed-policy inventory, and full
  110-control catalog are moved to appendices. The report is a rendering of the
  signed manifest; its cover and footer carry the manifest hash and signature so you
  can re-verify the underlying package.

The manual Steps 1–6 below are the same reproduction done by hand, for when you
want to inspect each link yourself.

## Step 1 — Resolve: contract → BOM → artifacts (two-level index)

The registry is a content-addressed store rooted at a delivered directory. Open
it and walk the **two-level index**:

```python
from compliance_engine.pipeline.registry import Registry

reg = Registry("<delivered-registry-dir>")     # probes the root (fails fast if unwritable)

bom_hash  = reg.latest_bom("NV012")            # level 1: contract_id -> latest BOM hash  (None if unknown)
artifacts = reg.bom_artifacts(bom_hash)        # level 2: BOM hash    -> [artifact hashes]
```

- `latest_bom(contract_id) -> str | None` and `bom_artifacts(bom_hash) -> list[str]`
  are the only two index levels (a `control_id → BOMs` reverse index is
  **deferred** — no consumer yet).
- On disk: each object lives at `<root>/objects/<h[:2]>/<h[2:4]>/<h>`; the index
  is `<root>/index.json` (deterministic `sort_keys` JSON).
- Retrieve any object's bytes with `reg.get(hash)` (raises `KeyError` if absent);
  `reg.has(hash)` tests existence.
- A `bom_hash`'s reference form is `reg.hash_reference(bom_hash)` →
  `registry://<hash>` (a **content reference, not a signature**).

The BOM object itself is one of those stored artifacts: `reg.get(bom_hash)` is
its canonical JSON. Its `artifact_hashes()` are exactly the union of the
Order hash, the applied-state hash, every evidence hash, every module hash, and
each control-mapping row's evidence hashes (sorted, deduped).

## Step 2 — Integrity: re-hash everything

Content-addressing makes tampering self-evident: the key is the SHA‑256 of the
bytes (`evidence/hashing.py` `content_hash(b) = hashlib.sha256(b).hexdigest()`;
this is the **same** SHA‑256 that produced every `ce:contentHash` in the graph —
no separate hash is invented).

```python
from compliance_engine.traceability.bom import verify_bom

reg.verify(bom_hash)          # re-hash the stored BOM bytes; True iff sha256(bytes) == key
all(reg.verify(h) for h in artifacts if reg.has(h))   # re-hash every stored artifact
verify_bom(bom, reg)          # convenience: re-checks the BOM hash + every stored referenced artifact
```

- `reg.verify(hash)` re-reads the stored object and returns `True` only if it
  re-hashes to its key. Any mutated byte → mismatch → `False`.
- `verify_bom(bom, registry)` returns `False` if the BOM object is missing/tampered
  **or** any *stored* referenced artifact no longer hashes to its key.
- The `bom_hash` is **recomputable from content**: `bom.compute_hash()` re-hashes
  `bom.canonical_bytes()` (the canonical dict, schema `ce-bom/1`, which
  deliberately **excludes** the `bom_hash` field itself). Recompute it and compare
  to the delivered `bom_hash` — they must be equal.
- The store is **write-once**: attempting to put different bytes under an existing
  key raises `ContentMismatch`. You cannot silently overwrite an object.

If any check fails, the delivery has been altered after signing-off — stop and
reject.

## Step 3 — Re-execute (proof by reproduction)

The environment is described by the Order's **real HCL** under `terraform/tier1/`,
tagged so each planned resource maps to the `cmmc:` control(s) it satisfies. Re-run
it at **plan level with mock providers** (no credentials, no cloud):

```bash
terraform -chdir=terraform/tier1 init -backend=false
terraform -chdir=terraform/tier1 validate
terraform -chdir=terraform/tier1 test          # mock_provider: plan (+ mocked apply), no cloud
```

Programmatically, `pipeline/provision/terraform.py` `TerraformBackend(chdir="terraform/tier1")`
does `init -backend=false` → `validate` → `plan -out=<tmp>` → `show -json`, and
`evidence/generators/terraform_plan.py` (`TerraformPlanGenerator`) reads that plan
JSON. Each `terraform_data.cmmc_tag` resource carries `{module, controls,
resource_ids, region}`, so the **control → resource → evidence** mapping is
mechanical. Confirm:

- the resources and their `cmmc_control` labels reproduce the BOM's
  `control_mapping[].resource_ids`;
- re-running the oracles over the evidence summaries reproduces the BOM's
  `oracle_outcomes` (and `control_mapping[].oracle_outcome`);
- the residency safety valve still holds: a non-US region makes the
  `SC.L2-3.13.1` check **FAIL** on the real plan output (`REGION_CONTROL`).

If `terraform` is absent the generator raises `TerraformUnavailable` (a clean
skip, not a silent pass). Because evidence is fixture-backed in Phase I, these
plan-time artifacts are marked `ce:evidentiaryStatus "mock-plan"`.

## Step 4 — Judgment vs. machine (the line that matters)

**An oracle never establishes MET.** Oracles are `earl:automatic`
`ce:ControlCheckAssertion`s that `ce:evaluatesAgainst` a control — *supporting*
signal only. A control is MET **only** where a human **attested** it:
`ce:attests <control>` + `ce:hasOutcome earl:passed` (see `traceability/audit.py`
`met_control_ids`). Evidence likewise only `ce:addresses` a control; it never
`ce:attests`.

Run the audit and review two things:

```python
from compliance_engine.traceability.audit import audit
report = audit(ds)                     # AuditReport
report.contradictions                  # list[ContradictionRow]
report.proven.summary()                # "N MET-by-machine / M MET-by-human-only"
```

- **Contradictions.** `report.contradictions` flags every
  **MET-over-failed-oracle**: an `earl:passed` attestation whose backing oracle is
  `failed` (or asserted-but-absent) and which is **not** backed by BOTH a written
  `cmmc:overrideJustification` **and** appended `ce:overrideEvidence`. Each
  `ContradictionRow` names the `attestation`, `control`, and `oracle_outcome`. These
  are the human calls that override machine evidence — scrutinize them. A
  justification alone no longer clears the flag: overruling a failed machine check
  requires concrete, resolvable appended evidence (enforced at the write path and by
  the tightened `ContradictionShape`).
- **Proven-vs-attested split.** `report.proven` (`ProvenVsAttested`) gives
  `met_by_machine` (attested MET *and* oracle passed) vs `met_by_human_only`
  (attested MET on human judgement alone). The `summary()` string is
  "`N` MET-by-machine / `M` MET-by-human-only". Higher human-only counts mean more
  of the score rests on attestation rather than reproducible machine checks.

BOM rows record both sides honestly: `ControlMappingRow` carries `oracle_outcome`
**and** `attestation_outcome`, an **`evidence_backing`** field, and its
`status` is driven by the attestation (`MET | NOT MET | N/A | PLANNED | NEEDS ACTION`).
`AttestationRecord` carries the `official`, `role`, `outcome`, and any
`override_justification` + `override_evidence`.

The `evidence_backing` field has **four** values, and it tells you *what kind of
proof stands behind a MET*:

- **`machine`** — the sign-off is backed by a passing config-check oracle over
  resolvable evidence.
- **`override`** — MET over a *failed* check (scrutinize: requires a written
  justification and appended override evidence; see Contradictions above).
- **`attested-evidenced`** — a **Track B (policy/human)** control whose human
  sign-off is anchored to a **machine-recorded document version**. This is
  distinct from bare `human-only`: for these controls the engine resolved the
  control's `ce:Reference` URI to the real document on disk, **SHA-256 hashed** it,
  captured the **git commit** that last changed it (author + date), and signed an
  upload receipt with the local Ed25519 signer, binding all of this into the
  evidence graph as a `ce:DocumentEvidence` node. The attested-reference oracle
  then **gated** the MET: the control is MET only because the reference is
  registered, resolves to a real file, is within its freshness window, and is
  signed by the required role. A stale, dead-link, missing, or wrong-signer
  reference would have produced `needsAction`/`failed` and a non-MET control. On
  an `attested-evidenced` row you can therefore trace a Track B MET back to the
  **exact document content hash and git commit** it was signed against: the row
  carries `reference_id`, `git_commit`, and `git_committed_at`, and the attestation
  rationale is the real Affirming Official sign-off text (from
  `data/attestations/tier1.jsonl`), not boilerplate.
- **`human-only`** — a human judgment with **no machine anchor** at all (no
  passing measurement and no document-evidence chain).

What `attested-evidenced` does **not** assert: the engine checked the bureaucratic
facts (the reference resolves, is fresh, and is role-signed) and pinned the exact
document version the human signed against — it did **not** judge whether the policy
document's substance is adequate. The document's substance is still the human's
call. And because evidence remains fixture-backed, the upload receipt uses the
local Ed25519 dev signer (not production cosign/KMS), so an `attested-evidenced`
run is still **NON-EVIDENTIARY** like the rest of Phase I.

## Step 5 — SSP cross-check (no drift)

The SSP + Traceability Matrix (Document 2) is a **byte-stable view** over the
graph, not a hand-written narrative. Two checks:

- **Faithful view.** `documents/ssp.py` compiles it deterministically
  (`compile_ssp_from_run(ds, audit_report=..., bom=...)`); the CLI drift gate
  proves the delivered document still matches the dataset:

  ```bash
  uv run python -m compliance_engine.documents.ssp build --input <dataset.trig> --output <ssp.md> --check
  # exit 0 = up to date · exit 1 = drifted from the dataset · exit 2 = output/input missing
  ```

- **No status drift.** The VCRM columns are **Control | Implementation |
  Responsible party | Evidence location | Evidence hash | Status | Gap notes |
  POA&M ref**. The **Status** column is the attestation outcome via `STATUS_LABEL`
  (unattested → `PLANNED`); it must equal the attestation outcomes in the graph
  (`met_control_ids(ds)` == the set of controls shown MET). The machine-checkable
  subset is cited to a 64-hex evidence hash in the "Evidence hash" column.

- **R12 banner.** If any `ce:evidentiaryStatus` is `mock` or `mock-plan`, the SSP
  emits a top **NON-EVIDENTIARY — fixture-derived / auto-attested** banner, an
  "Evidentiary status: NON-EVIDENTIARY" front-matter cell, and a colophon stamp —
  and it **cannot** be suppressed. A banner present means **this is not a
  submittable SSP**; it is a reproducible demonstration artifact.

## Step 6 — SPRS score

The score is computed over the **Order's required control set** only
(`traceability/sprs.py`):

```
score = 110 − Σ(weight of each required control not MET)      (weights 1 | 3 | 5)
  110      → Final        (all required controls MET)
  88..109  → Conditional  (POA&M-eligible; 180-day closeout)
  < 88     → Ineligible
```

`FINAL = 110`, `CONDITIONAL_FLOOR = 88`. Variable-weight controls
(`IA.L2-3.5.3`, `SC.L2-3.13.11`) score their full weight in Phase I.

**POA&M-legality is a hard fail** (`SprsResult.valid_submission`): only 1-point
controls may be deferred to a POA&M. Any 3- or 5-point control on a POA&M — **or**
one of the six excluded 1-pointers (`AC.L2-3.1.20`, `AC.L2-3.1.22`, `CA.L2-3.12.4`,
`PE.L2-3.10.3`, `PE.L2-3.10.4`, `PE.L2-3.10.5`) — appears in `illegal_poam` and
makes `valid_submission` **False regardless of the numeric score**. A high score
with a non-empty `illegal_poam` is an invalid submission, not a passing one.

---

## What the auditor CANNOT yet do in Phase I (deferred — stated honestly)

- **No live-cloud verification.** Provisioning is `terraform plan` with **mock
  providers**; there is **no live `terraform apply`** and **no live compliance
  test** against a real tenant. Evidence is **fixture-backed** → every run carries
  the `mock` / `mock-plan` evidentiary marker and the **NON-EVIDENTIARY** SSP
  banner. You are reproducing the *plan-time* proof, not a live-cloud state.
- **Signatures are real, but the production key path is deferred.** Attestation
  records and the audit-package manifest are signed with real **Ed25519** and
  verified offline (`ce verify-package`); a tampered or unverifiable signed record
  is rejected at load. What is deferred is the production **cosign + FIPS-KMS**
  signing path (implemented behind a probe, switches on when the cosign binary and
  KMS key are present) and a transparency log (**Rekor**, which would be
  self-hosted in-enclave if ever adopted — never the public instance, for CUI).
  Registry artifacts are still referenced by bare SHA‑256 (`registry://<hash>`);
  `hash_reference(...)` is a content reference, not a signature.
- **Coverage is scoped.** The score and the machine-checkable evidence cover the
  automatable subset; the remaining controls are **human-attested** from
  documentary evidence and carry no `ce:contentHash`. Gate 1 guarantees no *silent
  gaps* in the derivation chain, **not** the semantic correctness of each
  hand-authored obligation→control→module→criterion link (machine-unverified until
  the human Gate 2 attestation).
- **No SPRS/PIEE submission or affirmation.** The engine *computes* the score and
  the POA&M legality; a human still submits and affirms separately.
- **Registry reverse-lookup by control is not available.** Only
  `contract → BOM → artifacts` resolves; a `control_id → BOMs` index is deferred.
