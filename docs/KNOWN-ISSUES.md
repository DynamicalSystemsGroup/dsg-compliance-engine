# Known issues

Tracked, honestly-stated defects and gaps. Each entry says what is wrong, why it
is not already fixed, and how to fix it.

---

## KI-1: `ce verify` was broken and did not conform on the mock demo — RESOLVED

**Status:** RESOLVED (2026-07-03). Was pre-existing (predated `feat/signed-provenance`,
confirmed on `main`). Fix + regression test below.

**Resolution.**

- Fixed the import (`from compliance_engine.traceability import verification`) and a
  second bug in the same command (it read `m.evidence_iri/expected_hash/actual_hash`,
  but `ReverificationMismatch` fields are `evidence/expected/actual`).
- `verify` now separates the **tamper check** (re-hash every evidence node — always a
  hard failure on a mismatch) from the **SHACL closure** suite. On a NON-EVIDENTIARY
  (mock) run, closure findings for human-only controls are reported as an advisory,
  not a hard failure; on real evidence they remain hard failures.
- Fixed two real closure violations surfaced along the way: the downstream P-Plan
  activities lacked a `prov:wasAssociatedWith` agent (ActivityAgentShape), and the
  SOP step definitions (`plan.ttl`) were not loaded at verification time so
  `correspondsToStep` targets were untyped (PlanInstantiationShape). `verify_shacl`
  now loads `plan.ttl` alongside the data.
- Added `tests/test_verify_cli.py`: `ce verify` passes on a clean mock demo (with the
  advisory) and exits non-zero on tampering.

Net: `ce verify` on the demo now prints "No tampering detected" plus a clear
NON-EVIDENTIARY advisory and exits 0; a corrupted evidence hash prints "TAMPERING
DETECTED" and exits 1.

**Original diagnosis (for the record).** The `verify` command had two independent
problems:

1. **Import bug (hard crash).** Its body does `import traceability.verification`
   (a bare top-level import) instead of
   `from compliance_engine.traceability import verification`. The `traceability`
   package lives under `src/compliance_engine/traceability/`, so the bare import
   resolves nowhere and the command raises `ModuleNotFoundError: No module named
'traceability'` before it does any work. This line is present on `main`
   (`git show main:src/compliance_engine/cli.py`, line 511), so the bug predates
   this branch. No test invokes the `verify` command, so it has never been a
   passing path — the crash went unnoticed.

2. **Shapes are written for real evidence, not the mock demo.** Even with the
   import fixed, `verification.verify(ds)` runs the full closure/verification SHACL
   suite, which assumes real evidence. On the shipped **NON-EVIDENTIARY** demo it
   reports non-conformance for reasons that are expected on mock data — e.g.
   human-only controls that legitimately have no addressing evidence — mixed with a
   pyshacl inference artifact (a phantom blank-node `p-plan:Activity` flagged for a
   missing `correspondsToStep`, even though every real activity in the dataset has
   exactly one). So the command is not expected to conform on a practice run.

**What this does NOT affect.** This is a different command from `ce verify-package`
(the Phase E audit-package re-verification), which is fully wired and passes:
`ce verify-package` verifies the signed manifest, re-hashes every bundled artifact,
and checks the control->signed-policy chain. The demo, the notebook, `ce package`,
and the whole test suite (396 passing) are unaffected.

**Why it was not fixed here.** It is a pre-existing bug in a command that is not one
of the six signed-provenance items and is not part of the demo/notebook path.
Fixing the import is a one-liner, but making `verify` _behave sensibly_ also
requires deciding how it should report on NON-EVIDENTIARY data and running down the
pyshacl inference artifact — a separate, self-contained task. During the
signed-provenance work an opportunistic import fix was made and then reverted to
keep that change set scoped; the command was left exactly as found.

**How to fix (follow-up).**

1. Change `import traceability.verification` to
   `from compliance_engine.traceability import verification` (and use
   `verification.verify(...)`).
2. Have `verify` detect a NON-EVIDENTIARY dataset and print a clear message that
   full SHACL conformance is expected only on real evidence (so mock-data gaps read
   as "expected on a practice run", not as a crash or regression).
3. Investigate the phantom-blank-node `p-plan:Activity` finding (likely a pyshacl
   inference setting in `traceability/verification.py`); confirm the real dataset
   conforms on the `PlanInstantiationShape` (it does — all 12 activities carry
   exactly one `correspondsToStep`).
4. Add a test that invokes `verify` so it can never silently rot again.

**Note on provenance hygiene (already fixed).** The signed-provenance work initially
introduced one real SHACL violation here — evidence nodes and oracle assertions
already carry a generating activity, and the new P-Plan binding added a second
`prov:wasGeneratedBy` (violating the max-one-generating-activity shape). That was
fixed: those nodes are now tied to their plan Variable via `correspondsToVariable`
only. Every `prov:Entity` the run produces has at most one generating activity.

---

## KI-2: `Registry` is not composed with `FlexoBackend` — no write-through or fallback

**Status:** OPEN

**What is wrong.** `FlexoBackend` (`pipeline/backends/flexo.py`) fully implements the
`StoreBackend` protocol and is selectable via `--store-backend flexo`. However,
`Registry.__init__` (`traceability/registry.py`) is typed `LocalBackend | None` and
is never given a `FlexoBackend`. There is no write-through path (store to Flexo and
cache locally), no read-through path (check Flexo before the local copy), and no
graceful degradation to local when Flexo is unreachable. `--store-backend flexo`
causes the demo to persist its run to the `FakeFlexoStore` but the `Registry` that
the BOM and package commands use still reads and writes only local files. The two
tiers are parallel, not composed.

Additionally, `run_state.json` has no `degraded` field to signal that a run fell
back to local storage because Flexo was unavailable.

**Why it is not fixed.** The Flexo backend and the Registry were built in separate
passes. The compose step — making `Registry` accept a tiered backend and route
through it — was not implemented; it requires changing the `Registry` constructor
signature, adding write-through/read-through logic, and surfacing `degraded` in the
run state.

**How to fix.**

1. Change `Registry.__init__` to accept `backend: StoreBackend | None = None` and
   store it alongside the local path.
2. In `Registry.store()`, write to the backend first, then write locally as the cache
   tier; catch backend errors and set a `self.degraded = True` flag.
3. In `Registry.resolve()`, check the backend first; fall back to local on miss or
   error.
4. Expose `degraded` in `run_state.json` so downstream commands can report that a run
   was not persisted to the tier of record.
5. Pass the backend instance through `get_backend(...)` to the `Registry` constructor
   in each CLI command that constructs one.

---

## KI-3: References in `references.ttl` do not carry `ce:version` or `ce:signature`

**Status:** OPEN

**What is wrong.** `ce:version` and `ce:signature` are defined in
`data/ontology/ce-attestation-refs.ttl` as properties on `ce:Reference` individuals.
No `ce:REF_POL_*` node in `data/structural/references.ttl` has either property. The
attested-reference oracle (`oracles/attested_reference.py`) does not check for a
version pin or a detached signature on the reference target; references resolve to
floating file paths with no version anchor. The plan called for version-pinned Flexo
URIs (`flexo://<hash>`) as reference targets so that a reference is immutably bound
to a specific document version.

**Why it is not fixed.** This requires a live Flexo store to produce stable
`flexo://<hash>` URIs. Without a live tier the version pin would still be a local
path. The property definitions were put in the ontology as placeholders.

**How to fix.**

1. Add `ce:version` (a content hash or Flexo version token) and `ce:signature`
   (the detached Ed25519 signature over the resolved document) to each
   `ce:REF_POL_*` node in `references.ttl`.
2. Extend the attested-reference oracle to read and verify `ce:signature` when
   present, and add a `signature-invalid` oracle reason alongside the existing
   six reasons.
3. Once the live Flexo tier exists, replace file-path URIs with
   `flexo://<hash>` and update the resolver accordingly.

---

## KI-4: `step-SignAndStore` in `plan.ttl` is a provenance annotation, not a signing action

**Status:** OPEN

**What is wrong.** `ce:step-SignAndStore` is declared in `plan.ttl` as a
`p-plan:Step` that "cosign-signs the BOM and writes it once to the tier registry."
In practice, `plan_execution.py` creates a `p-plan:Activity` for this step as a
provenance record after the fact. Nothing in the run path calls cosign or writes a
detached signature when this step executes. The BOM is written to the local registry
and the activity is recorded; no signing happens. The step's description is aspirational
documentation, not executable behaviour.

**Why it is not fixed.** Actual cosign signing requires the `cosign` binary and
`CE_COSIGN_KMS_KEY` set to a `gcpkms://...` reference. `CosignKmsSigner.available()`
returns `False` in the demo environment. The step was defined alongside the provenance
plan before the signing probe was wired.

**How to fix.**

1. In the code path that records the `step-SignAndStore` activity, call
   `get_signer().sign(bom_bytes)` (the `Signer` protocol in `signing/signer.py`
   already handles both Ed25519 and cosign dispatch).
2. Write the detached signature alongside `bom.json` as `bom.json.sig`.
3. Update `verify_audit_package` to check for and verify `bom.json.sig` when
   present.
4. The demo will use `Ed25519LocalSigner` (which is always available); cosign
   activates automatically when the binary and key are present.

---

## KI-5: The attested-reference oracle has no signature-specific failure reasons

**Status:** OPEN

**What is wrong.** `oracles/attested_reference.py` returns six distinct
`needsAction`/`failed` reasons: `missing-reference`, `unresolvable`, `stale`,
`awaiting-attestation`, `role-mismatch`, and `predates-reference`. There is no
`signature-missing` or `signature-invalid` reason. When `ce:signature` is absent from
a reference (KI-3) or when a document's detached signature fails verification (KI-4),
the oracle either passes silently or falls through to `awaiting-attestation` — neither
accurately describes the failure. Signature failures are currently caught at
attestation load time by `attestation_store.verify_record()`, not surfaced through
the oracle's reason vocabulary.

**Why it is not fixed.** Signature checking in the oracle depends on references
carrying `ce:signature` (KI-3) and on the signing action being wired (KI-4). Both
are blocked; adding oracle reasons without the upstream work would produce dead
branches.

**How to fix.**

1. After resolving KI-3 and KI-4, add a `signature-missing` branch to the oracle
   (reference resolves, document exists, but `ce:signature` is absent) and a
   `signature-invalid` branch (signature present but `Signer.verify()` raises).
2. Both should return `needsAction` with the specific reason string, matching the
   pattern of the existing six branches.
3. Add test cases for each new branch in `tests/test_attested_reference.py`.

---

## KI-6: `evidence_backing` is absent from the BOM RDF graph and the SSP

**Status:** OPEN

**What is wrong.** `ControlMappingRow.evidence_backing` (`traceability/bom.py`) is
computed correctly and included in `to_dict()`, which feeds the JSON BOM. However,
`to_rdf()` on the same class does not emit `evidence_backing` as a triple; the
computed value is dropped when the BOM is serialised to the RDF dataset. Downstream
SPARQL queries over the dataset cannot filter or report by backing type.

Separately, `documents/ssp.py` does not include a backing column in the traceability
matrix. The SSP headers are: Control, Implementation, Responsible party, Evidence
location, Evidence hash, Status, Gap notes, POA&M ref. The backing type
(`machine` / `attested-evidenced` / `override` / `human-only`) that distinguishes
how a sign-off is supported is only visible in the notebook (Station 8) and the
JSON BOM.

**Why it is not fixed.** The backing property was added to the Python dataclass and
JSON output; the RDF and SSP representations were not updated in the same pass.

**How to fix.**

1. In `to_rdf()` in `traceability/bom.py`, add a triple:
   `g.add((row_node, CE.evidenceBacking, Literal(self.evidence_backing)))`.
   Define `ce:evidenceBacking` in `ce-attestation-refs.ttl`.
2. In `documents/ssp.py`, add a **Backing** column to the traceability matrix,
   populated from `bom_result.control_mapping[i].evidence_backing`.
3. Update the SHACL verification shapes to assert that every BOM mapping node
   carries exactly one `ce:evidenceBacking` value.

---

## KI-7: `AttestationRecord` does not validate `override_evidence` at construction

**Status:** OPEN

**What is wrong.** The rule "an override attestation must carry `override_evidence`"
is enforced in `attestation.py`'s `request_attestation()` function, which raises
before creating the record. The `AttestationRecord` dataclass in
`signing/attestation_store.py` has no `override_evidence` field and no
`__post_init__` validation. This means:

- Records loaded from `tier1.jsonl` bypass the check entirely (the store's
  `_parse_record()` does not enforce it).
- An `AttestationRecord` constructed directly (e.g. in tests) can represent an
  override with no evidence without triggering any error.
- The `AttestationRecord` API is incomplete relative to the data it is supposed to
  represent.

**Why it is not fixed.** The enforcement was added at the `request_attestation`
boundary, which is the only path exercised by the demo and the test suite. The
gap was not noticed because no test constructs an override `AttestationRecord`
directly.

**How to fix.**

1. Add `override_evidence: str | None = None` to `AttestationRecord` in
   `signing/attestation_store.py`.
2. Add `__post_init__` validation: if `outcome == "MET"` and
   `oracle_outcome in ("failed", "absent")` and `override_evidence` is None,
   raise `AttestationStoreError`.
3. Populate `override_evidence` in `_parse_record()` from the `"override_evidence"`
   key in the JSONL row.
4. Add a test that constructs an override record without evidence and asserts the
   error.

---

## KI-8: `OverrideEvidenceShape` is embedded inside `ContradictionShape`, not standalone

**Status:** OPEN

**What is wrong.** The SHACL enforcement that an override attestation must carry
`ce:overrideEvidence` is written as a nested `sh:node` constraint inside
`ContradictionShape` in `data/ontology/cmmc_shapes.ttl`. There is no
`ce:OverrideEvidenceShape` as a named, independently-targetable shape. This has two
practical consequences:

- The shape cannot be run in isolation to check only the override-evidence rule.
- A validator report refers to `ContradictionShape` rather than
  `OverrideEvidenceShape`, making the error message harder to read.
- Future shapes that apply the same rule to non-contradiction nodes (e.g. a
  standalone override record that has not yet been audited) cannot reuse it.

**Why it is not fixed.** The override-evidence rule and the contradiction rule were
implemented in the same pass. The nesting was expedient; a refactor was not
prioritised.

**How to fix.**

1. Extract the override-evidence constraint from `ContradictionShape` into a new
   named shape `ce:OverrideEvidenceShape` with its own `sh:targetClass` or
   `sh:targetSubjectsOf`.
2. Reference it from `ContradictionShape` via `sh:node ce:OverrideEvidenceShape`
   so existing behaviour is preserved.
3. Confirm `tests/test_verification_shapes.py` and `tests/test_override_evidence.py`
   still pass with the refactored shape.
