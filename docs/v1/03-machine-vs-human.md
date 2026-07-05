# 03 · Machines check, humans certify — how a control becomes MET

*Part of the v1 plain-English tour. Previous: [02-the-factory.md](02-the-factory.md).*

---

This chapter is the intellectual core of the Compliance Engine. The two previous
chapters described how a contract becomes a signed Order ([01-the-order.md](01-the-order.md))
and how the runtime builds and checks an environment from that Order
([02-the-factory.md](02-the-factory.md)). Neither of those steps, on its own,
declares a security control "met." This chapter explains the line the engine draws
between a machine measuring a fact and a human accepting legal responsibility for a
requirement, and it walks through the single mechanism — the attested-reference
model — that lets one uniform check cover all 110 controls.

Every unfamiliar term links to [06-glossary.md](06-glossary.md).

---

## The founding principle

> Evidence does not verify requirements; evidence supports a human judgment that
> requirements are satisfied.

Read that carefully, because it inverts a common assumption. Machines do not decide
that a control is satisfied. Machines provision infrastructure, gather evidence, and
run automated checks. The result of an automated check is recorded as an *automatic
assertion*: a mechanical reading of data, with no judgment and no accountability
attached.

A control is marked **met** only when a human — the **Affirming Official** — attests
it. That attestation is a *manual assertion*, and it carries real legal weight: the
False Claims Act, and 18 U.S.C. section 1001, which criminalizes false statements to
the federal government. The machine's check is an input to that judgment; it is not
the judgment.

The same line holds on the input side of the engine. Software drafts the contract's
obligations, but a **Compliance Officer** attests them before they become the
required-control set (see [01-the-order.md](01-the-order.md)). In both directions,
software prepares and a named human accepts responsibility.

---

## Verification versus validation

These two words sound interchangeable and are not. The distinction is the whole
chapter in miniature.

- **Verification** is a machine automatically checking a fact. Example: "the
  configuration export shows multi-factor authentication is enabled." This is a
  yes/no reading of data. It is automatic, repeatable, and carries no accountability.
- **Validation** is a responsible human certifying that the requirement is genuinely
  met. Example: "I, the Affirming Official, certify this control is satisfied, and I
  understand I am legally accountable for that statement." This is a judgment, and it
  is manual and accountable.

An analogy, stated only after the plain fact above: a spell-checker verifies that
every word in a contract is spelled correctly; it does not, and cannot, validate that
the contract says what you meant to agree to. A person has to read it and sign. The
engine keeps the spell-checker and the signer strictly separate, and it never lets
the spell-checker sign.

---

## Evidence addresses; only attestation attests

This separation is not a matter of policy that a diligent operator is expected to
follow. It is wired into the data model.

In the RDF graph (see [02-the-factory.md](02-the-factory.md) for the named-graph
layout, and [06-glossary.md](06-glossary.md) for the vocabulary), the two relationships
are different predicates:

- Evidence `ce:addresses` a control. Evidence is machine-readable facts that speak to
  a control, but "addresses" is deliberately weaker than "satisfies." It means the
  evidence is *relevant to* the control, not that the control is met.
- A human attestation `ce:attests` a control. Only this predicate marks a control met.

Because the predicates are distinct, no amount of evidence can flip a control to met
on its own. There is no code path in which a pile of `ce:addresses` links becomes an
`ce:attests` link without a human in the loop. The founding principle is enforced by
the shape of the graph, not by anyone remembering to follow a rule.

---

## The attested-reference model

This is the heart of the chapter, and the reason the engine can claim all 110 controls
rather than only the ones a machine can measure.

The problem it solves: many of the 110 NIST SP 800-171 Rev. 2 controls are not things a
machine can read off a configuration file. "Personnel are screened before being granted
access to CUI" lives in an HR system and a signed record, not in a cloud API. A pure
config-check approach can cover the machine-measurable controls and simply cannot reach
the rest. The attested-reference model gives every control — machine-measurable or not —
the *same* shape of check.

### What each module names

Every claiming module carries three things:

- an **authoritative source** (`ce:AuthoritativeSource`),
- a **reference** into that source (`ce:Reference`), and
- a required **attestation role** (`ce:attestationRole`).

### Authoritative source

An authoritative source is the system that owns the ground truth for a class of
evidence — the place where the truth of that control actually lives. It is not a copy
or a summary; it is the system of record. Examples:

| Authoritative source | What it owns |
| --- | --- |
| A cloud API | Live configuration state (segmentation, logging, allowlisting) |
| A learning-management system (LMS) | Training completion records |
| An HR system (HRIS) | Personnel screening and status |
| A document repository | Adopted policies, plans, and procedures |
| The engine's own run history | Evidence and outcomes from prior runs |

### Reference

A reference is a resolvable pointer into an authoritative source. It carries:

- a **URI** (where the referenced thing lives),
- a **freshness window** (`ce:freshnessDays` — how long the reference stays valid),
- a **last-verified timestamp** (`ce:lastVerified` — when it was last confirmed), and
- a named **custodian** (the person or role responsible for keeping it current).

Note: today, references resolve against local files and fixtures, not live systems.
Live resolvers are deferred work; see the honest-limits section at the end.

### Freshness policies

The freshness window says how stale a reference is allowed to be before it stops
counting. The policies and their day values are defined in
`src/compliance_engine/oracles/freshness.py`:

| Policy | Days (`ce:freshnessDays`) | Meaning |
| --- | --- | --- |
| annual | 365 | Valid for one year |
| semi-annual | 180 | Valid for six months |
| quarterly | 90 | Valid for three months |
| monthly | 30 | Valid for one month |
| event-based | 0 | Never expires on time alone; the record only needs to exist per event |

The `event-based` value of 0 is not "instantly stale." It means time alone never
expires the record — it is used for records that only need to exist for a given event
(for example, a record tied to a specific incident or a specific access grant).

### The four roles

A reference is only as good as the person who signs the attestation over it, and not
every signer is allowed to sign every control. There are four roles:

| Role | Owns / may attest |
| --- | --- |
| `Role_AffirmingOfficial` | May attest anything; carries the legal liability |
| `Role_SecurityOfficer` | Security-domain controls |
| `Role_ITAdmin` | IT administration controls |
| `Role_OPs` | Operations: personnel, maintenance, records |

The rule: a signer who is not the Affirming Official must match the module's required
role. The Affirming Official can attest regardless of the module's required role,
because the Affirming Official carries the legal liability for the whole submission.

### The attested-reference oracle: seven-step decision sequence

The attested-reference oracle
(`src/compliance_engine/oracles/attested_reference.py`) walks a fixed decision
sequence and **stops at the first failure**, returning a specific, machine-readable
reason. Only if every condition holds is the outcome `passed`.

| # | Condition checked | Outcome | Machine-readable reason |
| --- | --- | --- | --- |
| 1 | Reference not registered | `needsAction` | `reference-missing` |
| 2 | Reference has no URI | `failed` | `reference-unresolvable` |
| 3 | Reference never verified | `needsAction` | `reference-never-verified` |
| 4 | Reference past its freshness window | `failed` | e.g. `stale:172d>90d` |
| 5 | No attestation covers the control | `needsAction` | `awaiting-attestation` |
| 6 | Signer role is neither Affirming Official nor the required role | `failed` | e.g. `signer-role-mismatch:Role_ITAdmin!=Role_SecurityOfficer` |
| 7 | Attestation predates the reference's last verification | `failed` | `attestation-predates-reference` |

Two details worth stating plainly:

- Step 7 matters because an attestation must be *about* the current state of the
  reference. If someone signed before the reference was last verified, the signature
  cannot cover what the reference says now.
- If a signer's own declared outcome is a decline (`failed` or `needsAction`), that
  declined outcome is propagated, not overridden. The oracle does not upgrade a human's
  "no" into a "yes."

### Why the same check covers all 110 controls

This is the payoff. A control a machine can measure and a control only a human can
attest are checked by the *same* uniform sequence: is a reference registered, does it
resolve, is it within its freshness window, and is it signed by a human in the required
role? For a machine-measurable control the authoritative source is a cloud API; for a
policy-and-records control it is an HR system, an LMS, or a document repository. The
shape of the check does not change. That uniformity is exactly what lets the catalog
reach all 110 controls instead of only the ones a config-check can measure directly.

The split across the catalog:

- 65 controls machine-verified by the config-check oracle,
- 43 controls attested-reference,
- 2 controls CSP-inherited,
- 110 total, every one with a claiming module (39 modules in all).

---

## Oracle outcomes

An oracle can return one of three outcomes:

- **passed** — the check succeeded.
- **failed** — the check ran and the answer is no.
- **needsAction** — there is a concrete, actionable gap, and it *always* carries a
  reason.

Every required control resolves to one of these concrete outcomes. The value of
`needsAction` is that it names the specific next step — register a reference, refresh a
stale one, obtain a signature, or fix a role — rather than leaving the result vague.

That specificity is what turns the audit output into a work list. A run full of
`needsAction` outcomes is not a failure report; it is a to-do list, and every item
names the exact next action (from the reasons in the seven-step table above).

### Three oracle kinds

There are three kinds of oracle:

- **config-check** — for machine-measurable controls (the 65).
- **attested-reference** — a reference plus a signature (the model described above;
  the 43).
- **signed-artifact** — a detached signature over an artifact, used for signed
  documents.

---

## The contradiction guard (R13)

There is one situation the engine refuses to let hide: a human marks a control **met**
while the machine oracle for that control **failed or was absent**, and there is **no
written override justification**.

This is called a contradiction (referred to as R13 in the code comments; see the
contradiction dimension in `src/compliance_engine/traceability/audit.py`). It is a
legitimate thing for a human to do — a person can, with reason, override a machine —
but an *unexplained* human-over-machine call is exactly the kind of thing that should
never pass silently. So the engine surfaces contradictions **separately from the SPRS
score**, so they cannot be buried inside a passing number.

A written override justification clears the contradiction. The point is not to forbid
the override; it is to force it to be explained and visible.

You can see this behavior in the contradiction demo scenario ([05-try-it.md](05-try-it.md)),
where one control is attested met over a failed machine check and the audit reports:

```
Contradictions (attested MET over failed machine check): 1
```

The score itself still comes out `SPRS: score=110 status=Final valid_submission=True`,
which is precisely why the contradiction is reported on its own line — a clean score
does not mean there was nothing a reviewer needs to look at.

---

## Honest limits

To keep this chapter accurate rather than aspirational:

- Every run today is non-evidentiary: evidence is fixture-backed and the Terraform plan
  uses mock providers. Nothing here is a submittable government artifact.
- The engine records claims; it does not make an organization compliant. A false claim
  still passes here. The human signer carries the accountability, and an assessor
  (a C3PAO) catches it on reproduction ([04-the-proof.md](04-the-proof.md)).
- References are not resolved live yet; they resolve against local files and fixtures.
- Attestations are not cryptographically signed yet. Trust today is the Git history of
  the attestation file. Sigstore/cosign is scaffolded (a `sig_algo` field) but not
  wired.

---

## Summary

A machine can verify a fact; only a human can validate that a requirement is met, and
that human is legally accountable for the statement. The engine enforces this in its
data model — evidence `ce:addresses` a control, but only a human attestation
`ce:attests` it — so no amount of evidence can flip a control to met on its own. The
attested-reference model gives every control the same shape of check (a registered,
resolving, in-freshness reference signed by a human in the required role), which is why
coverage reaches all 110 controls and not just the machine-measurable ones. Every
required control resolves to a concrete outcome, and `needsAction` names an actionable
gap, turning the audit into a work list, and the contradiction guard makes
sure an unexplained human-over-machine "met" can never hide inside a passing score.

**Next:** [04-the-proof.md](04-the-proof.md) — the outputs (audit, SPRS, BOM, SSP) and
proof by reproduction.
