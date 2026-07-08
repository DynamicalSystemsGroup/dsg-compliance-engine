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

## KI-2: `Registry` is not composed with `FlexoBackend` — no write-through or fallback — RESOLVED

**Status:** RESOLVED (2026-07-08).

**Resolution.**

- Corrected the file path from the original write-up: `Registry` lives in
  `pipeline/registry.py`, not `traceability/registry.py`.
- `FlexoBackend.persist(ds, output_dir)` is whole-`Dataset`-shaped (it commits
  named graphs), while `Registry.put()`/`get()` are single-object,
  content-addressed operations — two genuinely different abstraction levels.
  Rather than force `Registry` onto the full `StoreBackend` protocol (which
  would require `LocalBackend` to grow an incompatible byte-blob
  responsibility), `FakeFlexoStore` and `FlexoBackend` gained a narrow,
  separate `put_object(bytes) -> str` / `get_object(hash) -> bytes` surface,
  reusing the same content-addressing discipline already used for named-graph
  snapshots but under a dedicated `_registry_objects` ref so BOM/artifact
  blobs never mix into graph-commit history.
- `Registry.__init__` now accepts an optional `remote` parameter (duck-typed:
  anything exposing `put_object`/`get_object`, feature-detected via
  `getattr` — no new formal Protocol, since `LocalBackend` doesn't need this
  surface). `Registry.put()` write-throughs to `remote` when configured; a
  remote failure sets `self.degraded = True` but never fails the local write
  (local remains the cache/fallback tier, unchanged from before). `Registry.get()`
  reads locally first and falls back to `remote` on a local miss, backfilling
  the local cache on success.
- Wiring `_do_bom()` in `cli.py` turned out to be a one-line change:
  `_make_store_backend()` already resolved `local`/`flexo` into a real
  `StoreBackend` and stored it on `PipelineState.store_backend` as part of
  `_do_run_factory()` — it was simply never read by `_do_bom()`. Now:
  `Registry(output_dir / "registry", remote=state.store_backend)`.
- Found and fixed a real ordering bug while tracing this: `_dump_run_state()`
  ran _before_ `_persist_to_flexo()` inside `demo()`, so `run_state.json` was
  always written before the code path that could set a degraded flag even
  ran. Reordered so `_persist_to_flexo()` (now returning whether it
  degraded) runs first, and its result plus `Registry.degraded` (surfaced via
  `state.registry_degraded`, set in `_do_bom()`) are both folded into a new
  `"degraded"` boolean in `run_state.json`.
- Tests: `tests/test_registry.py::TestRemoteComposition` (write-through,
  read-through/backfill, degrade-on-remote-failure without failing the local
  write, no-remote-configured behaves exactly as before);
  `tests/test_flexo_wiring.py` (`put_object`/`get_object` round-trip,
  write-once semantics, missing-key `KeyError`, registry objects kept
  separate from graph-commit history); `tests/test_cli.py`
  (`--store-backend flexo` exits 0 with `degraded: false` in `run_state.json`
  and the BOM object resolvable from the Flexo registry-objects tier; the
  default local path also reports `degraded: false`).
- Verified end to end: `just demo` and `just demo-flexo` both still produce
  SPRS 110/Final; `run_state.json` correctly reports `degraded: false` on a
  healthy run in both modes.

---

## KI-3: References in `references.ttl` do not carry `ce:version` or `ce:signature` — RESOLVED

**Status:** RESOLVED (2026-07-08).

**Resolution.**

- Chose the minimal honest interpretation, consistent with the ontology's own
  pre-existing comment ("Absent = latest/unpinned (fixture mode)"): `ce:version`
  is the SHA-256 hex content hash of the resolved document (the same
  content-addressing discipline already used throughout the registry and
  Flexo tiers), not a `flexo://<hash>` URI — a live Flexo version pin remains
  explicitly deferred future work, unblocked by no live Flexo tier existing
  yet. `ce:signature` is a real base64 Ed25519 detached signature over the
  raw document bytes, computed with the same deterministic
  `Ed25519LocalSigner` `pipeline/evidence/doc_evidence.py` already uses for
  upload-receipt signing.
- Generated the values with a one-off script (resolve each reference's
  `ce:uri` via `doc_evidence.resolve_uri()`, hash, sign, print paste-ready
  triples) and hand-reviewed the diff before committing; the script itself
  was deleted afterward rather than kept as permanent tooling, per the
  original fix text's spirit of keeping the ttl diff reviewable.
- Added `ce:version` and `ce:signature` to all 16 `ce:REF_POL_*` nodes in
  `data/structural/references.ttl`.
- Extended `ReferenceView` (`oracles/attested_reference.py`) with `version:
str | None`, `signature: str | None`, and `signature_verified: bool | None`
  (the last set by the caller after live verification — see KI-5), and
  `traceability/references.py::load_attested_controls()` now reads
  `ce:version`/`ce:signature` from the graph into the view. Verified live:
  all 43 Track B controls resolve a version-pinned reference from the real
  pipeline dataset.
- Signature verification (branch 2 of the original fix text) is implemented
  as part of KI-5, not here — see that entry for the oracle branches.
- Tests: `tests/test_attested_reference.py::TestReferenceVersionAndSignature`
  — every reference carries both properties, and (round-trip regression
  guard against doc drift) each reference's `ce:version`/`ce:signature`
  actually matches the currently-resolved document on disk, re-verified with
  a fresh `Ed25519LocalSigner`.

---

## KI-4: `step-SignAndStore` in `plan.ttl` is a provenance annotation, not a signing action — RESOLVED

**Status:** RESOLVED (2026-07-08).

**Resolution.**

- `traceability/bom.py::store_bom()` now signs the BOM's canonical bytes
  immediately after storing them, using `signing/signer.py`'s
  `default_local_signer()` (Ed25519 today; the same `Signer` protocol
  transparently dispatches to cosign+KMS when `CosignKmsSigner.available()`
  once the binary and key are present — no code change needed for that
  transition).
- The signature itself is stored as a registry object (`registry.put(sig,
  kind="bom-signature")`), and its object hash is recorded against the BOM
  hash via two new `Registry` index methods, `set_bom_signature()` /
  `bom_signature()`, mirroring the existing `set_bom_artifacts()` /
  `bom_artifacts()` pattern rather than inventing a new lookup path.
- `cli.py::_do_bom()` looks up the signature via `registry.bom_signature()`,
  fetches the bytes via `registry.get()`, and writes it base64-encoded as
  `bom.json.sig` next to `bom.json` — mirroring how `manifest.sig` already
  sits next to `package/manifest.json`.
- `traceability/package.py::build_audit_package()` copies `bom.json.sig` into
  the package directory alongside `bom.json` (not sha256-tracked as a bundled
  artifact, since it is itself a signature rather than re-hashable content),
  so an assessor examining the package alone can verify the BOM's own
  signature independently of the manifest's package-wide signature.
  `verify_audit_package()` checks it when present: absence is non-fatal
  (older packages predate this signature), but presence with an invalid
  signature is a hard failure.
- Tests: `tests/test_bom.py::test_store_bom_signs_the_bom_and_records_it_in_the_registry`;
  `tests/test_package.py::test_bom_json_sig_is_bundled_and_verifies` and
  `test_tampered_bom_signature_is_detected`.
- Verified end to end: `just demo` produces both `output/bom.json.sig` and
  `output/package/bom.json.sig`; `uv run ce verify-package` reports "VERIFIED:
  signature valid, artifacts intact, chain complete." Full suite: 447 passed.

---

## KI-5: The attested-reference oracle has no signature-specific failure reasons — RESOLVED

**Status:** RESOLVED (2026-07-08).

**Resolution.**

- Corrected the original write-up on two counts: the oracle had roughly nine
  return points / eight named branches, not "six" as previously stated; and
  the stated dependency on KI-4 (signing the BOM) was wrong — KI-5 only
  depends on KI-3 (references carrying `ce:signature`), which is unrelated
  to whether the BOM itself gets signed. Resolved after KI-3, independent of
  KI-4.
- **Design call:** kept `evaluate_attested_reference()` a pure, dependency-free
  function (no `Signer` import, no file I/O) rather than verifying inside the
  oracle. It already relied on the caller to resolve `resolved_ok` ahead of
  time; live signature verification follows the identical shape. Added
  `signature_verified: bool | None` to `ReferenceView`, set by
  `pipeline/runner.py` (which already resolves the document via
  `doc_evidence.capture()`) using `Ed25519LocalSigner().verify()` against the
  freshly re-read document bytes, and folded into the same `replace(view,
resolved_ok=..., signature_verified=...)` call already there.
- Added two branches to `evaluate_attested_reference()`, placed after the
  freshness check and before `awaiting-attestation` (a stale/dead reference
  is caught first; a missing/invalid signature is surfaced before an
  attestation even exists, since it's independently actionable):
  `signature-missing` (`needsAction`, when `reference.signature is None`) and
  `signature-invalid` (`failed`, when `reference.signature_verified is False`).
- Updated the module docstring's branch list to the corrected count and order.
- Tests: `tests/test_attested_reference.py` — `test_signature_missing_yields_needsAction`,
  `test_signature_invalid_yields_failed`,
  `test_signature_valid_continues_to_attestation_check` (proves the new
  branches don't short-circuit the existing happy path). The pre-existing
  `_ref()` fixture helper now defaults to a valid `signature`/`signature_verified=True`
  pair so all other branch tests (testing unrelated concerns) pass through the
  new checks transparently; the real end-to-end sanity test
  (`TestTrackBEndToEnd.test_every_track_b_control_passes`) now reads and
  live-verifies the actual `ce:version`/`ce:signature` from `references.ttl`
  against the real resolved documents, rather than constructing a bare
  `ReferenceView`.
- Verified end to end: `uv run ce demo --evidence-set all-covered --auto` and
  `uv run ce demo --full --report` both still produce SPRS 110/Final,
  unchanged from the KI-3-only checkpoint — all 43 real Track B controls'
  live signatures verify.

---

## KI-6: `evidence_backing` is absent from the BOM RDF graph and the SSP — RESOLVED

**Status:** RESOLVED (2026-07-08).

**Resolution.**

- Defined `ce:evidenceBacking` (`owl:DatatypeProperty`) in
  `data/ontology/ce-attestation-refs.ttl`, next to `ce:overrideEvidence`.
- Added `g.add((node, CE.evidenceBacking, Literal(row.evidence_backing)))` to
  `BOM.to_rdf()`'s per-row loop in `traceability/bom.py`, per the original fix
  text. **Caveat found and recorded honestly:** `to_rdf()` is never called
  anywhere outside the test suite — the BOM RDF subgraph is not merged into
  the live pipeline dataset today. This fix is therefore correct for any
  future RDF/SPARQL consumer of a `BOM.to_rdf()` graph, but it does not by
  itself feed the SSP (see below).
- **Corrected a wrong assumption in the original fix text:**
  `documents/ssp.py`'s VCRM table is built **entirely from SPARQL queries**
  against the live dataset (`traceability/queries.py::ATTESTATION_DETAIL`),
  not from a live `BOM`/`ControlMappingRow` object — there is no
  `bom_result.control_mapping` reference anywhere in `ssp.py`. The proposed
  fix ("populated from `bom_result.control_mapping[i].evidence_backing`")
  would not have worked as written.
- Instead: extended `ATTESTATION_DETAIL` to also select `?documentEvidence`
  (the `ce:documentEvidence` signal already written by
  `traceability/attestation.py` for Track B controls, previously queried but
  unused for this purpose). Added `_backing_for_row()` / `_backing_label()` in
  `documents/ssp.py`, mirroring — not calling —
  `ControlMappingRow.evidence_backing`'s four-way rule (machine /
  attested-evidenced / override / human-only), computed from the fields the
  query already returns (`outcomeShort`, `oracleOutcome`, `evidence`,
  `documentEvidence`). Added a **Backing** column to the VCRM header, placed
  right after **Status**.
- Bug found and fixed while testing: `oracleOutcome` comes back from the
  SPARQL query as a full EARL outcome IRI
  (`http://www.w3.org/ns/earl#failed`), not a short name — the first version
  of `_backing_for_row()` compared it against the bare string `"failed"` and
  silently always fell through to `human-only`. Fixed by normalising through
  the file's existing `_local()` helper before comparing.
- **Deferred, explicitly, rather than added as inert scope:** the SHACL shape
  proposed in the original fix text ("every BOM mapping node carries exactly
  one `ce:evidenceBacking` value") is not added. Since the BOM RDF subgraph
  is not merged into the live dataset (see above), such a shape would never
  fire against real data and would be untestable today. This is a stated,
  deliberate gap — add it only once `to_rdf()`'s output is actually merged
  into the pipeline's dataset.
- Tests: `tests/test_bom.py::test_to_rdf_emits_evidence_backing_per_control_mapping_row`;
  `tests/test_ssp.py::TestBackingColumn` (machine, attested-evidenced,
  override, human-only, and unattested-control cases, each verified through
  the real `compile_ssp()` SPARQL path); `_VCRM_HEADER` in `test_ssp.py`
  updated to the new 9-column header.
- Verified end to end: `uv run ce demo --full --report` (all 110 controls)
  produces a Backing-column distribution of **65 machine / 43
  attested-evidenced / 2 human-only** — exactly matching the BOM distribution
  already documented in `docs/AS-BUILT.md`. SPRS remains 110/Final; the
  byte-determinism test (`test_compile_twice_byte_identical`) still passes.

---

## KI-7: `AttestationRecord` does not validate `override_evidence` at construction — RESOLVED

**Status:** RESOLVED (2026-07-08).

**Resolution.**

- Corrected the file path from the original write-up: `AttestationRecord`
  lives in `traceability/attestation_store.py`, not `signing/attestation_store.py`.
- Corrected the proposed condition: `AttestationRecord` has no `oracle_outcome`
  field and no `"MET"` outcome value (`outcome` here is lowercase
  `passed`/`failed`/`needsAction`) — the original fix text's condition
  (`outcome == "MET" and oracle_outcome in ("failed", "absent")`) does not
  match this dataclass's actual schema. The real mirror target is
  `request_attestation()`'s own parameter pair (`override_justification`,
  `override_evidence`) and its simple presence check, not an oracle-outcome
  condition.
- Added **both** `override_justification: str | None = None` and
  `override_evidence: str | None = None` to `AttestationRecord` (adding only
  `override_evidence` would leave nothing to condition validation on).
- Added `__post_init__` validation: `override_justification` set without
  `override_evidence` raises `AttestationStoreError`, mirroring
  `request_attestation()`'s existing `ValueError` check exactly.
- Populated both fields in `_record_from_obj()` from the JSONL row, and added
  them to `_record_to_obj()` for round-trip write support.
  `AttestationRecord.signing_payload()` already builds its payload from
  `asdict(self)` excluding only `sig`/`sig_algo` by name, so the new fields
  are automatically covered by the existing signature — no change needed there.
- Tests added to `tests/test_override_evidence.py`: construct-without-evidence
  raises; construct-with-evidence succeeds; omitting both (the common case —
  all 16 real `tier1.jsonl` records today) still works; JSONL round-trip
  through `_record_from_obj()`.

---

## KI-8: `OverrideEvidenceShape` is embedded inside `ContradictionShape`, not standalone — RESOLVED

**Status:** RESOLVED (2026-07-08).

**Resolution.**

- Extracted `ce:OverrideEvidenceShape` as a standalone, named `sh:NodeShape` in
  `data/ontology/cmmc_shapes.ttl`, targeting `ce:Attestation` directly: any
  attestation carrying `cmmc:overrideJustification` without `ce:overrideEvidence`
  violates it — independent of whether the attestation is also caught up in a
  MET-over-FAILED contradiction. This is deliberately **not** gated on the
  contradiction condition, which the ontology's own pre-existing comment on
  `ce:overrideEvidence` already implied ("An override justification without
  appended evidence is a violation (OverrideEvidenceShape)") — making it
  general-purpose is the more correct rule, not scope creep.
- Referenced it from `ContradictionShape` via `sh:node ce:OverrideEvidenceShape`,
  but **kept** `ContradictionShape`'s own inline `FILTER NOT EXISTS` check
  rather than deleting it. Verified empirically (both via a local pyshacl
  probe and via the new test below) that `sh:node` and `sh:sparql` fire as
  independent, non-deduplicated constraint components: a MET-over-FAILED
  attestation with a justification but no evidence now reports **three**
  entries in the violation report (the `sh:node`-wrapped detail, the standalone
  `OverrideEvidenceShape` firing on its own since it independently targets
  `ce:Attestation`, and `ContradictionShape`'s own sparql violation) instead of
  one. This is more informative, not a regression — existing tests assert on
  message substrings, not violation counts, so nothing broke. Confirmed the
  standalone shape genuinely fires **outside** a contradiction too (a passed
  attestation with no oracle failure, just a bare justification and no
  evidence) — proving it is reusable, not merely relocated contradiction logic.
- Tests added to `tests/test_verification_shapes.py`:
  `test_override_justification_without_evidence_violates_standalone_shape`
  (fires with `"OverrideEvidenceShape"` in the report text, and explicitly
  confirms `"Contradiction (R13)"` does NOT appear, since this fixture has no
  failed oracle backing it) and
  `test_override_justification_with_evidence_conforms_standalone`. The two
  pre-existing `ContradictionShape` tests
  (`test_met_over_failed_oracle_without_override_fails`,
  `test_override_clears_contradiction`) pass unchanged.
- Verified end to end: `just demo` (SPRS 110/Final) and `just demo-contradiction`
  (SPRS 105/Conditional, `valid_submission=False`, exactly 1 contradiction
  reported in the audit summary — the audit's contradiction count is computed
  separately from the SHACL closure suite and is unaffected by this change)
  both behave identically to before.
