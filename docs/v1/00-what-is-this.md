# 00 — What is this?

## The problem, in plain words

If a company wants to handle the US Department of Defense's sensitive
information — the kind that isn't secret but still shouldn't leak, called
**CUI** (Controlled Unclassified Information) — it has to follow a big checklist
of security rules. The checklist is **CMMC Level 2**, which is built from a
government standard called **NIST SP 800-171**. It has about **110 rules**
(things like "require multi-factor login" or "encrypt sensitive data").

> **CUI, CMMC, NIST 800-171, control** → see [glossary](06-glossary.md).

Here's the painful part: today, _proving_ you follow those rules is mostly
manual. People take screenshots of settings, fill in spreadsheets, and assemble
a giant binder for an auditor. It's slow, error-prone, and goes stale the moment
someone changes a setting.

## The one big idea

> **Building the secure environment and proving it's compliant are the SAME
> action.**

**Analogy.** Imagine a factory that builds a product. Instead of building it and
_then_ sending an inspector around later, this factory stamps a **certificate of
authenticity as a byproduct of building the product** — the certificate is
produced by the same machine, from the same steps, at the same time. If the
build changes, the certificate changes with it. You can't have one without the
other.

That's what this system does for cloud security setups. Compliance isn't
gathered _after_ the fact by inspecting an existing setup — it's a **byproduct of
building the setup in the first place.**

## The two machines and the hand-off

The system is two separate machines that pass a single file between them:

```
   A contract (with security requirements)
            │
            ▼
   ┌──────────────────────┐        ┌──────────────────────┐
   │   ORDER COMPILER      │  the   │      THE FACTORY      │
   │  turns the contract   │ signed │  executes the Order:  │
   │  into a signed build  │ Order  │  build it + gather    │
   │  "Order"              │ ─────► │  the proof            │
   └──────────────────────┘  file  └──────────────────────┘
       "what must be true"            "make it true + prove it"
```

1. **The Order Compiler** reads a contract and turns it into a **signed Order** —
   a precise, tamper-evident "build order" that says exactly which security rules
   this environment must satisfy and which pieces of cloud setup will satisfy
   them. (Details in **[01 — The Order](01-the-order.md)**.)
2. **The Factory** takes that Order and executes it: it plans the environment,
   checks it against policy, gathers evidence, and runs automated checks.
   (Details in **[02 — The Factory](02-the-factory.md)**.)

The **Order file** is the only thing that passes between them. The Factory
doesn't care how the Order was written; it just executes it. This clean seam is
deliberate.

> **Order, module, evidence, oracle, attestation, BOM, SSP** → see
> [glossary](06-glossary.md).

## The two safety gates

The system refuses to fool itself. Two "gates" must pass:

- **Gate 1 — before anything is built:** _"Don't start unless the plan actually
  covers every required rule."_ Every required rule must have a piece of setup
  claiming to satisfy it, every piece of setup must trace back to a required
  rule, and every claim must be testable. If something's missing, **the Order is
  refused and names exactly what's missing** — nothing gets built.
- **Gate 2 — at the end:** _"A rule only counts as MET when a responsible human
  signs off, backed by evidence."_ A machine can gather evidence and run checks,
  but it can **never** declare a rule satisfied. Only a human — the Affirming
  Official — does that, and they carry the legal accountability. (More in
  **[03 — Machines vs. humans](03-machine-vs-human.md)**.)

Gate 1 is a promise ("the plan covers everything"). Gate 2 is the receipt ("and
we actually did it, and a human vouches for it").

## The honesty line (read this)

This is a **Phase-I prototype**, and it's important to be straight about what's
real:

- **Everything runs on fake (mock) data.** The evidence comes from example files
  in the repo, not a live cloud.
- **Terraform runs in preview (plan) mode only, with mock providers.** Terraform
  is the tool that would normally build cloud infrastructure — here it only
  _describes_ what it would build. **Nothing is deployed. No cloud account. No
  credentials. Nothing is created.**
- Because of that, **every output is stamped `NON-EVIDENTIARY`** — it's a
  practice artifact that demonstrates the machinery, **not** a real submission to
  the government.

None of that makes the demo fake in a misleading way — the _mechanism_ is fully
wired end to end. It just runs on stand-in data until real cloud integration is
switched on. You can run it yourself in **[05 — Try it yourself](05-try-it.md)**.

## In one sentence

This is a machine that turns a contract's security requirements into a built,
checked, and proven cloud environment — as one connected action — shown today as
a fully-wired mock run.

**Next: [01 — The Order](01-the-order.md)**
