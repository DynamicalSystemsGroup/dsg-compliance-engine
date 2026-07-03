# What We Need To Do To Submit Our CMMC Level 2 Score

This is the list of non-engineering work required to reach a submitted, affirmed
CMMC Level 2 self-assessment score in the government's SPRS system. The engineering
team handles the systems configuration separately; this document covers policies,
records, training, decisions, and the submission itself.

This is time-sensitive. CMMC is now in effect and is being written into contracts.
As of mid-2026 we are in the first rollout phase, where most contracts that involve
Controlled Unclassified Information (CUI) require at least a Level 2 self-assessment
score posted in SPRS as a condition of award. The next phase (Phase 2) begins
November 10, 2026, after which many Level 2 contracts require an independent third-party assessment
instead of a self-assessment, and some contracts already require that now at the
contracting officer's discretion.

---

## How this actually works

- We assess ourselves against the 110 security requirements of NIST SP 800-171
  (broken into roughly 320 detailed check items). Each item is either met or not met.
  A requirement only counts as met if every one of its check items passes.
- We calculate a score by starting at 110 and subtracting points for each requirement we
  have not met (a 1-, 3-, or 5-point deduction depending on the requirement); the score can
  fall below zero. We record the score, along with our System Security Plan, in SPRS (the
  government's Supplier Performance Risk System).
- A senior company official, the Affirming Official, signs a statement in SPRS that we
  meet the requirements. This is required at submission and every year after that. A
  full reassessment is required every three years.
- Whether we may self-assess or must use an independent assessor (a C3PAO) is set by
  the specific contract, not by us. Even where a C3PAO is required, the same policies,
  records, System Security Plan, and score are the input to that assessment. A third-party
  certification also satisfies any self-assessment requirement, but a self-assessment cannot
  substitute for a required certification.
- The Affirming Official's signature is a formal statement to the government. A false
  or careless one carries False Claims Act liability for the company and potentially
  the signer personally. We sign only what is true and supported.

---

## Decisions and prerequisites to resolve first

These gate the rest of the work. Resolve each one before or alongside the paperwork.

1. **Self-assessment or third-party (C3PAO).** Check the CMMC line in each relevant
   contract (DFARS clause 252.204-7021). Self-assessment is only allowed for
   lower-sensitivity ("non-prioritized") contracts; higher-sensitivity CUI requires a
   C3PAO. Confirm which applies per contract with the contracting officer or prime.
   Do not assume self-assessment is available.

2. **Which environment holds CUI: current Google Workspace or Assured Workloads (IL4).**
   Any cloud that stores, processes, or transmits CUI must meet FedRAMP Moderate-equivalent
   security; Assured Workloads / IL4 is how we meet that. A run against our current
   Workspace is a rehearsal that tells us where we stand — the submittable, evidentiary
   environment is Assured Workloads. Decide the upgrade timing, and do not collect "real"
   evidence in the throwaway environment.

3. **Physical office or fully remote.** The physical-access requirements (visitor log,
   badge issuance, escorts) assume a company facility. A fully remote team scopes these
   to home-office safeguards and a signed remote-work agreement per person instead.
   Confirm the scoping with the assessor rather than assuming it away — three of these
   controls are among the items that can never be deferred (see the rules below).

4. **Endpoint detection (EDR).** The malware and endpoint-integrity requirements assume a
   real EDR tool (CrowdStrike, SentinelOne, or equivalent) on every machine with access,
   reporting sensor status and current definitions. If none is deployed, deploy and enroll
   before claiming those controls.

5. **Mobile device management (MDM).** The mobile-device and removable-media requirements
   assume managed devices that enforce disk encryption and block USB storage for CUI.
   Choose the tool and enroll devices.

6. **Training platform.** We need a system that records completion by name, date, and score
   for everyone with access. Choose the platform. A shared document of "who watched a video"
   is not sufficient evidence.

7. **Background-check vendor and scope.** Decide who runs screening, what scope, and how
   often, and keep a per-person confirmation.

8. **Vulnerability scanning.** The vulnerability-management requirements assume a scanner
   producing dated findings against the CUI environment. Confirm one is running.

9. **Remote access path.** Requirements assume remote sessions run through a managed,
   encrypted path (zero-trust or a TLS VPN, no split tunnel). Confirm how people connect.

10. **Incident-reporting registration (set up in advance).** If a cyber incident occurs we
    must report it to the DoD within 72 hours. That requires registration done ahead of
    time: PIEE credentials (free, the DoD-preferred method) or a DoD-approved medium
    assurance certificate (about a week of lead time, notarized paperwork). You cannot start
    this after an incident and still meet the 72-hour clock. Register now and confirm we can
    reach the current DoD incident-reporting portal.

11. **Media sanitization capability.** We need a defined process to wipe or destroy storage
    and media (per NIST SP 800-88) and at least one actual sanitization record. A written
    policy alone does not satisfy this.

---

## The rules that cannot be bent

- A "Conditional" pass (leftover gaps carried on a corrective-action plan, a POA&M) requires
  two things together: a score of at least 88 of 110 (80 percent), and every open item being
  eligible for a POA&M. A score of 88 is not enough on its own if any ineligible item is still
  open (see the never-defer list below). Below 88 we cannot submit a passing status at all.
- Only minor (1-point) gaps may be deferred onto a POA&M. Anything more significant must be
  actually done before we submit. In practice, assume everything on this list must be
  genuinely completed.
- Six things can never be deferred under any circumstances: our System Security Plan; the
  control over connections to outside systems; the rule against putting CUI on public-facing
  systems; and the three physical-access controls (escorting visitors, keeping physical
  access logs, and managing physical access).
- Encryption of CUI is the one narrow exception that may be deferred, and only if we already
  encrypt CUI but have not yet completed FIPS validation.
- If we submit a "Conditional" score with a POA&M, we have 180 days to finish every item and
  pass a follow-up check, or the status expires and we lose eligibility.
- A former employee with active access will fail the personnel requirement regardless of
  what the policy says. Offboarding must actually revoke access within 24 hours of separation.

---

## The work, in order

### Stage 1 — Confirm scope and the up-front decisions

- [ ] **Confirm what CUI we handle and which systems are in scope.**
  - Owner: [assign]
  - When: [date]
  - Done when: we have a written statement of the CUI we handle and the systems that touch it.

- [ ] **Resolve the decisions in the section above (self vs C3PAO, environment, remote scoping, tools, registrations).**
  - Owner: [assign]
  - When: [date]
  - Done when: each of the eleven prerequisites has a decision or an owner and a date.

### Stage 2 — Write and sign the policies

Use the detailed list in "The policies to write" below. For each policy: replace the
placeholder draft with text that matches how we actually operate, then sign and date it.

- [ ] **Read the placeholder drafts and confirm the final set of policies we will adopt.**
  - Owner: [assign]
  - When: [date]
  - Done when: we have agreed on the list and who writes each.

- [ ] **Rewrite each policy to describe our real practice, then sign it.**
  - Owner: [assign per policy]
  - When: [date]
  - Done when: every policy in the list is signed, dated, and saved in the shared folder.

### Stage 3 — Train the team

- [ ] **Enroll everyone with access in the security awareness training and confirm completion.**
  - Owner: [assign]
  - When: [date]
  - Training link: [paste the training link here]
  - Done when: every person with access has a completion record (name, date, score).

### Stage 4 — People and access

- [ ] **Decide who is granted access and record why.**
  - Owner: [assign]
  - When: [date]
  - Done when: a written access list exists.

- [ ] **Complete screening for each person with access.**
  - Owner: [assign]
  - When: [date]
  - Done when: a screening confirmation exists per person.

- [ ] **Confirm the offboarding checklist is in use and revokes access within 24 hours.**
  - Owner: [assign]
  - When: [date]
  - Done when: the checklist exists and any past departures show access was revoked in time.

### Stage 5 — Run the incident-response drill

- [ ] **Run the incident-response tabletop.**
  - Owner: [assign]
  - When: [date]
  - Done when: the drill happened and people took part.

- [ ] **Write up the drill.**
  - Owner: [assign]
  - When: [date]
  - Done when: a short written report is saved in the shared folder.

### Stage 6 — Mark and handle CUI correctly

- [ ] **Adopt the CUI marking rules and apply them.**
  - Owner: [assign]
  - When: [date]
  - Done when: CUI is marked using approved banner markings from the CUI Registry (no legacy
    labels such as "FOUO"), and people know how to mark and handle it.

### Stage 7 — Gather the evidence into one folder

- [ ] **Collect everything into the shared compliance folder.**
  - Owner: [assign]
  - When: [date]
  - Done when the folder contains: every signed policy; the System Security Plan; the training
    completion records; the screening confirmations; the written access list; the onboarding
    and offboarding checklists; the tabletop report; and any monitoring or scan outputs.

### Stage 8 — Assess, score, and handle any gaps

- [ ] **Assess ourselves against all 110 requirements and calculate the score.**
  - Owner: [assign]
  - When: [date]
  - Done when: each requirement is marked met or not met and a score out of 110 is produced.

- [ ] **For any gaps, decide fix-now versus POA&M, respecting the rules above.**
  - Owner: [Affirming Official] with [ops lead]
  - When: [date]
  - Done when: the score is at least 88, every deferred item is eligible for a POA&M, and
    nothing on the never-defer list is open.

### Stage 9 — Submit in SPRS and affirm

- [ ] **Post the score and System Security Plan details in SPRS.**
  - Owner: [assign]
  - When: [date]
  - Done when: the score, assessment date, scope, CAGE code, and System Security Plan
    information are entered. (Requires SAM registration with a CAGE code, PIEE registration,
    and an approved SPRS Cyber Vendor role.)

- [ ] **The Affirming Official submits the affirmation in SPRS.**
  - Owner: [Affirming Official]
  - When: [date]
  - Done when: the affirmation is submitted and we have confirmation.

### Stage 10 — Maintain it

- [ ] **Submit the affirmation every year, and keep the score current.**
  - Owner: [Affirming Official]
  - When: annually
  - Done when: an affirmation is on file for the current year and the assessment is under three years old.

- [ ] **Stay ready to report a cyber incident within 72 hours.**
  - Owner: [assign]
  - When: ongoing
  - Done when: our registration works, the incident-response plan names the reporting steps,
    and we know to preserve forensic data for 90 days.

- [ ] **Flow the requirements down to any subcontractors that handle CUI, and reassess every three years.**
  - Owner: [assign]
  - When: ongoing
  - Done when: subcontracts include the required clauses and a reassessment is scheduled.

---

## The policies to write

For each policy: replace the placeholder with text describing our real practice, list the
evidence we will keep, and consider it done only when the evidence exists — not when the
document is merely written.

### 1. System description (System Security Plan)
Cannot be deferred. This is the root document; the others reference it.
- What to write: a description of our systems and the CUI in them — which systems handle CUI,
  how data flows in and out, who the authorized users are, the roles, the physical and
  remote-work environment, and any connections to outside systems.
- Evidence to keep: the written system description, kept current.
- Done when: it is complete, accurate, and signed.

### 2. Security awareness training
- What to write: an annual program covering CUI handling, phishing, insider threat, password
  practices, and mobile-device rules, plus role-specific training for ops and engineering
  (incident-response roles, key handling, secure change procedures).
- Evidence to keep: completion records (name, date, score) for everyone with access.
- Done when: the program is written and every person with access has a current completion record.

### 3. Incident response plan
Contains high-weight requirements that must be met, not deferred.
- What to write: who does what during an incident (incident commander, security officer), how
  we detect and escalate, the requirement to report a cyber incident to the DoD within 72 hours,
  and a schedule for an annual practice drill.
- Evidence to keep: the signed plan plus at least one completed tabletop drill report.
- Done when: the plan is signed and one drill has been run and written up.

### 4. Risk assessment
- What to write: our assets, the threats to them, how likely and how damaging each is, and our
  decision on each (accept, fix, or transfer), plus a tracker of findings with target dates.
- Evidence to keep: the dated, signed assessment and the findings log.
- Done when: the assessment is complete and signed and the findings log is current.

### 5. Personnel security
Contains a high-weight requirement that must be met. A former employee with active access fails this.
- What to write: when and how we screen people before access, and an offboarding checklist that
  revokes accounts, rotates credentials, recovers equipment, and returns access devices within
  24 hours of someone leaving.
- Evidence to keep: a screening confirmation per person and completed offboarding checklists for
  anyone who left.
- Done when: screening records exist for everyone with access and no former employee has active access.

### 6. Configuration management
- What to write: a procedure to review the security impact of a change before making it, and a
  process to approve user-installed software.
- Evidence to keep: the procedure and the change-log entries.
- Done when: the procedure is written and changes are being logged.

### 7. Maintenance
Contains a high-weight requirement that must be met.
- What to write: who is approved to perform maintenance and with what tools, how CUI is removed
  before equipment goes off-site, how diagnostic media is scanned, and escort rules for maintenance.
- Evidence to keep: the signed approved-vendor list and maintenance log entries.
- Done when: the list and procedures are signed and maintenance events are logged.

### 8. Media protection
- What to write: how we label CUI media, how we store and control access to it, how we sanitize or
  destroy it (per NIST SP 800-88), and a prohibition on unapproved portable storage.
- Evidence to keep: a media inventory and at least one sanitization or destruction record.
- Done when: the policy is written and at least one sanitization record exists.

### 9. Audit and log review
- What to write: which events we log (logins, use of privileges, changes, data access), and who
  reviews the logs and how often.
- Evidence to keep: the procedure and a sample log-review report.
- Done when: the procedure is written and a first review has been done.

### 10. Security engineering principles
Contains a high-weight requirement that must be met.
- What to write: the security design rules we follow — least privilege, layered defenses,
  fail-secure defaults, separation of duties, and minimizing what is exposed.
- Evidence to keep: a signed architecture or design review document.
- Done when: the document is written and signed.

### 11. Remote access authorization
The rule against putting CUI on public systems cannot be deferred.
- What to write: written authorization for running privileged commands remotely, a rule against
  portable storage on outside systems, and confirmation that no CUI is placed on public-facing systems.
- Evidence to keep: the policy, kept as an appendix to the system description.
- Done when: it is written, signed, and confirmed.

### 12. Physical and remote-work access
Three of these controls can never be deferred; a fully remote team should confirm scoping with the assessor.
- What to write: visitor escort and log rules, how access devices are issued and revoked, and
  home-office safeguards with a signed remote-work agreement per person.
- Evidence to keep: visitor and badge logs where applicable, and a remote-work agreement per person.
- Done when: the rules are written and the per-person agreements are signed.

### 13. Collaborative computing
- What to write: rules for cameras and microphones in spaces where CUI is discussed, what code is
  allowed to run, and voice and video call usage rules.
- Evidence to keep: the policy and device settings showing enforcement.
- Done when: it is written and enforced.

### 14. Separation of duties
- What to write: role definitions showing no single person can both approve and carry out a
  sensitive change, referencing the required-reviewer setup as the technical enforcement.
- Evidence to keep: a role and responsibility matrix.
- Done when: it is written and signed.

### 15. Ongoing monitoring
Contains high-weight requirements that must be met.
- What to write: what we monitor, how often, and who reviews it; the schedule for our yearly
  self-assessment; and the process for handling any gaps.
- Evidence to keep: the monitoring plan, the assessment outputs, and any open POA&M items.
- Done when: the plan is written and a monitoring cadence is running.

### 16. Login banner
- What to write: the exact warning notice shown when someone signs in to a CUI system (government
  interest, consent to monitoring, no expectation of privacy).
- Evidence to keep: the policy and confirmation the banner appears at sign-in.
- Done when: it is written and the banner is live.

---

## Owners (fill in)

- Affirming Official (signs and submits): [name]
- Policies lead: [name]
- People and access / HR: [name]
- Training coordinator: [name]
- Tabletop organizer: [name]
- Records and folder owner: [name]
- SPRS / PIEE submitter: [name]

## Target dates (fill in)

- Up-front decisions resolved by: [date]
- Policies signed by: [date]
- Training complete by: [date]
- Tabletop drill by: [date]
- Everything in the folder by: [date]
- Score submitted and affirmed by: [date]
