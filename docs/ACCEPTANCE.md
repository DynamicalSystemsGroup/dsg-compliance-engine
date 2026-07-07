# NV012 Compliance Engine — Acceptance Sign-Off

> **Verdict: GO** (Phase-I / Tier-1 as-built acceptance).
> Independent read-only QA pass, 2026-07-02. Environment: `uv` shared venv,
> Terraform **v1.15.7** installed. No code changed during this review.

## 1. Full test suite

```
uv run pytest -q
→ 293 passed, 1 deselected, 0 failed   (~24s)
```
- **1 deselected** = the opt-in network `fetch_imports` refresh test
  (`@pytest.mark.network`, excluded by default — correct, not a failure).
- SSP byte-stability tests (`tests/test_ssp.py`) and the terraform-marked tests
  pass (Terraform v1.15.7 present). No failures, no errors.

## 2. Three demo scenarios

| Scenario (`cli.py demo --evidence-set …`) | Gate 1 / SPRS | Exit | Artifacts | Verdict vs criterion |
| --- | --- | --- | --- | --- |
| **all-covered** | Gate 1 PASS (Order = 22 controls); **SPRS 110 / Final / valid_submission=True**; R13 contradictions **0**; proven 20 machine / 2 CSP-inherited | **0** | `bom.json` (`evidentiary_status=mock`), `audit.{md,json}`, `ssp.md` (NON-EVIDENTIARY banner **present**; VCRM = **110** control rows), `engine.trig`, `run_state.json`, `registry/{objects,index.json}` | **PASS** — Gate 1 pass, SPRS 110/Final/valid, R12 banner present, VCRM covers the graph |
| **gap** | **Gate 1 REFUSED — Order NOT emitted**, names missing module for **AC.L2-3.1.12** | **2** | none (Factory never ran; no `bom.json`) | **PASS** — refusal names the control, exit 2, Factory never runs |
| **contradiction** | Gate 1 PASS; **SPRS 105 / Conditional / valid_submission=False** (the contradicted control's weight is deducted); **R13 contradictions = 1**; proven 19 machine / 3 human | **0** | full set incl. `ssp.md`; colophon: *"…contradictions: 1."* | **PASS** — R13 flagged (count ≥ 1), the score drops and the submission is invalid, surfaced in `audit.md` + SSP colophon |

**SSP wiring has landed** — `cli.py demo` produces `ssp.md` directly (not a stub);
it carries the NON-EVIDENTIARY banner and colophon on every mock run.

**Override-clears-R13** is not exercised by the demo (which never adds an
override), but is verified green in the suite:
`tests/test_audit.py::test_override_clears_contradiction` and
`tests/test_shacl_closure.py::test_r13_override_clears_contradiction`.

## 3. R1–R13 spot-checks (against `docs/AS-BUILT.md`)

| Req | Claim checked | Result |
| --- | --- | --- |
| **R6** | illegal-POA&M gate in `traceability/sprs.py` | PASS `illegal = [c for c … if c.on_poam and (c.weight > 1 or not c.poam_eligible)]`; `valid_submission = not illegal_poam` |
| **R10** | all 110 controls in `ontology/cmmc-edit.ttl` | PASS exactly **110** `a cmmc:Control` nodes |
| **R12** | NON-EVIDENTIARY banner structurally non-omittable in `documents/ssp.py` | PASS `compile_ssp` emits the banner + colophon stamp whenever `mock_present`; no suppress flag exists — confirmed live (banner in all mock `ssp.md`) |
| **R13** | ContradictionShape in `ontology/cmmc_shapes.ttl` | PASS MET (`ce:hasOutcome earl:passed`) + `ce:oracleOutcome earl:failed` + no `cmmc:overrideJustification` ⇒ violation; confirmed live (contradiction scenario count = 1) |

All four hold. No traceability claim failed spot-check.

## 4. Observations (not defects)

- **A contradiction does not lower the SPRS score.** The contradiction scenario
  still reports **SPRS 110 / Final / valid_submission=True** because SPRS is
  attestation-authoritative (the control *is* attested MET). R13 is the honesty
  overlay: the contradiction is surfaced as a first-class `contradictions: 1`
  metric in `audit.md` and the SSP colophon — exactly its intended role (prevent a
  clean-looking 110 from hiding a failing oracle). Reviewers must read the
  contradiction count alongside the score; a `110/Final` with `contradictions ≥ 1`
  is **not** clean.
- **Most MET controls are human-only** (17–18 of 22): only the machine-oracle
  controls resolve from a config check, so the rest resolve human-only through
  the attested-reference oracle (`passed` / `needsAction` / `failed`) — every
  required control lands on a concrete outcome, consistent with R4/R13.
- All demo output carries `evidentiary_status=mock` / the NON-EVIDENTIARY banner —
  a compiled **demo** BOM/SSP, never a submittable one (R12 working as designed).

## 5. Defects

**None found.** The full suite is green, all three scenarios behave to the plan's
end-to-end acceptance criteria, and the four R spot-checks hold against the cited code.

## 6. Verdict — **GO**

The NV012 engine is accepted for the Phase-I / Tier-1 as-built milestone. Standing
caveats (all documented, none blocking):

- **NON-EVIDENTIARY:** evidence is fixture-backed (mock); every BOM/SSP is marked
  and banner-stamped. A live-tenant evidence pass is required before any real
  submission.
- **Terraform is plan-level only** (offline providers; no live apply/cloud).
- **Sigstore signing deferred** (SHA-256 write-once registry seam in place).
- **IL5 overlay deferred to Phase II** (`OBL-IL5` resolves empty in Phase I).

---
*QA sign-off is engineering acceptance of the as-built milestone, not legal
attestation. CMMC/ITAR interpretations remain subject to the contracting officer,
C3PAO, and counsel.*
