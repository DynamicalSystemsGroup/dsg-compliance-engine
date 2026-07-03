# The proof: what the run produces and how to read it

The previous chapter explained how a single control becomes MET (see
[03-machine-vs-human.md](03-machine-vs-human.md)). This chapter covers what the
runtime hands you at the end of a run, and how to read those outputs without being
misled.

Every run produces two checks and two documents, plus one idea that ties them
together:

- The **audit** answers "does the chain hold together, in both directions, and did
  any human overrule a machine?"
- The **SPRS score** turns the audit into the single number a defense contractor
  reports to the government, with a validity flag attached.
- The **BOM** (Bill of Materials) is the tamper-evident, content-addressed record
  of every control, its evidence, and its outcome.
- The **SSP** (System Security Plan) is the deterministic government document
  compiled from that same record.
- **Proof by reproduction** is the property that lets an outside assessor re-derive
  all of the above from the delivered artifacts alone, without trusting the party
  that produced them.

Terms in bold link to the [glossary](06-glossary.md). Every number, path, and output
string below is the real output of the shipped NV012 demonstration contract (see
[05-try-it.md](05-try-it.md)); none is invented.

All outputs are written under the `--output-dir` you pass on the command line.

---

## The audit

The audit is the bidirectional check that the evidence chain is complete and
consistent. Its code lives in
`src/compliance_engine/traceability/audit.py`, and it runs as stage 4 of the demo
chain. It reports along two directions plus two additional dimensions you must not
skip.

### Forward and backward

- **Forward.** Every control the **Order** requires has at least one claiming module,
  its evidence passed its **oracle**, and a human attested it in the required role.
  Nothing required is left unaccounted for.
- **Backward.** Every control-mapping row that made it into the BOM traces back to a
  control the Order actually required. Nothing floats free; no sign-off points at a
  control outside the Order's required set.

This is **Gate 2** at BOM close: the BOM's control-mapping is audited against the
Order's required set, forward and backward. A control is met only when its evidence
passes its oracle **and** a human attests it in the required role. Forward-and-backward
completeness is what makes the BOM a closed record rather than a pile of assertions.

### The proven-vs-attested split

The audit prints one line that separates what a machine proved from what rests on
human judgment alone. For the all-covered demo:

```
Proven vs attested: 4 MET-by-machine / 18 MET-by-human-only
```

All 22 required controls are MET. Of those, a machine oracle actually measured 4 of
them (a **config-check** oracle passed on real evidence). The other 18 are MET
because a named human in the required role attested them; the engine confirmed the
attested reference is registered, resolves, is fresh, and is signed by the right
role, but the truth of the control still lives in an authoritative source a human
vouched for, not in a machine measurement. This split is printed on purpose so that
"22 controls met" can never quietly imply "22 controls machine-proven."

### The contradiction list

The audit surfaces contradictions separately from the score. A contradiction
(referred to as R13 in the code comments) is a control a human marked MET while its
machine oracle failed or was absent, with no written override justification. It is
reported on its own line so an unexplained human-over-machine call cannot hide inside
a passing number. A written override justification clears the contradiction; the
absence of one is exactly what an assessor needs to see. The same
`src/compliance_engine/traceability/audit.py` computes this dimension.

For the all-covered demo the line reads:

```
Contradictions (attested MET over failed machine check): 0
```

For the contradiction demo, where one oracle deliberately fails but a human still
attests the control, it reads:

```
Contradictions (attested MET over failed machine check): 1
```

### The honesty point

> A score of 110 with status Final and `valid_submission=True` is **not** a clean
> result if the contradiction line is nonzero. The score and the contradiction list
> are separate on purpose. The score can read 110/Final while a human has overruled
> a failed machine check with no written justification. Read both lines together, or
> you have not read the audit.

In the contradiction demo the audit prints exactly that combination:

```
SPRS: score=110 status=Final valid_submission=True
Proven vs attested: 3 MET-by-machine / 19 MET-by-human-only
Contradictions (attested MET over failed machine check): 1
```

Score 110/Final, and one unexplained contradiction. The number alone would mislead;
the two lines together tell the truth.

---

## The SPRS score

The **SPRS** score is the single number a defense contractor reports for CMMC
Level 2. It is computed in `src/compliance_engine/traceability/sprs.py`.

### The formula

```
score = 110 - (sum of the weights of the controls that are NOT met)
```

Every control carries a weight of 1, 3, or 5. A fully met set of controls loses no
weight, so the score is 110. Each not-met control subtracts its own weight.

### The bands

| Score      | Status      | Meaning                                             |
|------------|-------------|-----------------------------------------------------|
| 110        | Final       | Every applicable control met.                        |
| 88 to 109  | Conditional | Permitted with a **POA&M** (a Plan of Action and Milestones). |
| Below 88   | Ineligible  | Not submittable.                                     |

### It is computed over the Order's required set, not all 110

This is the point most likely to be misread. The catalog has **110** controls, but
the SPRS score is computed over the **Order's required set**. For NV012 that set is
**22** controls, so the demo score of 110 is a full pass over those 22, not over the
whole catalog. The demonstration contract exercises a 22-control slice; the
structural model claims all 110, but the score is scoped to what this Order requires.

Do not read the demo's 110 as "all 110 controls proven." Likewise, do not read the
all-covered demo's `20 evidence nodes, 51 oracle outcomes` as feeding the score. Those
counts are collected over the whole fixture world for that evidence-set; the score and
the proven-vs-attested split are computed over the 22 met controls of the Order.

### What the numbers mean

A small breakdown of the all-covered demo:

| Number | What it counts                                                        |
|--------|-----------------------------------------------------------------------|
| 110    | Controls in the catalog (NIST SP 800-171 Rev. 2 / CMMC Level 2).      |
| 22     | Controls required by the NV012 Order (the demo's slice).              |
| 4      | Of the 22, machine-proven (a config-check oracle passed).            |
| 18     | Of the 22, met by human attestation alone.                           |
| 110 minus 22 = 88 | Catalog controls outside this Order's scope (not scored here). This 88 is a count of out-of-scope controls; do not confuse it with the SPRS Conditional-band threshold of 88 points above. |

### POA&M legality

The band alone does not decide whether a submission is valid. A separate legality
check gates it:

- Only **1-point** controls may be deferred onto a POA&M.
- Deferring a **3-point** or **5-point** control, or one of six specifically excluded
  1-pointers, sets `valid_submission=False` regardless of the numeric score.

So a score in the Conditional band with an illegal deferral is not a valid
submission, and the flag says so plainly. The demo, with every required control met,
reports `valid_submission=True`.

---

## The BOM

The **BOM** is written to `bom.json`. It is the machine-readable record of every
required control and what supports it. Each required control gets one row.

### Per-control row

| Field               | What it holds                                              |
|---------------------|-----------------------------------------------------------|
| control             | The control ID from the catalog.                           |
| resource / module   | The claiming module (and the resource it maps to).         |
| evidence hashes     | The content-address(es) of the supporting evidence.        |
| oracle outcome      | passed, failed, cantTell, or needsAction.                  |
| attestation outcome | The human sign-off result and the signer's role.           |
| status              | The control's overall status and evidentiary status.       |

### Content-addressed, write-once, weakest-status

- **Content-addressed.** The BOM has its own **SHA-256**. In the all-covered demo the
  BOM hash is `4df1499a6b9949bf0e12c3bf5d502428a04debb28db189b897131f6b70903d7c`; in
  the contradiction demo it is
  `1cb90743ec6b98d421a7ccc5dd73c4da801269fe4b94bfa88c6ab4e45f5658ee`. Change one byte
  and the hash changes, which is how tampering is detected.
- **Write-once.** It is stored in the registry write-once; a delivered BOM is not
  edited in place.
- **Inherits the weakest evidentiary status.** Evidence carries evidentiary-status
  tags: `mock` (a fixture config export), `mock-plan` (derived from the real
  terraform plan), and `attested-reference-mock` (a fixture attestation for a Track B
  control). All three are non-evidentiary. The BOM inherits the weakest status present
  across its evidence. The demo BOM is stamped `evidentiary_status=mock`:

```
[5/6 bom] 4df1499a6b9949bf0e12c3bf5d502428a04debb28db189b897131f6b70903d7c evidentiary_status=mock -> <dir>/bom.json
```

If any weak status is present, the whole BOM and SSP are stamped NON-EVIDENTIARY and
are not submittable. There is no switch to remove that stamp while mock inputs are
present.

### The registry index

The BOM does not live alone. The `registry/` directory is the write-once,
content-addressed object store, plus a two-level index that resolves
**contract to BOM to artifact hashes**. Given a contract, you find its BOM; given the
BOM, you find every artifact hash it references, and every one of those resolves back
to a stored object. That index is what makes proof by reproduction mechanical rather
than manual.

The full RDF named-graph dataset for the run is written to `engine.trig`, and a
per-stage run-state summary to `run_state.json`.

---

## The SSP

The **SSP** is written to `ssp.md`. It is the System Security Plan, the document a
contractor submits. It is generated by `src/compliance_engine/documents/ssp.py`.

### Deterministic and byte-stable

The SSP is compiled from the **same dataset** the BOM records, so the two cannot
disagree. Compilation is deterministic: the same inputs produce the same bytes every
time. This byte-stability is what lets an assessor re-compile the SSP and confirm it
matches, rather than eyeballing a hand-edited document.

### The traceability matrix

The centerpiece is the per-control **traceability matrix**, also called the **VCRM**.
For each control it shows the requirement, the module and resource that claim it, the
evidence, the oracle outcome, and the human attestation, in one row. A reader can
trace any single control from the contractual requirement down to the specific
evidence and the specific signature, and back up again.

### The NON-EVIDENTIARY banner is structural

When any input is mock, the SSP emits the **NON-EVIDENTIARY** banner structurally.
It is part of how the document is compiled, not a flag someone remembered to set, and
there is no switch to suppress it while mock inputs are present. The demo confirms it:

```
[6/6 ssp]
SSP: wrote <dir>/ssp.md (NON-EVIDENTIARY banner: present)
```

A submittable SSP would be produced only from real, live evidence. Today every run is
fixture-backed, so every SSP carries the banner honestly.

---

## Proof by reproduction

The reason this beats a folder of screenshots is that an assessor does not have to
trust the party that produced the delivery. Given a delivered BOM, an assessor (a
**C3PAO**) can re-derive the whole record:

1. **Resolve** every artifact by its hash from the registry.
2. **Re-hash** each artifact and confirm the fingerprint matches the record. If one
   byte changed, the hash will not match, and the tampering is caught.
3. **Re-run** the plan-level checks to confirm the control-to-resource-to-evidence
   mapping and the oracle outcomes match what the BOM records.

If every fingerprint matches and every re-run outcome agrees with the record, the
delivery is exactly what was signed, and its checks reproduce. The step-by-step
version, written for an assessor, is in
[docs/AUDITOR-GUIDE.md](../AUDITOR-GUIDE.md).

Note: reproduction confirms that the delivered record is internally consistent and
untampered, and that its automated checks re-run to the same outcomes. It does not by
itself make an organization compliant. A false claim can still pass the engine; the
human signer carries the accountability, and the assessor's reproduction plus review
is what catches it.

---

## Summary

A run produces two checks and two documents. The **audit** walks the evidence chain
forward and backward, prints the proven-vs-attested split (4 MET-by-machine /
18 MET-by-human-only in the all-covered demo), and lists contradictions separately so
that a score of 110/Final with one contradiction cannot pass as clean. The **SPRS
score** is 110 minus the weights of the not-met controls, banded into Final (110),
Conditional (88 to 109, with a legal POA&M), or Ineligible (below 88), computed over
the Order's 22 required controls rather than all 110, and gated by the POA&M-legality
rule that only 1-point controls may be deferred. The **BOM** (`bom.json`) is the
content-addressed, write-once, per-control record that inherits the weakest
evidentiary status (`mock` in the demo), indexed contract-to-BOM-to-artifact in the
registry. The **SSP** (`ssp.md`) is the deterministic, byte-stable government document
compiled from that same dataset, whose VCRM traces every control end to end and whose
NON-EVIDENTIARY banner is structural. And **proof by reproduction** lets an assessor
resolve every artifact by hash, re-hash to confirm, and re-run the plan-level checks
to independently confirm the record.

Next: [05-try-it.md](05-try-it.md)
