# The Factory (the runtime)

The second machine is the runtime, called the **Factory** in the code. It takes a
single signed Order — the output of the Order Compiler described in
[01-the-order.md](01-the-order.md) — and executes it through a fixed sequence of
stages. Along the way it provisions the described environment (at plan level),
gathers machine-readable facts, and runs automated checks. What it produces is a
**run record**, not a verdict.

That distinction is the whole point of this chapter, so it is worth stating plainly
up front: the Factory never says a control is met. It provisions, it collects
evidence, and it records automated check results. Whether a control is actually met
is decided later, by a human signature, and that step is covered in
[03-machine-vs-human.md](03-machine-vs-human.md). Everything the Factory does is
recorded and content-addressed so that the human deciding, and the assessor checking
the human, can trace each fact back to where it came from.

New terms in this chapter — Order, module, oracle, evidence, evidentiary status,
residency gate, PipelineState — are all defined in
[06-glossary.md](06-glossary.md).

## What the Factory is for

The Factory's job is to run the signed Order to completion and emit a faithful
record of what happened at each stage. It is the runtime half of the system's first
big idea: **provisioning and proving are the same action.** The environment is
described by a signed Order, and the proof of compliance is produced from that same
description — not gathered afterward by walking around and inspecting a running
system. The Factory is where "produced from the same description" actually happens.

Because of that, the Factory is deliberately not a judge. It records **automatic
assertions** (the results of automated checks) and it binds **evidence** to the
controls that evidence is about. It does not, and cannot, mark a control met. In the
data model, evidence only ever *addresses* a control; only a human attestation
*attests* it, and that rule is enforced in the graph, not by convention. So even at
its most successful, a Factory run hands off a set of facts and check results for a
human to judge.

The runtime lives under `src/compliance_engine/pipeline/` (`runner.py`,
`dataset.py`, `state.py`, `registry.py`, and the `provision/`, `backends/`, and
`evidence/` subpackages).

## The stages, in order

The Factory runs the Order through the following stages in sequence. Each stage
writes into the run record, and a failure in an early stage can halt the run before
later stages execute.

1. **Load the Order.** The Factory reads the signed Order and **recomputes its
   hashes, then re-checks them against the hashes recorded in the Order.** If any
   recomputed hash does not match, the run stops immediately. This is a tamper check:
   the Order was fingerprinted with SHA-256 when the Order Compiler emitted it (see
   [01-the-order.md](01-the-order.md)), and if a single byte changed in between, the
   fingerprints no longer match and the Factory refuses to build from it.

2. **Fetch the modules by hash.** The Order names each module it needs by hash. The
   Factory resolves each one out of the write-once, content-addressed object store by
   that hash. Fetching by hash rather than by name means the Factory gets exactly the
   module the Order committed to, and any substitution is caught because the hash
   would not resolve.

3. **Plan.** The Factory runs a **real `terraform plan`** against the real
   infrastructure-as-code under `infrastructure/terraform/tier1/` — but with **mock
   providers**: no cloud is contacted, no credentials are used, and nothing is
   deployed.

   To make sense of this, it helps to separate two Terraform actions. A
   `terraform plan` computes what *would* change — it reads the desired
   configuration, compares it against current state, and produces a concrete,
   inspectable description of the resources and settings that an apply would create
   or modify. A `terraform apply` is the step that *actually makes those changes* in
   the real world. Plan is "here is exactly what I would do"; apply is "now do it."

   A **mock provider** stands in for the real cloud provider plugin. A normal
   provider (for example, the cloud vendor's provider) is the piece that would talk to
   the live cloud API to read and write real resources. A mock provider satisfies the
   same interface so that `terraform plan` runs and produces a real, structured plan,
   but it answers locally instead of reaching out — so the plan is genuine while no
   cloud is touched, no credentials are needed, and nothing is created. The result is
   a real plan document describing the intended environment, produced offline.

4. **Policy check and the residency hard gate.** The Factory runs a policy-as-code
   check that **reads the real plan produced in the previous stage.** Inside that
   check is a **data-residency hard gate**. The gate **halts the run before apply if
   any planned region is non-US, or if the plan carries no region signal at all.**
   Both conditions fail closed: a region outside the United States is a violation, and
   a plan that cannot even be shown to be in-region is treated as a violation too, so
   silence is never mistaken for compliance.

   Why read the real plan instead of a checkbox? Because that is what
   provision-equals-prove means in practice. A checkbox that says "US region: yes" is
   an assertion *about* the environment that can drift away from the environment. The
   residency gate instead reads the same plan the environment would actually be built
   from, so the thing being checked and the thing being built are one and the same
   artifact. If the plan does not clearly put every region in the United States, the
   run stops here, before anything is applied.

5. **Apply.** Today this stage is a **mock apply**; a **live `terraform apply` is
   deferred** (planned, not built yet). The mock apply advances the run through the
   stage that would, in a future version, actually create resources — but in the
   current system nothing is deployed. This is consistent with the honest limits
   below: every run today is offline and non-evidentiary.

6. **Collect evidence.** The Factory gathers **evidence** — machine-readable facts
   that **address** controls. It is important to hold the line here: evidence points
   at the controls it is relevant to; it never marks them met. Marking a control met
   requires a human attestation, which is a separate machine and a separate chapter
   ([03-machine-vs-human.md](03-machine-vs-human.md)).

   Every piece of evidence carries an **evidentiary-status** stamp that says how
   trustworthy the underlying fact is. Today there are three stamps, and all three are
   non-evidentiary:

   - **`mock`** — a fixture configuration export (a stand-in config fact, not a real
     one).
   - **`mock-plan`** — derived from the real `terraform plan` (a real plan, but the
     plan itself came from mock providers).
   - **`attested-reference-mock`** — a fixture attestation standing in for a policy
     control (a Track B control; see the evidence-set table below and
     [03-machine-vs-human.md](03-machine-vs-human.md)).

   The rule on these stamps is strict: **if any weak stamp is present anywhere in the
   run, the whole BOM and SSP are stamped `NON-EVIDENTIARY` and are not submittable.**
   The run inherits the weakest status it contains. There is no switch to remove the
   banner while mock inputs are present — the only way to earn a submittable artifact
   is to feed the Factory real evidence, which the current system does not yet do.

7. **Run the oracles.** Finally, the Factory runs the **oracles** — the automated
   checks — over the collected evidence. Two kinds are in play here:

   - **config-check oracles** for the machine-measurable controls (the 65
     machine-verified controls), which read a config-level fact and decide whether it
     meets the rule.
   - the **attested-reference oracle** for the policy-and-records controls (the 43
     attested-reference controls), which checks that a reference into an authoritative
     source is registered, resolves, is fresh, and is signed by a human in the
     required role.

   Each oracle returns one of three outcomes: **`passed`**, **`failed`**, or
   **`needsAction`** (a concrete, actionable gap that always carries a reason). Every
   required control resolves to one of these. These outcomes are recorded as automatic
   assertions in the run record. The full mechanics of the attested-reference oracle —
   its decision sequence, its roles, and its specific failure reasons — belong to
   [03-machine-vs-human.md](03-machine-vs-human.md); here it is enough to know the
   Factory runs it and records what it returns.

## What comes out: a run record, not a verdict

When the stages complete, the Factory produces a **run record** — in the code, a
**PipelineState** — summarized per stage in `run_state.json`. The run record captures
what was loaded, what was planned, what evidence was collected and with what stamps,
and what every oracle returned. It also carries the full RDF named-graph dataset for
the run (`engine.trig`) so the whole run is traceable.

What the run record does **not** contain is any statement that a control is met. No
Factory stage writes "MET" for any control. That word only enters the record later,
when a named, role-appropriate human signs an attestation — the step covered in
[03-machine-vs-human.md](03-machine-vs-human.md) — and it is confirmed at BOM close by
Gate 2, described in [04-the-proof.md](04-the-proof.md). The Factory hands the human a
complete, fingerprinted set of facts and check results, and stops there.

## The three evidence-set worlds

The demo runs the Factory against three different **evidence sets**, selected with the
`--evidence-set` flag. Each one simulates a different situation. Note one important
subtlety: the **`gap`** world never reaches the Factory at all — it is refused by
**Gate 1** inside the Order Compiler, before any Order is emitted, so the runtime does
not start.

| Evidence set | What it simulates | What the runtime does |
| --- | --- | --- |
| `all-covered` | A complete, well-formed run: every required control has a claiming module and supporting evidence. | The Factory runs all stages end to end, collects evidence, and records oracle outcomes. The run is stamped `NON-EVIDENTIARY` because inputs are mock. |
| `gap` | A missing-coverage situation. Because all 110 real catalog controls now have a claiming module, a genuine "required but unclaimed" gap cannot occur with a real control, so this injects a fake, non-catalog control id (`XX.L2-3.99.99`). | The runtime never starts. The catalog validator rejects the fake id and **Gate 1 refuses to emit the Order.** The lesson is the one Gate 1 always enforces: the compiler refuses to emit an Order it cannot fully cover, and names the problem. |
| `contradiction` | A control marked met by a human while its machine oracle failed, with no written override justification. | The Factory runs normally and collects evidence and oracle outcomes. The failed oracle result is recorded faithfully, which is what lets the later audit surface the contradiction (see [04-the-proof.md](04-the-proof.md)) instead of hiding it. |

The exact commands and full terminal output for all three worlds are in
[05-try-it.md](05-try-it.md).

## Honest limits of the Factory today

State these plainly, because they bound everything above:

- **Every run today is non-evidentiary.** Evidence is fixture-backed
  (`fixtures/nv012/`) and the `terraform plan` runs against mock providers. Nothing a
  run produces is a submittable government artifact.
- **The live apply is deferred.** The apply stage is a mock apply; no resources are
  ever deployed.
- **The Factory records claims; it does not make an organization compliant.** It
  provisions and gathers facts. A control is only met when a human signs, and that
  human — not the Factory — carries the accountability.

## Summary

The Factory is the runtime that consumes one signed Order and drives it through a
fixed sequence of stages: load and re-hash the Order as a tamper check, fetch its
modules by hash, run a real `terraform plan` under mock providers so no cloud is
touched, run a policy check whose data-residency hard gate reads that real plan and
halts before apply on any non-US or region-less plan, run a mock apply, collect
evidence that only *addresses* controls, and run the config-check and
attested-reference oracles to record `passed` / `failed` / `needsAction`
outcomes. Because inputs are fixture-backed and providers are mock, every stamp is
weak and the whole run comes out `NON-EVIDENTIARY`. What the Factory emits is a run
record (a PipelineState summarized in `run_state.json`, with the full dataset in
`engine.trig`) — a complete, fingerprinted set of facts and check results, and
deliberately not a statement that any control is met.

Next: [03-machine-vs-human.md](03-machine-vs-human.md)
