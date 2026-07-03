# 00 — What is this?

This is the first stop on a plain-English tour of the Compliance Engine. It gives
you the whole picture in one sitting: the problem the engine solves, the two ideas
at its core, what it covers, how it is built out of two machines with a clean seam
between them, the two gates that keep it honest, and an unvarnished list of its
current limits. Later chapters go deep on each part. If a term is unfamiliar, the
[glossary](06-glossary.md) defines every one of them.

In one line: the Compliance Engine ingests a signed description of what a contract
requires and a signed set of statements about how an organization satisfies each
requirement, and it emits a System Security Plan, a Bill of Materials of the
supporting evidence, and a Supplier Performance Risk System (SPRS) score. Every automated check, every piece of
evidence, and every human sign-off is content-addressed and cross-linked, and no
requirement is recorded as met until a named, role-appropriate human signs a
statement to that effect.

## The problem, in plain terms

A U.S. defense contractor that handles the government's sensitive-but-unclassified
information must prove it runs a secure operation. That information is called
[Controlled Unclassified Information (CUI)](06-glossary.md): data that is not
classified as secret but is still restricted and must not leak. To handle it, a
contractor has to meet a security standard.

The standard here is [CMMC](06-glossary.md) Level 2, which is defined as the 110
security [controls](06-glossary.md) of [NIST SP 800-171](06-glossary.md) Rev. 2. A
control is a single required security practice — for example, requiring multi-factor
authentication for privileged access, or keeping audit logs, or having a written and
tested incident-response plan. There are 110 of them, and they range from settings a
computer can measure to policies and records that only a person can vouch for.

Proving you meet those controls produces two artifacts an assessor expects to see:

- A [System Security Plan (SSP)](06-glossary.md): the document that describes, control
  by control, how the organization satisfies each requirement.
- A [Supplier Performance Risk System (SPRS)](06-glossary.md) score: a single number,
  filed at a government portal, that summarizes how many of the required controls are
  met, weighted by importance.

Here is the painful part today. That proof is assembled by hand. People take
screenshots of settings, fill in spreadsheets, and stitch together a binder for an
auditor. It is slow, error-prone, and it goes stale the moment someone changes a
setting after the screenshot was taken. The paper says one thing; the live system
may already say another. The Compliance Engine exists to close that gap.

## The two big ideas

Two ideas do the real work in this system. Neither is optional; both should be in
your head before you read further.

### 1. Provisioning and proving are the same action

The environment is described by a signed [Order](06-glossary.md), and the proof of
compliance is produced from that same description — not gathered afterward by
inspection. You do not build the environment and then, weeks later, send someone
around to document what got built. The description of what must be true and the
proof that it is true come from one source, produced in one connected action. If the
description changes, the proof changes with it. There is no window in which the
binder and the live system are allowed to drift apart, because they are not two
separate things.

### 2. The attested-reference model

This is the idea that lets the engine cover all 110 controls rather than only the
ones a machine can measure, so it deserves real weight here.

Every control points at an *authoritative source*: the place where the truth of that
control actually lives. For a firewall rule, that is a cloud API. For security-awareness
training, it is a learning-management system. For personnel records, it is an HR
system. For a written policy, it is a document repository. For a control proven by the
engine's own past runs, it is the engine's run history. The authoritative source is the
system that owns the ground truth for a whole class of evidence.

Each control then carries a *reference* into that source: a resolvable pointer with a
URI, a freshness window (how long the reference stays valid before it must be
re-verified), a last-verified timestamp, and a named custodian. And each control names
a required attestation *role* — which kind of official must sign it.

The engine applies one uniform check to every control. It confirms that the reference
is registered, that it resolves, that it is within its freshness window, and that it is
signed by a human in the required role. That same four-part check works identically
whether the control is something a machine can measure (a firewall setting) or
something only a human can attest (a tested incident-response plan). Because the check
does not depend on the control being machine-measurable, the engine can cover the
policy-and-records controls on equal footing with the technical ones. That is what
takes coverage from "the machine-measurable subset" to all 110.

> These two ideas are the point of the system. Everything else — the two machines,
> the two gates, the outputs — exists to carry them out faithfully.

## What it covers: 110 controls, all now claimed

The control catalog holds 110 controls, and every one of them now has a claiming
module — a unit of the engine that takes responsibility for the control and names how
it will be verified. There are 39 modules in total. The controls split across three
verification kinds:

| Verification kind | Controls | What it means |
|---|---|---|
| Machine-verified (config-check oracle) | 65 | The control is measured directly from configuration. |
| Attested-reference | 43 | A registered, fresh, signed reference into an authoritative source. |
| CSP-inherited | 2 | Satisfied by the cloud service provider and inherited. |
| **Total** | **110** | |

The modules group into three sets:

- **Baseline (Tier 1)**: 10 modules covering 22 controls — 20 machine-verified plus
  the 2 inherited.
- **Track A (machine)**: 13 modules covering 45 controls. These are the technical
  controls — for example VPC segmentation, endpoint detection, mobile-device
  management, Security Command Center, Workspace admin policy, BeyondCorp remote
  access, GitHub change management, operations MFA, Cloud Logging, Binary Authorization
  allowlisting, session control, VPC Service Controls, and IAM privileged-use.
- **Track B (attested-reference)**: 16 modules covering 43 controls. These are the
  policy-and-records controls — training, incident response, risk assessment,
  personnel security, configuration management, maintenance, media protection, audit
  procedure, security engineering, remote-access authorization, physical access,
  collaborative computing, separation of duties, continuous monitoring, and login
  banner.

The structural model claims all 110 controls. The shipped demonstration contract,
[NV012](06-glossary.md), exercises a 22-control slice of that model — a manageable,
runnable subset for the demo. When the demo computes an SPRS score, it scores over the
Order's 22 required controls, not all 110. Keep that distinction in mind: the model is
built for 110; the demo runs 22.

## The two machines and the hand-off

The engine is two separate machines that pass a single file between them.

The first machine is the **Order Compiler** (upstream). It reads a contract and
produces a signed Order. The flow inside it is:

- A contract comes in.
- Software drafts the contract's obligations, and a [Compliance Officer](06-glossary.md)
  attests them.
- A rule library turns those obligations into the required-control set.
- Gate 1 checks that the plan fully covers that set (described below).
- If Gate 1 passes, the Order Compiler emits a signed Order.

"Signed" here means hash-referenced: the Order is fixed to a [SHA-256](06-glossary.md)
fingerprint so any later change is detectable. True cryptographic signing
(Sigstore/cosign) is future work. One safety property is worth naming now: a CUI or
ITAR deliverable cannot silently drop a requirement. A spillover guard forces human
review instead of quietly dropping controls.

The second machine is the **Runtime**, called "the Factory" in the code (downstream).
It consumes a signed Order and runs it through stages: load the Order and re-check its
hashes, fetch each module by hash, run a real terraform plan (with mock providers, so
no cloud is contacted, no credentials are used, and nothing is deployed), run a
policy-as-code check that includes a data-residency hard gate, run a mock apply (a live
apply is deferred), collect evidence, and run the [oracles](06-glossary.md).

The clean seam between the two machines is deliberate. The **Order** is the only thing
that passes between them. The Order Compiler decides *what must be true*; the Runtime
makes it true and proves it. The Runtime does not care how the Order was written — it
just executes it. That separation lets each machine be reasoned about, and audited, on
its own.

> Provisioning and proving are the same action precisely because these two machines
> share one Order: the Order describes the environment, and the Runtime produces the
> proof from that same Order.

## The two gates

The engine refuses to fool itself. Two gates must pass, one in each machine.

**Gate 1 — planning coverage.** This runs in the Order Compiler, before anything is
built. It enforces three things: *forward* (every required control has at least one
claiming module), *backward* (every included module traces back to a required control),
and *no untestable claim* (every claiming module names a verification method). If any
of these fails, the Order is not emitted and the specific gap is named. Nothing gets
built on an incomplete plan. The code is
`src/compliance_engine/order_compiler/gate1.py`.

**Gate 2 — proven fulfillment.** This runs in the Runtime, at the point the Bill of
Materials is closed. A control is recorded as met only when its evidence passes its
oracle *and* a human attests it in the required role. The Bill of Materials'
control-mapping is then audited against the Order's required set, forward and backward,
so the proof matches the plan in both directions. The code is
`src/compliance_engine/traceability/audit.py`.

Read simply: Gate 1 is the promise that the plan covers everything. Gate 2 is the
receipt that it was actually done and a human vouches for it.

## The founding principle

One sentence governs the whole design:

> Evidence does not verify requirements; evidence supports a human judgment that
> requirements are satisfied.

Machines provision the environment, gather evidence, and run automated checks, which
are recorded as automatic assertions. But a control is marked met only when a human —
the [Affirming Official](06-glossary.md) — attests it, recorded as a manual assertion.
That human carries legal accountability under the False Claims Act, and under 18 U.S.C.
section 1001 for false statements to the federal government. The same line holds on the
input side: software drafts the contract's obligations, and a Compliance Officer
attests them. In the data model itself, evidence *addresses* a control and only a human
attestation *attests* it — and this is enforced in the graph, not merely by policy.
Chapter [03-machine-vs-human.md](03-machine-vs-human.md) explains this in full.

## Honest limits

It matters to state plainly what is not yet real. None of this is buried in fine print.

- **Every run today is non-evidentiary.** Evidence is fixture-backed and the terraform
  plan uses mock providers. Nothing produced today is a submittable government artifact.
- **The engine records claims; it does not make an organization compliant.** A false
  claim still passes here. A human signer carries the accountability, and an assessor
  catches it.
- **References are not resolved live yet.** They resolve against local files and
  fixtures rather than reaching out to the real authoritative source. References now
  carry a pinned version and a signature field for the signed-policy model, but the
  live resolvers are deferred.
- **Attestation signing is wired, but the production key path is deferred.** The engine
  signs and verifies attestation records with real Ed25519 signatures today, and rejects
  a tampered or unverifiable signed record at load (fail-closed). The production
  cosign + FIPS-KMS path is implemented behind a probe and switches on when the cosign
  binary and KMS key are present. The demo runs unsigned (`sig_algo=none`, git-trust) and
  is stamped NON-EVIDENTIARY.
- **The append-only tier of record is wired, but the live server is deferred.** A Flexo
  MMS backend persists each run to an append-only, versioned store (`--store-backend
  flexo`); it is offline-simulated here, with the local registry retained as the
  cache/fallback tier. Standing up a live in-enclave Flexo server is deferred.
- **The engine does not talk to SPRS.** A human files the computed score at the
  government portal.
- **The 16 policy documents** under `src/compliance_engine/documents/policies/` are
  scaffolding and must be replaced with an organization's own adopted policies.
- **Deferred work** includes: live terraform apply, live evidence resolvers,
  cosign + KMS signing (Ed25519 works today), a live Flexo MMS server (the backend is
  wired and offline-simulated), cloud (GCS/Azure) registry backends, and an approval gate.

What is now real end to end: full-chain P-Plan provenance (contract to BOM/SSP, with an
SOP-adherence check), cryptographically-signed attestations, an append-only storage tier,
and a single signed **audit package** (`ce package` / `ce verify-package`) an assessor can
re-verify offline.

Note: none of this makes the demo misleading. The mechanism is wired end to end; it
simply runs on stand-in inputs until live integration is switched on, and it stamps
every output NON-EVIDENTIARY so no one mistakes a practice run for a real submission.

## Summary

The Compliance Engine turns a contract's security requirements into a proven cloud
environment, treating provisioning and proving as one action rather than two. It
targets CMMC Level 2 — the 110 controls of NIST SP 800-171 Rev. 2 — and covers all of
them, not just the machine-measurable ones, by using a single attested-reference check
that works the same whether a control is measured by a machine or attested by a person.
Two machines carry this out across a clean seam: the Order Compiler decides what must
be true and emits a signed Order, and the Runtime executes that Order to make it true
and prove it. Two gates keep the process honest — Gate 1 refuses to build on an
incomplete plan, and Gate 2 records a control as met only when evidence passes its
oracle and a named human attests it. Above all, evidence supports a human judgment; it
never replaces one.

**Next: [01-the-order.md](01-the-order.md)**
