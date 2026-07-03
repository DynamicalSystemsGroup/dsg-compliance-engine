# 05 — Try it yourself

This chapter is a hands-on run guide. You will run the Compliance Engine end to end on
your own machine, three times, and read the exact output each run produces. No cloud
account, no credentials, and nothing is deployed. If a term is unfamiliar, see the
[glossary](06-glossary.md).

The engine produces byte-deterministic output from a given set of inputs. The demo
inputs are fixed, so the output you see on your machine will match the output printed
in this chapter line for line.

---

## Prerequisites

You need two things, one of them optional.

```bash
# 1. Install dependencies with uv (https://docs.astral.sh/uv/)
uv sync

# 2. terraform is OPTIONAL.
#    The demo runs a real `terraform plan` only on the real plan path.
#    You only need terraform installed if you exercise that path.
#    Nothing is deployed either way: the plan uses mock providers,
#    no cloud is contacted, and no credentials are used.
```

The installed CLI entry point is `ce`. Two equivalent forms exist if you prefer them:
`compliance-engine` and `python -m compliance_engine`. This chapter uses `ce`.

Every run writes its artifacts into the directory you name with `--output-dir`. The
examples below write into `/tmp/...` so nothing is left in the repository.

The `demo` command runs the full chain in one shot:
`compile-order` then `run-factory` then `attest` then `audit` then `bom` then `ssp`.
The `--evidence-set` flag selects which fixture world the run uses, and `--auto`
runs the chain without stopping for input. The three values below —
`all-covered`, `gap`, and `contradiction` — are the three scenarios in this chapter.

---

## Scenario A — the covered run (all-covered)

Everything the NV012 contract requires is covered by a claiming module and signed off
by a human in the required role. This is the run that completes cleanly.

```bash
uv run ce demo --evidence-set all-covered --auto --output-dir /tmp/nv012-all
```

Output (the many per-control MET lines are trimmed; every summary line is verbatim):

```
[demo] evidence-set=all-covered
[1/6 compile-order] Order cdad6fb17f7cb53728276bb24de654c87b6725e31b9bd731efa7769234afbc85 (22 controls)
[Preflight] Probing backends...
  Provision: FakeProvisionBackend (compliant, deterministic, no terraform)
  Storage:   Local filesystem (rdflib Dataset, persisted as output/engine.ttl + output/engine.trig)
  Provision probe: PASS
  Storage probe:   PASS
[2/6 run-factory] 20 evidence nodes, 51 oracle outcomes
[3/6 attest] 22 control(s) attested (Gate 2)
[4/6 audit]
SPRS: score=110 status=Final valid_submission=True
Proven vs attested: 4 MET-by-machine / 18 MET-by-human-only
Contradictions (attested MET over failed machine check): 0
[5/6 bom] 4df1499a6b9949bf0e12c3bf5d502428a04debb28db189b897131f6b70903d7c evidentiary_status=mock -> /tmp/nv012-all/bom.json
[6/6 ssp]
SSP: wrote /tmp/nv012-all/ssp.md (NON-EVIDENTIARY banner: present)
```

Exit code: `0`.

### What it proves

The full chain runs. Gate 1 passes and emits a signed Order over 22 required controls.
The runtime (called the Factory in the code) plans the environment, collects evidence,
and runs the oracles. All 22 required controls are attested MET at Gate 2. The audit
computes an [SPRS](06-glossary.md#sprs) score of 110 with status Final and
`valid_submission=True`, and reports zero contradictions. A
[BOM](06-glossary.md#bom) and an [SSP](06-glossary.md#ssp) are written. This is the
scenario walked through in [01-the-order.md](01-the-order.md),
[02-the-factory.md](02-the-factory.md), and [04-the-proof.md](04-the-proof.md).

### The honest caveats

Read the summary lines carefully; they are designed to keep you from being misled.

- **Only 4 of the 22 required controls are machine-proven.** The line
  `4 MET-by-machine / 18 MET-by-human-only` says the machine oracle actually proved 4
  of the required controls; the other 18 rest on human attestation. That split is over
  the Order's 22 required controls, not over the whole catalog.
- **The `20 evidence nodes, 51 oracle outcomes` counts are not the score.** Those are
  the totals the runtime collects over this evidence-set's entire fixture world. The
  NV012 Order still requires only 22 controls, and the SPRS score and the
  proven-vs-attested split are computed over those 22. The score does not cover all 110
  controls, and the 51 oracle outcomes do not all feed the score.
- **The BOM and SSP are mock.** The BOM is stamped `evidentiary_status=mock`, and the
  SSP is written with the NON-EVIDENTIARY banner present. See "What is real versus
  pretend" below. A score of 110 / Final here does not make either document a
  submittable government artifact.

---

## Scenario B — the coverage gap (gap)

This run asks for a control that nothing can cover, so the compiler refuses before
anything is built.

```bash
uv run ce demo --evidence-set gap --auto --output-dir /tmp/nv012-gap
```

Output:

```
[demo] evidence-set=gap
[1/6 compile-order] Gate 1 REFUSED — Order NOT emitted. Obligation cites control ID 'XX.L2-3.99.99', which is not one of the 110 controls in cmmc-edit.ttl.
```

Exit code: `2`.

### What it proves

The compiler will not emit an Order it cannot fully cover, and it names the problem
instead of dropping it. Here the drafted obligations cite control ID `XX.L2-3.99.99`,
which the catalog validator does not recognize, so the run stops at step 1 and the
Factory never starts. Exit code 2 signals a Gate 1 refusal (or bad arguments), distinct
from a clean completion.

There is a nuance worth stating plainly. All 110 real catalog controls now have a
claiming module, so a genuine "required but unclaimed" gap cannot occur with a real
control. To still exercise the lesson, this scenario injects a fake, non-catalog
control ID (`XX.L2-3.99.99`) that the catalog validator rejects before Gate 1 even
runs. The point is identical either way: the compiler refuses to emit an Order it
cannot fully cover, and it tells you exactly what is wrong. Gate 1 itself is described
in [01-the-order.md](01-the-order.md).

---

## Scenario C — the contradiction (contradiction)

This run completes and even scores 110 / Final, but a machine oracle fails on one
control while a human still attests that control MET, with no written override
justification. The audit surfaces that conflict rather than letting the score hide it.

```bash
uv run ce demo --evidence-set contradiction --auto --output-dir /tmp/nv012-con
```

Output (tail; earlier lines match Scenario A's shape):

```
[2/6 run-factory] 7 evidence nodes, 6 oracle outcomes
[3/6 attest] 22 control(s) attested (Gate 2)
[4/6 audit]
SPRS: score=110 status=Final valid_submission=True
Proven vs attested: 3 MET-by-machine / 19 MET-by-human-only
Contradictions (attested MET over failed machine check): 1
[5/6 bom] 1cb90743ec6b98d421a7ccc5dd73c4da801269fe4b94bfa88c6ab4e45f5658ee evidentiary_status=mock -> /tmp/nv012-con/bom.json
[6/6 ssp]
SSP: wrote /tmp/nv012-con/ssp.md (NON-EVIDENTIARY banner: present)
```

Exit code: `0`.

### What it proves

The run completes and the numeric score is again 110 / Final with
`valid_submission=True`. That number alone is not a clean result. Two lines tell the
real story:

- `Proven vs attested: 3 MET-by-machine / 19 MET-by-human-only` — one control that was
  machine-proven in Scenario A now fails its oracle, so the machine-proven count drops
  from 4 to 3 and the human-only count rises from 18 to 19.
- `Contradictions (attested MET over failed machine check): 1` — this is the R13
  contradiction, described in [03-machine-vs-human.md](03-machine-vs-human.md) and
  [04-the-proof.md](04-the-proof.md). A human marked a control MET while its machine
  oracle failed, with no written override justification, so the audit reports it
  separately from the score. The score does not silently absorb the conflict.

> Important: a 110 / Final result with `contradictions: 1` is not a clean pass. The
> score and the contradiction list are reported separately on purpose. Read both. A
> written override justification is what clears the contradiction; without one, the
> unexplained human-over-machine call is left visible for an assessor.

---

## What lands in the output directory

After Scenario A, listing `/tmp/nv012-all/` shows the artifacts of the run. Each is
described in full in [04-the-proof.md](04-the-proof.md).

| Artifact | What it is |
| --- | --- |
| `bom.json` | The Bill of Materials. Per required control: the claiming module(s), evidence hashes, oracle outcome, attestation outcome, and status. Content-addressed by its own SHA-256, stored write-once, and stamped with the weakest evidentiary status present. |
| `ssp.md` | The System Security Plan. Deterministic, compiled from the same dataset the BOM records. Its centerpiece is the per-control traceability matrix (also called the VCRM). It emits the NON-EVIDENTIARY banner structurally when the inputs are mock. |
| `audit.md` | The bidirectional audit in human-readable form: the SPRS score, POA&M legality, and the contradiction list, plus the forward and backward passes. |
| `audit.json` | The same audit content in machine-readable form. |
| `engine.trig` | The full RDF named-graph dataset for the run — every lifecycle layer (ontology, plan, structural, order, evidence, attestations, plan-execution, audit) in one file. |
| `registry/` | The write-once, content-addressed object store, plus a two-level index (contract, then BOM, then artifact hashes). Every artifact is keyed by its hash. |
| `run_state.json` | The per-stage run-state summary: order hash, evidence hashes, oracle outcomes, and resources, for inspection and debugging. |

---

## What is real versus pretend

State this plainly to anyone reading the output. The engine runs a real software spine
end to end, but nothing it produces today is a submittable government artifact.

- **Every run is non-evidentiary.** Evidence is fixture-backed (from `fixtures/nv012/`)
  and the Terraform plan uses mock providers. Because a weak evidentiary status is
  present, the whole BOM and SSP are stamped NON-EVIDENTIARY, and there is no switch to
  remove that banner while mock inputs are present.
- **Terraform is plan-level only.** The runtime runs a real `terraform plan` with mock
  providers: no cloud is contacted, no credentials are used, and nothing is deployed.
  Live `terraform apply` is deferred.
- **The engine records claims; it does not make an organization compliant.** A false
  claim still passes here. The human signer — the Affirming Official — carries the legal
  accountability, and an assessor is expected to catch a false claim on reproduction.
- **References are not resolved live yet.** They resolve against local files and
  fixtures, not live systems.
- **Attestations are not cryptographically signed yet.** Trust today is the Git history
  of the attestation file. Sigstore/cosign is scaffolded (there is a `sig_algo` field)
  but not wired.
- **The engine does not talk to SPRS.** It computes the score; a human files that score
  at the government portal.
- **The 16 policy documents under `src/compliance_engine/documents/policies/` are
  scaffolding** and must be replaced with an organization's own adopted policies.
- **Also deferred:** live evidence resolvers, cloud (GCS/Azure) registry backends, and
  an approval gate.

None of this is hidden by the tool. The NON-EVIDENTIARY banner, the `mock` stamp, and
the proven-versus-attested split are all in the output for exactly this reason.

---

## Summary

Three commands show the whole system on your own machine, and because the output is
byte-deterministic, yours matches this chapter exactly. The `all-covered` run completes
with a score of 110 / Final and writes a mock BOM and SSP; the `gap` run makes Gate 1
refuse and name the offending control ID before anything is built (exit code 2); and
the `contradiction` run completes at 110 / Final yet loudly reports one contradiction,
showing that the score never absorbs an unexplained human-over-machine call. Every
document produced is stamped NON-EVIDENTIARY because the evidence is still
fixture-backed.

Next: the glossary ([06-glossary.md](06-glossary.md)).
