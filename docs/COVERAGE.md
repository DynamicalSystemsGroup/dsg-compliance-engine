## CMMC Level 2 — All 110 Controls Reference

**Status update (2026-07-03): the engine now claims every one of the 110 catalog controls.**

- **22** via the original tier-1 machine modules (Workspace 2SV, CMEK, IAM, DLP, org policy, audit-log export, service allowlist, TF baseline, monitoring, CSP-inherited physical).
- **45** via 13 new Track A machine modules (VPC segmentation, EDR, MDM, SCC, Workspace admin policy, BeyondCorp, GitHub branch protection, ops-MFA, Cloud Logging, BinAuth, session control, VPC-SC, IAM privileged use).
- **43** via 16 new Track B attested-reference (policy) modules — each pointing at an authoritative source (LMS, HRIS, DocRepo, EngineHistory) via `ce:Reference` and freshness-gated by `ce:oracle-attested-reference`.

Every control now has a claiming module. Machine-covered controls still emit config-check evidence; policy-covered controls emit `ce:AttestedReference` evidence with a fixture AO signature (`evidentiary_status="attested-reference-mock"`). NEEDS_ACTION is a first-class outcome for references that are missing / stale / awaiting attestation. The status table below still reflects the original tier-1 slice (Covered = tier-1 machine-checked); the new modules add the previous Machine and Human columns as attested-reference coverage on top.

**Legend:**

- **Covered** — machine-checked today via Terraform/oracle + attestation
- **Machine-possible** — no current evidence generator, but could be automated (cloud API, scanner, config check)
- **Human-only** — requires policy, procedure, training record, or physical inspection; the attested-reference oracle returns `passed` / `needsAction` / `failed`
- **CSP-inherited** — Google IL4 / your cloud provider handles this; you attest it as inherited
- **Non-deferrable** — cannot be put on a POA&M (six specific 1-pointers plus all 5-point controls by regulation)
- **Wt** = SPRS weight (points deducted if not MET; `110 − Σ weight` = your score)

---

### AC — Access Control (22 controls, up to 40 pts exposed)

| Control      | Wt  | Status | Plain-English Requirement                                                     |
| ------------ | --- | ------ | ----------------------------------------------------------------------------- |
| AC.L2-3.1.1  | 5   | Covered, No-POA&M | Only authorized users/devices/processes can access systems (IAM bindings)     |
| AC.L2-3.1.2  | 5   | Covered, No-POA&M | Users can only do the transactions/functions they're permitted (role scoping) |
| AC.L2-3.1.3  | 1   | Covered | CUI flows only on approved paths (data flow enforcement)                      |
| AC.L2-3.1.4  | 1   | Human | Separate duties so no single person can do something malicious alone          |
| AC.L2-3.1.5  | 3   | Covered, No-POA&M | Least privilege — accounts have only the access they need                     |
| AC.L2-3.1.6  | 1   | Machine | Use unprivileged accounts for non-security work (detectable via IAM)          |
| AC.L2-3.1.7  | 1   | Machine | Non-admins can't run privileged functions; log when they try                  |
| AC.L2-3.1.8  | 1   | Machine | Lock accounts after N failed login attempts                                   |
| AC.L2-3.1.9  | 1   | Human | Display a security/privacy notice at login (a banner or policy page)          |
| AC.L2-3.1.10 | 1   | Machine | Screen lock with pattern-hiding after inactivity                              |
| AC.L2-3.1.11 | 1   | Machine | Auto-terminate user sessions after a defined condition                        |
| AC.L2-3.1.12 | 5   | Machine, No-POA&M | Monitor and control every remote access session                               |
| AC.L2-3.1.13 | 5   | Machine, No-POA&M | Encrypt remote access sessions (TLS/VPN)                                      |
| AC.L2-3.1.14 | 1   | Machine | All remote access routes through managed access control points                |
| AC.L2-3.1.15 | 1   | Human | Authorize remote execution of privileged commands in writing                  |
| AC.L2-3.1.16 | 5   | Human, No-POA&M | Formally authorize every wireless connection before it's allowed              |
| AC.L2-3.1.17 | 5   | Machine, No-POA&M | Wireless uses authentication + encryption (WPA3/802.1X)                       |
| AC.L2-3.1.18 | 5   | Human, No-POA&M | Mobile device management policy + enforcement (MDM)                           |
| AC.L2-3.1.19 | 3   | Machine, No-POA&M | Encrypt CUI on mobile devices (MDM encryption-at-rest policy)                 |
| AC.L2-3.1.20 | 1   | Machine, No-POA&M | Verify and control/limit connections to external systems                      |
| AC.L2-3.1.21 | 1   | Human | Limit use of portable storage on external systems                             |
| AC.L2-3.1.22 | 1   | Human, No-POA&M | Control CUI posted on publicly accessible systems                             |

**Currently covered: 4 of 22.** The 18 uncovered AC controls include 5 that are 5-pt non-deferrable (remote access crypto, wireless, mobile). Those are high priority.

---

### AT — Awareness & Training (3 controls, up to 11 pts exposed)

| Control     | Wt  | Status | Plain-English Requirement                                         |
| ----------- | --- | ------ | ----------------------------------------------------------------- |
| AT.L2-3.2.1 | 5   | Human, No-POA&M | Everyone with system access gets security-risk awareness training |
| AT.L2-3.2.2 | 5   | Human, No-POA&M | People with security duties get role-specific training            |
| AT.L2-3.2.3 | 1   | Human | Insider threat awareness training for all personnel               |

**All three are human-only.** You need: a training program, completion records by person and date, curriculum that covers CMMC topics. No machine oracle can verify this.

---

### AU — Audit & Accountability (9 controls, up to 16 pts exposed)

| Control     | Wt  | Status | Plain-English Requirement                                           |
| ----------- | --- | ------ | ------------------------------------------------------------------- |
| AU.L2-3.3.1 | 5   | Covered, No-POA&M | Create and retain audit logs sufficient to reconstruct events       |
| AU.L2-3.3.2 | 3   | Covered, No-POA&M | Actions are traceable to individual users (no shared accounts)      |
| AU.L2-3.3.3 | 1   | Human | Review and update which events you log (defined log scope)          |
| AU.L2-3.3.4 | 1   | Machine | Alert when audit logging fails or is disabled                       |
| AU.L2-3.3.5 | 5   | Covered, No-POA&M | Correlate logs across systems for investigation (SIEM)              |
| AU.L2-3.3.6 | 1   | Human | Audit log reduction and report generation for on-demand analysis    |
| AU.L2-3.3.7 | 1   | Machine | Internal clocks synchronized to an authoritative time source (NTP)  |
| AU.L2-3.3.8 | 1   | Machine | Audit logs protected from unauthorized access/modification/deletion |
| AU.L2-3.3.9 | 1   | Machine | Only a subset of privileged users can manage audit logging itself   |

**Currently covered: 3 of 9.** AU.3, AU.4, AU.7, AU.8, AU.9 are all achievable via cloud config checks (Cloud Logging settings, IAM on log buckets, NTP config, alerting policies).

---

### CA — Security Assessment (4 controls, up to 14 pts exposed)

| Control      | Wt  | Status | Plain-English Requirement                                               |
| ------------ | --- | ------ | ----------------------------------------------------------------------- |
| CA.L2-3.12.1 | 5   | Human, No-POA&M | Periodically assess whether your security controls are actually working |
| CA.L2-3.12.2 | 3   | Human, No-POA&M | Develop and implement Plans of Action & Milestones (POA&M) for gaps     |
| CA.L2-3.12.3 | 5   | Human, No-POA&M | Ongoing monitoring of controls (not just annual assessments)            |
| CA.L2-3.12.4 | 1   | Human, No-POA&M | Write, document, and keep current a System Security Plan                |

**All four are human-only.** CA.12.4 is the SSP itself — this engine generates it, but a human must author the substance. CA.12.1/3 require a formal assessment program with documented results.

---

### CM — Configuration Management (9 controls, up to 24 pts exposed)

| Control     | Wt  | Status | Plain-English Requirement                                                      |
| ----------- | --- | ------ | ------------------------------------------------------------------------------ |
| CM.L2-3.4.1 | 5   | Covered, No-POA&M | Baseline configurations established and maintained (IaC)                       |
| CM.L2-3.4.2 | 5   | Covered, No-POA&M | Security configuration settings enforced across all IT products                |
| CM.L2-3.4.3 | 1   | Machine | Track, approve, and log all changes to systems                                 |
| CM.L2-3.4.4 | 1   | Human | Analyze security impact before implementing changes                            |
| CM.L2-3.4.5 | 5   | Machine, No-POA&M | Access restrictions enforced for making changes (branch protection, approvals) |
| CM.L2-3.4.6 | 5   | Covered, No-POA&M | Systems provide only essential capabilities (least functionality)              |
| CM.L2-3.4.7 | 5   | Covered, No-POA&M | Disable/remove nonessential programs, ports, protocols, services               |
| CM.L2-3.4.8 | 5   | Machine, No-POA&M | Software allowlisting: deny-all, permit-by-exception                           |
| CM.L2-3.4.9 | 1   | Human | Control and monitor user-installed software                                    |

**Currently covered: 4 of 9.** CM.4.3 (change log), CM.4.5 (change access controls), CM.4.8 (allowlisting) are all machine-checkable via cloud org policy and deployment pipeline config.

---

### IA — Identification & Authentication (11 controls, up to 22 pts exposed)

| Control      | Wt  | Status | Plain-English Requirement                                                 |
| ------------ | --- | ------ | ------------------------------------------------------------------------- |
| IA.L2-3.5.1  | 5   | Machine, No-POA&M | Identify all users, processes, and devices (directory / service accounts) |
| IA.L2-3.5.2  | 5   | Covered, No-POA&M | Authenticate every user/process/device before granting access             |
| IA.L2-3.5.3  | 5   | Covered, No-POA&M | MFA for all privileged accounts and non-privileged network access         |
| IA.L2-3.5.4  | 1   | Covered | Replay-resistant authentication (token, FIDO, certificate)                |
| IA.L2-3.5.5  | 1   | Machine | Prevent reuse of user IDs for a defined period                            |
| IA.L2-3.5.6  | 1   | Machine | Disable user IDs after a defined period of inactivity                     |
| IA.L2-3.5.7  | 1   | Machine | Enforce minimum password complexity requirements                          |
| IA.L2-3.5.8  | 1   | Machine | Prohibit password reuse for a specified number of generations             |
| IA.L2-3.5.9  | 1   | Machine | Temporary passwords must be changed at first login                        |
| IA.L2-3.5.10 | 5   | Machine, No-POA&M | Passwords stored and transmitted only in hashed/encrypted form            |
| IA.L2-3.5.11 | 1   | Human | Don't display passwords on screen while being entered                     |

**Currently covered: 3 of 11.** IA.5.1, IA.5.5–5.10 are all readable from Google Workspace / Cloud Identity policy API calls — high machine-coverage potential.

---

### IR — Incident Response (3 controls, up to 11 pts exposed)

| Control     | Wt  | Status | Plain-English Requirement                                                 |
| ----------- | --- | ------ | ------------------------------------------------------------------------- |
| IR.L2-3.6.1 | 5   | Human, No-POA&M | Have a documented, operational incident response capability (plan + team) |
| IR.L2-3.6.2 | 5   | Human, No-POA&M | Track, document, and report incidents to authorities (CISA, DIBNet)       |
| IR.L2-3.6.3 | 1   | Human | Test your incident response capability (tabletop or live drill)           |

**All three are human-only.** You need a written IR plan, documented roles, evidence of at least one exercise per year, and a reporting mechanism to US-CERT/CISA. No machine can verify these.

---

### MA — Maintenance (6 controls, up to 17 pts exposed)

| Control     | Wt  | Status | Plain-English Requirement                                            |
| ----------- | --- | ------ | -------------------------------------------------------------------- |
| MA.L2-3.7.1 | 3   | Human, No-POA&M | Perform system maintenance on schedule with documented procedures    |
| MA.L2-3.7.2 | 5   | Human, No-POA&M | Control who does maintenance and with what tools (approved list)     |
| MA.L2-3.7.3 | 1   | Human | Sanitize equipment of CUI before sending it off-site for maintenance |
| MA.L2-3.7.4 | 3   | Human, No-POA&M | Scan diagnostic media for malware before using on systems            |
| MA.L2-3.7.5 | 5   | Machine, No-POA&M | MFA required for remote/nonlocal maintenance sessions                |
| MA.L2-3.7.6 | 1   | Human | Supervise maintenance personnel who lack access authorization        |

**One machine-possible (MA.7.5 — MFA for remote maintenance, verifiable via IAM policy). Five are human-only** — they require maintenance logs, approved vendor lists, and documented procedures.

---

### MP — Media Protection (9 controls, up to 22 pts exposed)

| Control     | Wt  | Status | Plain-English Requirement                                                        |
| ----------- | --- | ------ | -------------------------------------------------------------------------------- |
| MP.L2-3.8.1 | 3   | Human, No-POA&M | Physically control and securely store all media (paper + digital) containing CUI |
| MP.L2-3.8.2 | 3   | Human, No-POA&M | Limit who can access CUI on media to authorized people only                      |
| MP.L2-3.8.3 | 5   | Human, No-POA&M | Sanitize or destroy media before disposal or reuse                               |
| MP.L2-3.8.4 | 1   | Human | Mark media with required CUI labels and distribution limits                      |
| MP.L2-3.8.5 | 1   | Human | Control media transport and maintain accountability chain                        |
| MP.L2-3.8.6 | 1   | Human | Encrypt CUI on portable media in transit                                         |
| MP.L2-3.8.7 | 5   | Machine, No-POA&M | Control use of removable media on systems (block USB if not authorized)          |
| MP.L2-3.8.8 | 3   | Human, No-POA&M | Prohibit portable storage with no identifiable owner                             |
| MP.L2-3.8.9 | 1   | Human | Protect confidentiality of backup CUI at storage locations                       |

**One machine-possible (MP.8.7 — USB/removable media blocking, enforceable via OS policy or MDM). Eight are human-only** — physical media handling is inherently procedural.

---

### PE — Physical & Environmental Protection (6 controls, up to 13 pts exposed)

| Control      | Wt  | Status   | Plain-English Requirement                                       |
| ------------ | --- | -------- | --------------------------------------------------------------- |
| PE.L2-3.10.1 | 5   | Covered, CSP, No-POA&M | Limit physical access to systems/equipment to authorized people |
| PE.L2-3.10.2 | 5   | Covered, CSP, No-POA&M | Protect and monitor the physical facility and infrastructure    |
| PE.L2-3.10.3 | 1   | Human, No-POA&M | Escort visitors and monitor visitor activity                    |
| PE.L2-3.10.4 | 1   | Human, No-POA&M | Maintain physical access logs                                   |
| PE.L2-3.10.5 | 1   | Human, No-POA&M | Control and manage physical access devices (badges, keys, fobs) |
| PE.L2-3.10.6 | 1   | Human | Safeguard CUI at alternate work sites (home offices, etc.)      |

**PE.1 and PE.2 are covered and CSP-inherited** — Google IL4 datacenters handle physical security, and you attest this as inherited. **The other four apply to your own offices** — visitor logs, badge access systems, key management. PE.6 (remote work) is a policy document.

---

### PS — Personnel Security (2 controls, up to 8 pts exposed)

| Control     | Wt  | Status | Plain-English Requirement                                                          |
| ----------- | --- | ------ | ---------------------------------------------------------------------------------- |
| PS.L2-3.9.1 | 3   | Human, No-POA&M | Background screen individuals before granting CUI system access                    |
| PS.L2-3.9.2 | 5   | Human, No-POA&M | Protect systems when employees are terminated or transferred (revoke access, etc.) |

**Both are human-only.** You need documented screening procedures and evidence of offboarding checklists. PS.9.2 is a 5-pointer non-deferrable — a terminated employee with live credentials is a serious gap.

---

### RA — Risk Assessment (3 controls, up to 9 pts exposed)

| Control      | Wt  | Status | Plain-English Requirement                                       |
| ------------ | --- | ------ | --------------------------------------------------------------- |
| RA.L2-3.11.1 | 3   | Human, No-POA&M | Periodically assess risk to operations, assets, and people      |
| RA.L2-3.11.2 | 5   | Machine, No-POA&M | Scan for vulnerabilities periodically and after new discoveries |
| RA.L2-3.11.3 | 1   | Human | Remediate vulnerabilities per your risk assessment              |

**RA.11.2 is machine-possible** — vulnerability scanners (Tenable, Qualys, Google's Security Command Center) produce machine-readable output that could feed an evidence generator. The other two require documented risk assessments and remediation tracking.

---

### SC — System & Communications Protection (16 controls, up to 41 pts exposed)

| Control       | Wt  | Status | Plain-English Requirement                                                   |
| ------------- | --- | ------ | --------------------------------------------------------------------------- |
| SC.L2-3.13.1  | 5   | Covered, No-POA&M | Monitor and protect communications at external boundaries                   |
| SC.L2-3.13.2  | 5   | Human, No-POA&M | Use security engineering principles in system design                        |
| SC.L2-3.13.3  | 1   | Machine | Separate user-facing from system management functionality                   |
| SC.L2-3.13.4  | 1   | Machine | Prevent info leakage via shared system resources                            |
| SC.L2-3.13.5  | 5   | Machine, No-POA&M | Network segmentation — DMZ for public components, isolated internals        |
| SC.L2-3.13.6  | 5   | Machine, No-POA&M | Default deny on network traffic (deny-all, permit-by-exception)             |
| SC.L2-3.13.7  | 1   | Machine | Prevent split tunneling on remote connections                               |
| SC.L2-3.13.8  | 3   | Machine, No-POA&M | Encrypt CUI in transit (TLS 1.2+ on all connections)                        |
| SC.L2-3.13.9  | 1   | Machine | Terminate network sessions after defined idle period                        |
| SC.L2-3.13.10 | 1   | Covered | Manage cryptographic keys for all crypto employed                           |
| SC.L2-3.13.11 | 5   | Covered, No-POA&M | FIPS-validated cryptography for CUI protection                              |
| SC.L2-3.13.12 | 1   | Human | Disable collaborative computing device remote activation (cameras/mics)     |
| SC.L2-3.13.13 | 1   | Human | Control and monitor mobile code (JavaScript, ActiveX, etc.)                 |
| SC.L2-3.13.14 | 1   | Human | Control and monitor VoIP usage                                              |
| SC.L2-3.13.15 | 5   | Machine, No-POA&M | Protect authenticity of communications sessions (TLS certs, session tokens) |
| SC.L2-3.13.16 | 1   | Covered | Encrypt CUI at rest                                                         |

**Currently covered: 4 of 16.** SC is the richest opportunity for machine coverage — SC.13.5, 13.6, 13.8, 13.15 can all be verified from Terraform VPC/firewall config. That's another ~19 pts of 5-pt non-deferrables that could be automated.

---

### SI — System & Information Integrity (7 controls, up to 30 pts exposed)

| Control      | Wt  | Status | Plain-English Requirement                                       |
| ------------ | --- | ------ | --------------------------------------------------------------- |
| SI.L2-3.14.1 | 5   | Machine, No-POA&M | Identify and patch system flaws in a timely manner              |
| SI.L2-3.14.2 | 5   | Machine, No-POA&M | Malware protection at designated locations (endpoint AV/EDR)    |
| SI.L2-3.14.3 | 5   | Covered, No-POA&M | Monitor security alerts and act on them                         |
| SI.L2-3.14.4 | 5   | Machine, No-POA&M | Update malware protection when new signatures are available     |
| SI.L2-3.14.5 | 3   | Machine, No-POA&M | Periodic and real-time scans for malware                        |
| SI.L2-3.14.6 | 5   | Covered, No-POA&M | Monitor inbound/outbound traffic for attacks and indicators     |
| SI.L2-3.14.7 | 3   | Machine, No-POA&M | Identify unauthorized use of systems (anomaly detection / UEBA) |

**Currently covered: 2 of 7.** The other five are all machine-possible via endpoint management APIs, patch status endpoints, or SIEM queries — SI is one of the highest-return areas to automate next.

---

## Summary Scorecard

| Family    | Controls | Currently Covered | Machine-Possible | Human-Only | Max pts at risk |
| --------- | -------- | :---------------: | :--------------: | :--------: | :-------------: |
| AC        | 22       |         4         |        12        |     6      |       40        |
| AT        | 3        |         0         |        0         |     3      |       11        |
| AU        | 9        |         3         |        5         |     1      |       16        |
| CA        | 4        |         0         |        0         |     4      |       14        |
| CM        | 9        |         4         |        3         |     2      |       24        |
| IA        | 11       |         3         |        7         |     1      |       22        |
| IR        | 3        |         0         |        0         |     3      |       11        |
| MA        | 6        |         0         |        1         |     5      |       17        |
| MP        | 9        |         0         |        1         |     8      |       22        |
| PE        | 6        |       2 CSP |        0         |     4      |       13        |
| PS        | 2        |         0         |        0         |     2      |        8        |
| RA        | 3        |         0         |        1         |     2      |        9        |
| SC        | 16       |         4         |        9         |     3      |       41        |
| SI        | 7        |         2         |        5         |     0      |       30        |
| **Total** | **110**  |      **22**       |      **44**      |   **44**   |     **278**     |

The 278 is not the score — it's the total _points available to lose_ if everything were uncovered. Your current SPRS floor from the 22 covered controls is already strong for the controls you do have evidence on. But **44 more controls could be machine-covered with additional evidence generators**, and **44 require documented human attestations**. The human-only 44 are the ones you need to build policy and procedure for before a self-assessment.

**The highest-priority gaps** (5-pt non-deferrable, not yet covered): PS.9.2 (termination), AT.2.1/2.2 (training), IR.6.1/6.2 (incident response), SC.13.2/13.5/13.6/13.15 (network security engineering), SI.14.1/14.2 (patching/malware), CM.4.5/4.8 (change controls/allowlisting). These alone represent **60+ points** of SPRS exposure.
