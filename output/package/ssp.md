<!-- AUTO-GENERATED ARTIFACT - DO NOT EDIT.
     Deterministic view compiled from the RDF dataset by documents/ssp.py.
     Edit the dataset (re-run the pipeline), then rebuild:
       uv run python -m documents.ssp build --input <dataset.trig> -->

# SSP-NV012 — NV012 System Security Plan + Traceability Matrix (Document 2)

> **NON-EVIDENTIARY — fixture-derived / auto-attested.**
> Evidentiary status present: mock. This is a demonstration artifact, **not a submittable SSP**.

## 1. System identification and CUI boundary

| Field | Value |
| --- | --- |
| Document ID | SSP-NV012 |
| System | NV012 Tier 1 IL4 CUI enclave |
| CUI boundary | Google Workspace Enterprise Plus + GCP Assured Workloads (IL4) |
| Dataset | output/engine.trig |
| Dataset SHA-256 | 111fee7ccbee578ed03503b6d700682238ccbef4d218f3ac686d833b028bd9e6 |
| Quad count | 5687 |
| Document date | 2026-07-04T20:35:19.673721+00:00 |
| Evidentiary status | NON-EVIDENTIARY (mock) |
| Compiler | documents/ssp.py |

## 2. Framework applicability

Scope: NIST SP 800-171 Rev. 2 / CMMC Level 2 (110 controls). Status is the
recorded human attestation (EARL outcome via `STATUS_LABEL`); evidence
*addresses* controls but never *attests* them. The machine-checkable subset
is verified by oracles; the remainder is human-attested from documentary
evidence.

## 3. Verification Cross-Reference Matrix (VCRM) — Document 2

One row per control (all 110). Status is the attestation outcome; a control
with no attestation is PLANNED (a gap).

| Control | Implementation | Responsible party | Evidence location | Evidence hash | Status | Gap notes | POA&M ref |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC.L2-3.1.1 | IAM groups + least-privilege role bindings for CUI access | NV012 Affirming Official | nv012/all-covered/gcp_iam_bindings.json | 4bba2d0adcbb, 6c69bdddaea3 | MET | - | - |
| AC.L2-3.1.10 | Cloud Identity session control + failed-login lockout | NV012 Affirming Official | nv012/all-covered/gcp_session_control.json | 8959f24468b8 | MET | - | - |
| AC.L2-3.1.11 | Cloud Identity session control + failed-login lockout | NV012 Affirming Official | nv012/all-covered/gcp_session_control.json | 8959f24468b8 | MET | - | - |
| AC.L2-3.1.12 | BeyondCorp Enterprise remote access + TLS enforcement | NV012 Affirming Official | nv012/all-covered/beyondcorp_remote.json | 753946a895a2 | MET | - | - |
| AC.L2-3.1.13 | BeyondCorp Enterprise remote access + TLS enforcement | NV012 Affirming Official | nv012/all-covered/beyondcorp_remote.json | 753946a895a2 | MET | - | - |
| AC.L2-3.1.14 | BeyondCorp Enterprise remote access + TLS enforcement | NV012 Affirming Official | nv012/all-covered/beyondcorp_remote.json | 753946a895a2 | MET | - | - |
| AC.L2-3.1.15 | Remote access authorization (SSP appendix) | NV012 Affirming Official | - | - | MET | - | - |
| AC.L2-3.1.16 | Chrome Cloud Management + Endpoint Verification (MDM) | NV012 Affirming Official | nv012/all-covered/chrome_mdm.json | df6706e07d44 | MET | - | - |
| AC.L2-3.1.17 | Chrome Cloud Management + Endpoint Verification (MDM) | NV012 Affirming Official | nv012/all-covered/chrome_mdm.json | df6706e07d44 | MET | - | - |
| AC.L2-3.1.18 | Chrome Cloud Management + Endpoint Verification (MDM) | NV012 Affirming Official | nv012/all-covered/chrome_mdm.json | df6706e07d44 | MET | - | - |
| AC.L2-3.1.19 | Chrome Cloud Management + Endpoint Verification (MDM) | NV012 Affirming Official | nv012/all-covered/chrome_mdm.json | df6706e07d44 | MET | - | - |
| AC.L2-3.1.2 | IAM groups + least-privilege role bindings for CUI access | NV012 Affirming Official | - | - | MET | - | - |
| AC.L2-3.1.20 | VPC Service Controls perimeter — external system authorization | NV012 Affirming Official | nv012/all-covered/gcp_vpc_service_controls.json | b6c67e930e8a | MET | - | - |
| AC.L2-3.1.21 | Remote access authorization (SSP appendix) | NV012 Affirming Official | - | - | MET | - | - |
| AC.L2-3.1.22 | Remote access authorization (SSP appendix) | NV012 Affirming Official | - | - | MET | - | - |
| AC.L2-3.1.3 | Drive + Gmail DLP rules (control the flow of CUI) | NV012 Affirming Official | - | - | MET | - | - |
| AC.L2-3.1.4 | Separation of duties (RACI matrix) | NV012 Affirming Official | - | - | MET | - | - |
| AC.L2-3.1.5 | IAM groups + least-privilege role bindings for CUI access | NV012 Affirming Official | - | - | MET | - | - |
| AC.L2-3.1.6 | GCP IAM policy + audit-log signals for privileged use | NV012 Affirming Official | nv012/all-covered/gcp_iam_privileged.json | 594252df359f | MET | - | - |
| AC.L2-3.1.7 | GCP IAM policy + audit-log signals for privileged use | NV012 Affirming Official | nv012/all-covered/gcp_iam_privileged.json | 594252df359f | MET | - | - |
| AC.L2-3.1.8 | Cloud Identity session control + failed-login lockout | NV012 Affirming Official | nv012/all-covered/gcp_session_control.json | 8959f24468b8 | MET | - | - |
| AC.L2-3.1.9 | Login banner policy (system-use notification) | NV012 Affirming Official | - | - | MET | - | - |
| AT.L2-3.2.1 | Annual security awareness + role-based training program | NV012 Affirming Official | - | - | MET | - | - |
| AT.L2-3.2.2 | Annual security awareness + role-based training program | NV012 Affirming Official | - | - | MET | - | - |
| AT.L2-3.2.3 | Annual security awareness + role-based training program | NV012 Affirming Official | - | - | MET | - | - |
| AU.L2-3.3.1 | Workspace + GCP audit log export to retained Cloud Storage bucket | NV012 Affirming Official | - | - | MET | - | - |
| AU.L2-3.3.2 | Workspace + GCP audit log export to retained Cloud Storage bucket | NV012 Affirming Official | - | - | MET | - | - |
| AU.L2-3.3.3 | Audit management procedure (log review cadence + reports) | NV012 Affirming Official | - | - | MET | - | - |
| AU.L2-3.3.4 | Cloud Logging sinks + NTP + IAM on log buckets | NV012 Affirming Official | nv012/all-covered/gcp_cloud_logging.json | dbbec2757568 | MET | - | - |
| AU.L2-3.3.5 | Workspace + GCP audit log export to retained Cloud Storage bucket | NV012 Affirming Official | - | - | MET | - | - |
| AU.L2-3.3.6 | Audit management procedure (log review cadence + reports) | NV012 Affirming Official | - | - | MET | - | - |
| AU.L2-3.3.7 | Cloud Logging sinks + NTP + IAM on log buckets | NV012 Affirming Official | nv012/all-covered/gcp_cloud_logging.json | dbbec2757568 | MET | - | - |
| AU.L2-3.3.8 | Cloud Logging sinks + NTP + IAM on log buckets | NV012 Affirming Official | nv012/all-covered/gcp_cloud_logging.json | dbbec2757568 | MET | - | - |
| AU.L2-3.3.9 | Cloud Logging sinks + NTP + IAM on log buckets | NV012 Affirming Official | nv012/all-covered/gcp_cloud_logging.json | dbbec2757568 | MET | - | - |
| CA.L2-3.12.1 | Continuous monitoring: engine run history + POA&M tracker | NV012 Affirming Official | - | - | MET | - | - |
| CA.L2-3.12.2 | Continuous monitoring: engine run history + POA&M tracker | NV012 Affirming Official | - | - | MET | - | - |
| CA.L2-3.12.3 | Continuous monitoring: engine run history + POA&M tracker | NV012 Affirming Official | - | - | MET | - | - |
| CA.L2-3.12.4 | System Security Plan supplement (system description) | NV012 Affirming Official | - | - | MET | - | - |
| CM.L2-3.4.1 | Terraform baseline configuration + resource inventory (IaC) | NV012 Affirming Official | - | - | MET | - | - |
| CM.L2-3.4.2 | Terraform baseline configuration + resource inventory (IaC) | NV012 Affirming Official | - | - | MET | - | - |
| CM.L2-3.4.3 | GitHub branch protection + required reviews | NV012 Affirming Official | nv012/all-covered/github_branch_protection.json | a911dd6a6276 | MET | - | - |
| CM.L2-3.4.4 | Configuration management: security impact analysis procedure | NV012 Affirming Official | - | - | MET | - | - |
| CM.L2-3.4.5 | GitHub branch protection + required reviews | NV012 Affirming Official | nv012/all-covered/github_branch_protection.json | a911dd6a6276 | MET | - | - |
| CM.L2-3.4.6 | Disable non-FedRAMP-authorized services for the CUI OU (least functionality) | NV012 Affirming Official | - | - | MET | - | - |
| CM.L2-3.4.7 | Disable non-FedRAMP-authorized services for the CUI OU (least functionality) | NV012 Affirming Official | - | - | MET | - | - |
| CM.L2-3.4.8 | Binary Authorization — image allowlist / user-installed software | NV012 Affirming Official | nv012/all-covered/gcp_binauth_allowlist.json | e1bec3138a1e | MET | - | - |
| CM.L2-3.4.9 | Binary Authorization — image allowlist / user-installed software | NV012 Affirming Official | nv012/all-covered/gcp_binauth_allowlist.json | e1bec3138a1e | MET | - | - |
| IA.L2-3.5.1 | Workspace Admin identity lifecycle + password policy | NV012 Affirming Official | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | MET | - | - |
| IA.L2-3.5.10 | Workspace Admin identity lifecycle + password policy | NV012 Affirming Official | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | MET | - | - |
| IA.L2-3.5.11 | Workspace Admin identity lifecycle + password policy | NV012 Affirming Official | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | MET | - | - |
| IA.L2-3.5.2 | Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU | NV012 Affirming Official | - | - | MET | - | - |
| IA.L2-3.5.3 | Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU | NV012 Affirming Official | nv012/all-covered/workspace_2sv.json | 6549f40b7941 | MET | - | - |
| IA.L2-3.5.4 | Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU | NV012 Affirming Official | - | - | MET | - | - |
| IA.L2-3.5.5 | Workspace Admin identity lifecycle + password policy | NV012 Affirming Official | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | MET | - | - |
| IA.L2-3.5.6 | Workspace Admin identity lifecycle + password policy | NV012 Affirming Official | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | MET | - | - |
| IA.L2-3.5.7 | Workspace Admin identity lifecycle + password policy | NV012 Affirming Official | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | MET | - | - |
| IA.L2-3.5.8 | Workspace Admin identity lifecycle + password policy | NV012 Affirming Official | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | MET | - | - |
| IA.L2-3.5.9 | Workspace Admin identity lifecycle + password policy | NV012 Affirming Official | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | MET | - | - |
| IR.L2-3.6.1 | Incident Response Plan + annual tabletop exercise | NV012 Affirming Official | - | - | MET | - | - |
| IR.L2-3.6.2 | Incident Response Plan + annual tabletop exercise | NV012 Affirming Official | - | - | MET | - | - |
| IR.L2-3.6.3 | Incident Response Plan + annual tabletop exercise | NV012 Affirming Official | - | - | MET | - | - |
| MA.L2-3.7.1 | Maintenance policy: approved vendor list + maintenance log | NV012 Affirming Official | - | - | MET | - | - |
| MA.L2-3.7.2 | Maintenance policy: approved vendor list + maintenance log | NV012 Affirming Official | - | - | MET | - | - |
| MA.L2-3.7.3 | Maintenance policy: approved vendor list + maintenance log | NV012 Affirming Official | - | - | MET | - | - |
| MA.L2-3.7.4 | Maintenance policy: approved vendor list + maintenance log | NV012 Affirming Official | - | - | MET | - | - |
| MA.L2-3.7.5 | Cloud Identity MFA for ops / break-glass roles | NV012 Affirming Official | nv012/all-covered/workspace_ops_mfa.json | d51b18159d04 | MET | - | - |
| MA.L2-3.7.6 | Maintenance policy: approved vendor list + maintenance log | NV012 Affirming Official | - | - | MET | - | - |
| MP.L2-3.8.1 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | NV012 Affirming Official | - | - | MET | - | - |
| MP.L2-3.8.2 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | NV012 Affirming Official | - | - | MET | - | - |
| MP.L2-3.8.3 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | NV012 Affirming Official | - | - | MET | - | - |
| MP.L2-3.8.4 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | NV012 Affirming Official | - | - | MET | - | - |
| MP.L2-3.8.5 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | NV012 Affirming Official | - | - | MET | - | - |
| MP.L2-3.8.6 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | NV012 Affirming Official | - | - | MET | - | - |
| MP.L2-3.8.7 | Chrome Cloud Management + Endpoint Verification (MDM) | NV012 Affirming Official | nv012/all-covered/chrome_mdm.json | df6706e07d44 | MET | - | - |
| MP.L2-3.8.8 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | NV012 Affirming Official | - | - | MET | - | - |
| MP.L2-3.8.9 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | NV012 Affirming Official | - | - | MET | - | - |
| PE.L2-3.10.1 | CSP-inherited physical protection (Google IL4 data-center controls) | NV012 Affirming Official | - | - | MET | - | - |
| PE.L2-3.10.2 | CSP-inherited physical protection (Google IL4 data-center controls) | NV012 Affirming Official | - | - | MET | - | - |
| PE.L2-3.10.3 | Physical access (visitor log + badge + WFH agreements) | NV012 Affirming Official | - | - | MET | - | - |
| PE.L2-3.10.4 | Physical access (visitor log + badge + WFH agreements) | NV012 Affirming Official | - | - | MET | - | - |
| PE.L2-3.10.5 | Physical access (visitor log + badge + WFH agreements) | NV012 Affirming Official | - | - | MET | - | - |
| PE.L2-3.10.6 | Physical access (visitor log + badge + WFH agreements) | NV012 Affirming Official | - | - | MET | - | - |
| PS.L2-3.9.1 | Personnel security: background screening + offboarding | NV012 Affirming Official | - | - | MET | - | - |
| PS.L2-3.9.2 | Personnel security: background screening + offboarding | NV012 Affirming Official | - | - | MET | - | - |
| RA.L2-3.11.1 | Formal risk assessment + finding tracker | NV012 Affirming Official | - | - | MET | - | - |
| RA.L2-3.11.2 | GCP Security Command Center — vulnerability management | NV012 Affirming Official | nv012/all-covered/gcp_scc_findings.json | 4472a35663ce | MET | - | - |
| RA.L2-3.11.3 | Formal risk assessment + finding tracker | NV012 Affirming Official | - | - | MET | - | - |
| SC.L2-3.13.1 | GCP Org Policy: US-only resource locations + restricted service usage | NV012 Affirming Official | nv012/all-covered/gcp_org_policy_region.json | 385f07ca2e58, 5f8e7ef2f8ff | MET | - | - |
| SC.L2-3.13.10 | Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto) | NV012 Affirming Official | - | - | MET | - | - |
| SC.L2-3.13.11 | Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto) | NV012 Affirming Official | nv012/all-covered/gcp_kms_cmvp.json | 3c4af60bc144 | MET | - | - |
| SC.L2-3.13.12 | Collaborative computing / mobile code / VoIP policies | NV012 Affirming Official | - | - | MET | - | - |
| SC.L2-3.13.13 | Collaborative computing / mobile code / VoIP policies | NV012 Affirming Official | - | - | MET | - | - |
| SC.L2-3.13.14 | Collaborative computing / mobile code / VoIP policies | NV012 Affirming Official | - | - | MET | - | - |
| SC.L2-3.13.15 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | NV012 Affirming Official | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | MET | - | - |
| SC.L2-3.13.16 | Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto) | NV012 Affirming Official | nv012/all-covered/gcp_cmek_at_rest.json | 52eb61a61772 | MET | - | - |
| SC.L2-3.13.2 | Security engineering principles (NIST SP 800-160 Vol.1) | NV012 Affirming Official | - | - | MET | - | - |
| SC.L2-3.13.3 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | NV012 Affirming Official | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | MET | - | - |
| SC.L2-3.13.4 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | NV012 Affirming Official | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | MET | - | - |
| SC.L2-3.13.5 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | NV012 Affirming Official | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | MET | - | - |
| SC.L2-3.13.6 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | NV012 Affirming Official | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | MET | - | - |
| SC.L2-3.13.7 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | NV012 Affirming Official | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | MET | - | - |
| SC.L2-3.13.8 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | NV012 Affirming Official | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | MET | - | - |
| SC.L2-3.13.9 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | NV012 Affirming Official | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | MET | - | - |
| SI.L2-3.14.1 | GCP Security Command Center — vulnerability management | NV012 Affirming Official | nv012/all-covered/gcp_scc_findings.json | 4472a35663ce | MET | - | - |
| SI.L2-3.14.2 | CrowdStrike Falcon EDR — malware + endpoint integrity | NV012 Affirming Official | nv012/all-covered/crowdstrike_edr.json | 78748c996698 | MET | - | - |
| SI.L2-3.14.3 | Cloud Monitoring + Workspace Alert Center (security alert monitoring/response) | NV012 Affirming Official | - | - | MET | - | - |
| SI.L2-3.14.4 | CrowdStrike Falcon EDR — malware + endpoint integrity | NV012 Affirming Official | nv012/all-covered/crowdstrike_edr.json | 78748c996698 | MET | - | - |
| SI.L2-3.14.5 | GCP Security Command Center — vulnerability management | NV012 Affirming Official | nv012/all-covered/gcp_scc_findings.json | 4472a35663ce | MET | - | - |
| SI.L2-3.14.6 | Cloud Monitoring + Workspace Alert Center (security alert monitoring/response) | NV012 Affirming Official | - | - | MET | - | - |
| SI.L2-3.14.7 | CrowdStrike Falcon EDR — malware + endpoint integrity | NV012 Affirming Official | nv012/all-covered/crowdstrike_edr.json | 78748c996698 | MET | - | - |

## 4. Per-control detail

### AC.L2-3.1.1

**Statement.** Limit system access to authorized users, processes acting on behalf of authorized users, and devices (including other systems).

- Family: AC · Weight: 5 · POA&M-eligible: false
- Implementation: IAM groups + least-privilege role bindings for CUI access
- Verification method: oracle-iam-least-privilege

- Attestation: ATT-AC.L2-3.1.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.367957+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.10

**Statement.** Use session lock with pattern-hiding displays to prevent access and viewing of data after a period of inactivity.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: Cloud Identity session control + failed-login lockout
- Verification method: oracle-session-control

- Attestation: ATT-AC.L2-3.1.10 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.380445+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.11

**Statement.** Terminate (automatically) a user session after a defined condition.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: Cloud Identity session control + failed-login lockout
- Verification method: oracle-session-control

- Attestation: ATT-AC.L2-3.1.11 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.393430+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.12

**Statement.** Monitor and control remote access sessions.

- Family: AC · Weight: 5 · POA&M-eligible: false
- Implementation: BeyondCorp Enterprise remote access + TLS enforcement
- Verification method: oracle-beyondcorp-remote-access

- Attestation: ATT-AC.L2-3.1.12 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.404895+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.13

**Statement.** Employ cryptographic mechanisms to protect the confidentiality of remote access sessions.

- Family: AC · Weight: 5 · POA&M-eligible: false
- Implementation: BeyondCorp Enterprise remote access + TLS enforcement
- Verification method: oracle-beyondcorp-remote-access

- Attestation: ATT-AC.L2-3.1.13 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.416901+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.14

**Statement.** Route remote access via managed access control points.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: BeyondCorp Enterprise remote access + TLS enforcement
- Verification method: oracle-beyondcorp-remote-access

- Attestation: ATT-AC.L2-3.1.14 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.428821+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.15

**Statement.** Authorize remote execution of privileged commands and remote access to security-relevant information.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: Remote access authorization (SSP appendix)
- Verification method: oracle-attested-reference

- Attestation: ATT-AC.L2-3.1.15 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.441094+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AC.L2-3.1.16

**Statement.** Authorize wireless access prior to allowing such connections.

- Family: AC · Weight: 5 · POA&M-eligible: false
- Implementation: Chrome Cloud Management + Endpoint Verification (MDM)
- Verification method: oracle-mdm-policy

- Attestation: ATT-AC.L2-3.1.16 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.453811+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.17

**Statement.** Protect wireless access using authentication and encryption.

- Family: AC · Weight: 5 · POA&M-eligible: false
- Implementation: Chrome Cloud Management + Endpoint Verification (MDM)
- Verification method: oracle-mdm-policy

- Attestation: ATT-AC.L2-3.1.17 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.465922+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.18

**Statement.** Control connection of mobile devices.

- Family: AC · Weight: 5 · POA&M-eligible: false
- Implementation: Chrome Cloud Management + Endpoint Verification (MDM)
- Verification method: oracle-mdm-policy

- Attestation: ATT-AC.L2-3.1.18 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.477693+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.19

**Statement.** Encrypt CUI on mobile devices and mobile computing platforms.

- Family: AC · Weight: 3 · POA&M-eligible: false
- Implementation: Chrome Cloud Management + Endpoint Verification (MDM)
- Verification method: oracle-mdm-policy

- Attestation: ATT-AC.L2-3.1.19 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.489390+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.2

**Statement.** Limit system access to the types of transactions and functions that authorized users are permitted to execute.

- Family: AC · Weight: 5 · POA&M-eligible: false
- Implementation: IAM groups + least-privilege role bindings for CUI access
- Verification method: oracle-iam-least-privilege

- Attestation: ATT-AC.L2-3.1.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.501286+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AC.L2-3.1.20

**Statement.** Verify and control/limit connections to and use of external systems.

- Family: AC · Weight: 1 · POA&M-eligible: false
- Implementation: VPC Service Controls perimeter — external system authorization
- Verification method: oracle-vpc-sc-perimeter

- Attestation: ATT-AC.L2-3.1.20 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.513721+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.21

**Statement.** Limit use of portable storage devices on external systems.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: Remote access authorization (SSP appendix)
- Verification method: oracle-attested-reference

- Attestation: ATT-AC.L2-3.1.21 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.526390+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AC.L2-3.1.22

**Statement.** Control CUI posted or processed on publicly accessible systems.

- Family: AC · Weight: 1 · POA&M-eligible: false
- Implementation: Remote access authorization (SSP appendix)
- Verification method: oracle-attested-reference

- Attestation: ATT-AC.L2-3.1.22 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.538180+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AC.L2-3.1.3

**Statement.** Control the flow of CUI in accordance with approved authorizations.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: Drive + Gmail DLP rules (control the flow of CUI)
- Verification method: oracle-drive-dlp-rules

- Attestation: ATT-AC.L2-3.1.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.549778+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AC.L2-3.1.4

**Statement.** Separate the duties of individuals to reduce the risk of malevolent activity without collusion.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: Separation of duties (RACI matrix)
- Verification method: oracle-attested-reference

- Attestation: ATT-AC.L2-3.1.4 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.561718+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AC.L2-3.1.5

**Statement.** Employ the principle of least privilege, including for specific security functions and privileged accounts.

- Family: AC · Weight: 3 · POA&M-eligible: false
- Implementation: IAM groups + least-privilege role bindings for CUI access
- Verification method: oracle-iam-least-privilege

- Attestation: ATT-AC.L2-3.1.5 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.573280+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AC.L2-3.1.6

**Statement.** Use non-privileged accounts or roles when accessing nonsecurity functions.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: GCP IAM policy + audit-log signals for privileged use
- Verification method: oracle-iam-privileged-use

- Attestation: ATT-AC.L2-3.1.6 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.584700+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.7

**Statement.** Prevent non-privileged users from executing privileged functions and capture the execution of such functions in audit logs.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: GCP IAM policy + audit-log signals for privileged use
- Verification method: oracle-iam-privileged-use

- Attestation: ATT-AC.L2-3.1.7 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.596947+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.8

**Statement.** Limit unsuccessful logon attempts.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: Cloud Identity session control + failed-login lockout
- Verification method: oracle-session-control

- Attestation: ATT-AC.L2-3.1.8 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.608109+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.9

**Statement.** Provide privacy and security notices consistent with applicable CUI rules.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: Login banner policy (system-use notification)
- Verification method: oracle-attested-reference

- Attestation: ATT-AC.L2-3.1.9 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.619400+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AT.L2-3.2.1

**Statement.** Ensure that managers, systems administrators, and users of organizational systems are made aware of the security risks associated with their activities and of the applicable policies, standards, and procedures related to the security of those systems.

- Family: AT · Weight: 5 · POA&M-eligible: false
- Implementation: Annual security awareness + role-based training program
- Verification method: oracle-attested-reference

- Attestation: ATT-AT.L2-3.2.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.631105+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AT.L2-3.2.2

**Statement.** Ensure that personnel are trained to carry out their assigned information security-related duties and responsibilities.

- Family: AT · Weight: 5 · POA&M-eligible: false
- Implementation: Annual security awareness + role-based training program
- Verification method: oracle-attested-reference

- Attestation: ATT-AT.L2-3.2.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.642840+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AT.L2-3.2.3

**Statement.** Provide security awareness training on recognizing and reporting potential indicators of insider threat.

- Family: AT · Weight: 1 · POA&M-eligible: true
- Implementation: Annual security awareness + role-based training program
- Verification method: oracle-attested-reference

- Attestation: ATT-AT.L2-3.2.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.654624+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AU.L2-3.3.1

**Statement.** Create and retain system audit logs and records to the extent needed to enable the monitoring, analysis, investigation, and reporting of unlawful or unauthorized system activity.

- Family: AU · Weight: 5 · POA&M-eligible: false
- Implementation: Workspace + GCP audit log export to retained Cloud Storage bucket
- Verification method: oracle-auditlog-export

- Attestation: ATT-AU.L2-3.3.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.667058+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AU.L2-3.3.2

**Statement.** Ensure that the actions of individual system users can be uniquely traced to those users, so they can be held accountable for their actions.

- Family: AU · Weight: 3 · POA&M-eligible: false
- Implementation: Workspace + GCP audit log export to retained Cloud Storage bucket
- Verification method: oracle-auditlog-export

- Attestation: ATT-AU.L2-3.3.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.678398+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AU.L2-3.3.3

**Statement.** Review and update logged events.

- Family: AU · Weight: 1 · POA&M-eligible: true
- Implementation: Audit management procedure (log review cadence + reports)
- Verification method: oracle-attested-reference

- Attestation: ATT-AU.L2-3.3.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.690065+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AU.L2-3.3.4

**Statement.** Alert in the event of an audit logging process failure.

- Family: AU · Weight: 1 · POA&M-eligible: true
- Implementation: Cloud Logging sinks + NTP + IAM on log buckets
- Verification method: oracle-cloud-logging-config

- Attestation: ATT-AU.L2-3.3.4 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.701973+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AU.L2-3.3.5

**Statement.** Correlate audit record review, analysis, and reporting processes for investigation and response to indications of unlawful, unauthorized, suspicious, or unusual activity.

- Family: AU · Weight: 5 · POA&M-eligible: false
- Implementation: Workspace + GCP audit log export to retained Cloud Storage bucket
- Verification method: oracle-auditlog-export

- Attestation: ATT-AU.L2-3.3.5 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.713860+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AU.L2-3.3.6

**Statement.** Provide audit record reduction and report generation to support on-demand analysis and reporting.

- Family: AU · Weight: 1 · POA&M-eligible: true
- Implementation: Audit management procedure (log review cadence + reports)
- Verification method: oracle-attested-reference

- Attestation: ATT-AU.L2-3.3.6 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.725503+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### AU.L2-3.3.7

**Statement.** Provide a system capability that compares and synchronizes internal system clocks with an authoritative source to generate time stamps for audit records.

- Family: AU · Weight: 1 · POA&M-eligible: true
- Implementation: Cloud Logging sinks + NTP + IAM on log buckets
- Verification method: oracle-cloud-logging-config

- Attestation: ATT-AU.L2-3.3.7 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.738379+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AU.L2-3.3.8

**Statement.** Protect audit information and audit logging tools from unauthorized access, modification, and deletion.

- Family: AU · Weight: 1 · POA&M-eligible: true
- Implementation: Cloud Logging sinks + NTP + IAM on log buckets
- Verification method: oracle-cloud-logging-config

- Attestation: ATT-AU.L2-3.3.8 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.749936+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AU.L2-3.3.9

**Statement.** Limit management of audit logging functionality to a subset of privileged users.

- Family: AU · Weight: 1 · POA&M-eligible: true
- Implementation: Cloud Logging sinks + NTP + IAM on log buckets
- Verification method: oracle-cloud-logging-config

- Attestation: ATT-AU.L2-3.3.9 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.761830+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### CA.L2-3.12.1

**Statement.** Periodically assess the security controls in organizational systems to determine if the controls are effective in their application.

- Family: CA · Weight: 5 · POA&M-eligible: false
- Implementation: Continuous monitoring: engine run history + POA&M tracker
- Verification method: oracle-attested-reference

- Attestation: ATT-CA.L2-3.12.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.773613+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### CA.L2-3.12.2

**Statement.** Develop and implement plans of action designed to correct deficiencies and reduce or eliminate vulnerabilities in organizational systems.

- Family: CA · Weight: 3 · POA&M-eligible: false
- Implementation: Continuous monitoring: engine run history + POA&M tracker
- Verification method: oracle-attested-reference

- Attestation: ATT-CA.L2-3.12.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.785168+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### CA.L2-3.12.3

**Statement.** Monitor security controls on an ongoing basis to ensure the continued effectiveness of the controls.

- Family: CA · Weight: 5 · POA&M-eligible: false
- Implementation: Continuous monitoring: engine run history + POA&M tracker
- Verification method: oracle-attested-reference

- Attestation: ATT-CA.L2-3.12.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.796751+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### CA.L2-3.12.4

**Statement.** Develop, document, and periodically update system security plans that describe system boundaries, system environments of operation, how security requirements are implemented, and the relationships with or connections to other systems.

- Family: CA · Weight: 1 · POA&M-eligible: false
- Implementation: System Security Plan supplement (system description)
- Verification method: oracle-attested-reference

- Attestation: ATT-CA.L2-3.12.4 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.818537+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### CM.L2-3.4.1

**Statement.** Establish and maintain baseline configurations and inventories of organizational systems (including hardware, software, firmware, and documentation) throughout the respective system development life cycles.

- Family: CM · Weight: 5 · POA&M-eligible: false
- Implementation: Terraform baseline configuration + resource inventory (IaC)
- Verification method: oracle-terraform-baseline

- Attestation: ATT-CM.L2-3.4.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.830325+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### CM.L2-3.4.2

**Statement.** Establish and enforce security configuration settings for information technology products employed in organizational systems.

- Family: CM · Weight: 5 · POA&M-eligible: false
- Implementation: Terraform baseline configuration + resource inventory (IaC)
- Verification method: oracle-terraform-baseline

- Attestation: ATT-CM.L2-3.4.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.841850+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### CM.L2-3.4.3

**Statement.** Track, review, approve or disapprove, and log changes to organizational systems.

- Family: CM · Weight: 1 · POA&M-eligible: true
- Implementation: GitHub branch protection + required reviews
- Verification method: oracle-github-change-mgmt

- Attestation: ATT-CM.L2-3.4.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.853231+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### CM.L2-3.4.4

**Statement.** Analyze the security impact of changes prior to implementation.

- Family: CM · Weight: 1 · POA&M-eligible: true
- Implementation: Configuration management: security impact analysis procedure
- Verification method: oracle-attested-reference

- Attestation: ATT-CM.L2-3.4.4 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.865141+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### CM.L2-3.4.5

**Statement.** Define, document, approve, and enforce physical and logical access restrictions associated with changes to organizational systems.

- Family: CM · Weight: 5 · POA&M-eligible: false
- Implementation: GitHub branch protection + required reviews
- Verification method: oracle-github-change-mgmt

- Attestation: ATT-CM.L2-3.4.5 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.876765+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### CM.L2-3.4.6

**Statement.** Employ the principle of least functionality by configuring organizational systems to provide only essential capabilities.

- Family: CM · Weight: 5 · POA&M-eligible: false
- Implementation: Disable non-FedRAMP-authorized services for the CUI OU (least functionality)
- Verification method: oracle-restrict-service-usage

- Attestation: ATT-CM.L2-3.4.6 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.888832+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### CM.L2-3.4.7

**Statement.** Restrict, disable, or prevent the use of nonessential programs, functions, ports, protocols, and services.

- Family: CM · Weight: 5 · POA&M-eligible: false
- Implementation: Disable non-FedRAMP-authorized services for the CUI OU (least functionality)
- Verification method: oracle-restrict-service-usage

- Attestation: ATT-CM.L2-3.4.7 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.900006+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### CM.L2-3.4.8

**Statement.** Apply deny-by-exception (blacklisting) policy to prevent the use of unauthorized software or deny-all, permit-by-exception (whitelisting) policy to allow the execution of authorized software.

- Family: CM · Weight: 5 · POA&M-eligible: false
- Implementation: Binary Authorization — image allowlist / user-installed software
- Verification method: oracle-binauth-allowlist

- Attestation: ATT-CM.L2-3.4.8 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.912723+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### CM.L2-3.4.9

**Statement.** Control and monitor user-installed software.

- Family: CM · Weight: 1 · POA&M-eligible: true
- Implementation: Binary Authorization — image allowlist / user-installed software
- Verification method: oracle-binauth-allowlist

- Attestation: ATT-CM.L2-3.4.9 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.924713+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.1

**Statement.** Identify system users, processes acting on behalf of users, and devices.

- Family: IA · Weight: 5 · POA&M-eligible: false
- Implementation: Workspace Admin identity lifecycle + password policy
- Verification method: oracle-workspace-admin-policy

- Attestation: ATT-IA.L2-3.5.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.936294+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.10

**Statement.** Store and transmit only cryptographically-protected passwords.

- Family: IA · Weight: 5 · POA&M-eligible: false
- Implementation: Workspace Admin identity lifecycle + password policy
- Verification method: oracle-workspace-admin-policy

- Attestation: ATT-IA.L2-3.5.10 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.947930+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.11

**Statement.** Obscure feedback of authentication information.

- Family: IA · Weight: 1 · POA&M-eligible: true
- Implementation: Workspace Admin identity lifecycle + password policy
- Verification method: oracle-workspace-admin-policy

- Attestation: ATT-IA.L2-3.5.11 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.961082+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.2

**Statement.** Authenticate (or verify) the identities of users, processes, or devices, as a prerequisite to allowing access to organizational systems.

- Family: IA · Weight: 5 · POA&M-eligible: false
- Implementation: Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU
- Verification method: oracle-mfa-2sv-enforced

- Attestation: ATT-IA.L2-3.5.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.972826+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### IA.L2-3.5.3

**Statement.** Use multifactor authentication for local and network access to privileged accounts and for network access to non-privileged accounts.

- Family: IA · Weight: 5 · POA&M-eligible: false
- Implementation: Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU
- Verification method: oracle-mfa-2sv-enforced

- Attestation: ATT-IA.L2-3.5.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.984495+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.4

**Statement.** Employ replay-resistant authentication mechanisms for network access to privileged and non-privileged accounts.

- Family: IA · Weight: 1 · POA&M-eligible: true
- Implementation: Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU
- Verification method: oracle-mfa-2sv-enforced

- Attestation: ATT-IA.L2-3.5.4 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:18.995870+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### IA.L2-3.5.5

**Statement.** Prevent reuse of identifiers for a defined period.

- Family: IA · Weight: 1 · POA&M-eligible: true
- Implementation: Workspace Admin identity lifecycle + password policy
- Verification method: oracle-workspace-admin-policy

- Attestation: ATT-IA.L2-3.5.5 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.007461+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.6

**Statement.** Disable identifiers after a defined period of inactivity.

- Family: IA · Weight: 1 · POA&M-eligible: true
- Implementation: Workspace Admin identity lifecycle + password policy
- Verification method: oracle-workspace-admin-policy

- Attestation: ATT-IA.L2-3.5.6 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.019708+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.7

**Statement.** Enforce a minimum password complexity and change of characters when new passwords are created.

- Family: IA · Weight: 1 · POA&M-eligible: true
- Implementation: Workspace Admin identity lifecycle + password policy
- Verification method: oracle-workspace-admin-policy

- Attestation: ATT-IA.L2-3.5.7 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.030929+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.8

**Statement.** Prohibit password reuse for a specified number of generations.

- Family: IA · Weight: 1 · POA&M-eligible: true
- Implementation: Workspace Admin identity lifecycle + password policy
- Verification method: oracle-workspace-admin-policy

- Attestation: ATT-IA.L2-3.5.8 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.042701+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.9

**Statement.** Allow temporary password use for system logons with an immediate change to a permanent password.

- Family: IA · Weight: 1 · POA&M-eligible: true
- Implementation: Workspace Admin identity lifecycle + password policy
- Verification method: oracle-workspace-admin-policy

- Attestation: ATT-IA.L2-3.5.9 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.054037+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IR.L2-3.6.1

**Statement.** Establish an operational incident-handling capability for organizational systems that includes preparation, detection, analysis, containment, recovery, and user response activities.

- Family: IR · Weight: 5 · POA&M-eligible: false
- Implementation: Incident Response Plan + annual tabletop exercise
- Verification method: oracle-attested-reference

- Attestation: ATT-IR.L2-3.6.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.066078+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### IR.L2-3.6.2

**Statement.** Track, document, and report incidents to designated officials and/or authorities both internal and external to the organization.

- Family: IR · Weight: 5 · POA&M-eligible: false
- Implementation: Incident Response Plan + annual tabletop exercise
- Verification method: oracle-attested-reference

- Attestation: ATT-IR.L2-3.6.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.077907+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### IR.L2-3.6.3

**Statement.** Test the organizational incident response capability.

- Family: IR · Weight: 1 · POA&M-eligible: true
- Implementation: Incident Response Plan + annual tabletop exercise
- Verification method: oracle-attested-reference

- Attestation: ATT-IR.L2-3.6.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.090272+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MA.L2-3.7.1

**Statement.** Perform maintenance on organizational systems.

- Family: MA · Weight: 3 · POA&M-eligible: false
- Implementation: Maintenance policy: approved vendor list + maintenance log
- Verification method: oracle-attested-reference

- Attestation: ATT-MA.L2-3.7.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.101984+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MA.L2-3.7.2

**Statement.** Provide controls on the tools, techniques, mechanisms, and personnel used to conduct system maintenance.

- Family: MA · Weight: 5 · POA&M-eligible: false
- Implementation: Maintenance policy: approved vendor list + maintenance log
- Verification method: oracle-attested-reference

- Attestation: ATT-MA.L2-3.7.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.113586+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MA.L2-3.7.3

**Statement.** Ensure equipment removed for off-site maintenance is sanitized of any CUI.

- Family: MA · Weight: 1 · POA&M-eligible: true
- Implementation: Maintenance policy: approved vendor list + maintenance log
- Verification method: oracle-attested-reference

- Attestation: ATT-MA.L2-3.7.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.125361+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MA.L2-3.7.4

**Statement.** Check media containing diagnostic and test programs for malicious code before the media are used in organizational systems.

- Family: MA · Weight: 3 · POA&M-eligible: false
- Implementation: Maintenance policy: approved vendor list + maintenance log
- Verification method: oracle-attested-reference

- Attestation: ATT-MA.L2-3.7.4 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.137911+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MA.L2-3.7.5

**Statement.** Require multifactor authentication to establish nonlocal maintenance sessions via external network connections and terminate such connections when nonlocal maintenance is complete.

- Family: MA · Weight: 5 · POA&M-eligible: false
- Implementation: Cloud Identity MFA for ops / break-glass roles
- Verification method: oracle-remote-maintenance-mfa

- Attestation: ATT-MA.L2-3.7.5 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.149574+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### MA.L2-3.7.6

**Statement.** Supervise the maintenance activities of maintenance personnel without required access authorization.

- Family: MA · Weight: 1 · POA&M-eligible: true
- Implementation: Maintenance policy: approved vendor list + maintenance log
- Verification method: oracle-attested-reference

- Attestation: ATT-MA.L2-3.7.6 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.162034+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MP.L2-3.8.1

**Statement.** Protect (i.e., physically control and securely store) system media containing CUI, both paper and digital.

- Family: MP · Weight: 3 · POA&M-eligible: false
- Implementation: Media protection: labeling, storage, sanitization (NIST SP 800-88)
- Verification method: oracle-attested-reference

- Attestation: ATT-MP.L2-3.8.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.174408+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MP.L2-3.8.2

**Statement.** Limit access to CUI on system media to authorized users.

- Family: MP · Weight: 3 · POA&M-eligible: false
- Implementation: Media protection: labeling, storage, sanitization (NIST SP 800-88)
- Verification method: oracle-attested-reference

- Attestation: ATT-MP.L2-3.8.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.186785+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MP.L2-3.8.3

**Statement.** Sanitize or destroy system media containing CUI before disposal or release for reuse.

- Family: MP · Weight: 5 · POA&M-eligible: false
- Implementation: Media protection: labeling, storage, sanitization (NIST SP 800-88)
- Verification method: oracle-attested-reference

- Attestation: ATT-MP.L2-3.8.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.198450+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MP.L2-3.8.4

**Statement.** Mark media with necessary CUI markings and distribution limitations.

- Family: MP · Weight: 1 · POA&M-eligible: true
- Implementation: Media protection: labeling, storage, sanitization (NIST SP 800-88)
- Verification method: oracle-attested-reference

- Attestation: ATT-MP.L2-3.8.4 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.209881+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MP.L2-3.8.5

**Statement.** Control access to media containing CUI and maintain accountability for media during transport outside of controlled areas.

- Family: MP · Weight: 1 · POA&M-eligible: true
- Implementation: Media protection: labeling, storage, sanitization (NIST SP 800-88)
- Verification method: oracle-attested-reference

- Attestation: ATT-MP.L2-3.8.5 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.222197+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MP.L2-3.8.6

**Statement.** Implement cryptographic mechanisms to protect the confidentiality of CUI stored on digital media during transport unless otherwise protected by alternative physical safeguards.

- Family: MP · Weight: 1 · POA&M-eligible: true
- Implementation: Media protection: labeling, storage, sanitization (NIST SP 800-88)
- Verification method: oracle-attested-reference

- Attestation: ATT-MP.L2-3.8.6 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.234016+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MP.L2-3.8.7

**Statement.** Control the use of removable media on system components.

- Family: MP · Weight: 5 · POA&M-eligible: false
- Implementation: Chrome Cloud Management + Endpoint Verification (MDM)
- Verification method: oracle-mdm-policy

- Attestation: ATT-MP.L2-3.8.7 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.245585+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### MP.L2-3.8.8

**Statement.** Prohibit the use of portable storage devices when such devices have no identifiable owner.

- Family: MP · Weight: 3 · POA&M-eligible: false
- Implementation: Media protection: labeling, storage, sanitization (NIST SP 800-88)
- Verification method: oracle-attested-reference

- Attestation: ATT-MP.L2-3.8.8 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.257442+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### MP.L2-3.8.9

**Statement.** Protect the confidentiality of backup CUI at storage locations.

- Family: MP · Weight: 1 · POA&M-eligible: true
- Implementation: Media protection: labeling, storage, sanitization (NIST SP 800-88)
- Verification method: oracle-attested-reference

- Attestation: ATT-MP.L2-3.8.9 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.269571+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### PE.L2-3.10.1

**Statement.** Limit physical access to organizational systems, equipment, and the respective operating environments to authorized individuals.

- Family: PE · Weight: 5 · POA&M-eligible: false
- Implementation: CSP-inherited physical protection (Google IL4 data-center controls)
- Verification method: inherited:google-workspace-crm

- Attestation: ATT-PE.L2-3.10.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.281663+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### PE.L2-3.10.2

**Statement.** Protect and monitor the physical facility and support infrastructure for organizational systems.

- Family: PE · Weight: 5 · POA&M-eligible: false
- Implementation: CSP-inherited physical protection (Google IL4 data-center controls)
- Verification method: inherited:google-workspace-crm

- Attestation: ATT-PE.L2-3.10.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.293362+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### PE.L2-3.10.3

**Statement.** Escort visitors and monitor visitor activity.

- Family: PE · Weight: 1 · POA&M-eligible: false
- Implementation: Physical access (visitor log + badge + WFH agreements)
- Verification method: oracle-attested-reference

- Attestation: ATT-PE.L2-3.10.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.306550+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### PE.L2-3.10.4

**Statement.** Maintain audit logs of physical access.

- Family: PE · Weight: 1 · POA&M-eligible: false
- Implementation: Physical access (visitor log + badge + WFH agreements)
- Verification method: oracle-attested-reference

- Attestation: ATT-PE.L2-3.10.4 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.318058+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### PE.L2-3.10.5

**Statement.** Control and manage physical access devices.

- Family: PE · Weight: 1 · POA&M-eligible: false
- Implementation: Physical access (visitor log + badge + WFH agreements)
- Verification method: oracle-attested-reference

- Attestation: ATT-PE.L2-3.10.5 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.329694+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### PE.L2-3.10.6

**Statement.** Enforce safeguarding measures for CUI at alternate work sites.

- Family: PE · Weight: 1 · POA&M-eligible: true
- Implementation: Physical access (visitor log + badge + WFH agreements)
- Verification method: oracle-attested-reference

- Attestation: ATT-PE.L2-3.10.6 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.341875+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### PS.L2-3.9.1

**Statement.** Screen individuals prior to authorizing access to organizational systems containing CUI.

- Family: PS · Weight: 3 · POA&M-eligible: false
- Implementation: Personnel security: background screening + offboarding
- Verification method: oracle-attested-reference

- Attestation: ATT-PS.L2-3.9.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.353840+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### PS.L2-3.9.2

**Statement.** Ensure that organizational systems containing CUI are protected during and after personnel actions such as terminations and transfers.

- Family: PS · Weight: 5 · POA&M-eligible: false
- Implementation: Personnel security: background screening + offboarding
- Verification method: oracle-attested-reference

- Attestation: ATT-PS.L2-3.9.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.366553+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### RA.L2-3.11.1

**Statement.** Periodically assess the risk to organizational operations (including mission, functions, image, or reputation), organizational assets, and individuals, resulting from the operation of organizational systems and the associated processing, storage, or transmission of CUI.

- Family: RA · Weight: 3 · POA&M-eligible: false
- Implementation: Formal risk assessment + finding tracker
- Verification method: oracle-attested-reference

- Attestation: ATT-RA.L2-3.11.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.378664+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### RA.L2-3.11.2

**Statement.** Scan for vulnerabilities in organizational systems and applications periodically and when new vulnerabilities affecting those systems and applications are identified.

- Family: RA · Weight: 5 · POA&M-eligible: false
- Implementation: GCP Security Command Center — vulnerability management
- Verification method: oracle-scc-vuln-mgmt

- Attestation: ATT-RA.L2-3.11.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.390515+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### RA.L2-3.11.3

**Statement.** Remediate vulnerabilities in accordance with risk assessments.

- Family: RA · Weight: 1 · POA&M-eligible: true
- Implementation: Formal risk assessment + finding tracker
- Verification method: oracle-attested-reference

- Attestation: ATT-RA.L2-3.11.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.402020+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### SC.L2-3.13.1

**Statement.** Monitor, control, and protect communications (i.e., information transmitted or received by organizational systems) at the external boundaries and key internal boundaries of organizational systems.

- Family: SC · Weight: 5 · POA&M-eligible: false
- Implementation: GCP Org Policy: US-only resource locations + restricted service usage
- Verification method: oracle-orgpolicy-us-residency

- Attestation: ATT-SC.L2-3.13.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.413051+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.10

**Statement.** Establish and manage cryptographic keys for cryptography employed in organizational systems.

- Family: SC · Weight: 1 · POA&M-eligible: true
- Implementation: Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto)
- Verification method: oracle-cmek-fips-keyring

- Attestation: ATT-SC.L2-3.13.10 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.424354+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### SC.L2-3.13.11

**Statement.** Employ FIPS-validated cryptography when used to protect the confidentiality of CUI.

- Family: SC · Weight: 5 · POA&M-eligible: false
- Implementation: Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto)
- Verification method: oracle-cmek-fips-keyring

- Attestation: ATT-SC.L2-3.13.11 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.436197+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.12

**Statement.** Prohibit remote activation of collaborative computing devices and provide indication of devices in use to users present at the device.

- Family: SC · Weight: 1 · POA&M-eligible: true
- Implementation: Collaborative computing / mobile code / VoIP policies
- Verification method: oracle-attested-reference

- Attestation: ATT-SC.L2-3.13.12 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.447663+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### SC.L2-3.13.13

**Statement.** Control and monitor the use of mobile code.

- Family: SC · Weight: 1 · POA&M-eligible: true
- Implementation: Collaborative computing / mobile code / VoIP policies
- Verification method: oracle-attested-reference

- Attestation: ATT-SC.L2-3.13.13 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.458707+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### SC.L2-3.13.14

**Statement.** Control and monitor the use of Voice over Internet Protocol (VoIP) technologies.

- Family: SC · Weight: 1 · POA&M-eligible: true
- Implementation: Collaborative computing / mobile code / VoIP policies
- Verification method: oracle-attested-reference

- Attestation: ATT-SC.L2-3.13.14 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.471102+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### SC.L2-3.13.15

**Statement.** Protect the authenticity of communications sessions.

- Family: SC · Weight: 5 · POA&M-eligible: false
- Implementation: VPC network segmentation (subnetworks + firewalls + Cloud Armor)
- Verification method: oracle-vpc-segmentation

- Attestation: ATT-SC.L2-3.13.15 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.483245+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.16

**Statement.** Protect the confidentiality of CUI at rest.

- Family: SC · Weight: 1 · POA&M-eligible: true
- Implementation: Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto)
- Verification method: oracle-cmek-fips-keyring

- Attestation: ATT-SC.L2-3.13.16 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.495052+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.2

**Statement.** Employ architectural designs, software development techniques, and systems engineering principles that promote effective information security within organizational systems.

- Family: SC · Weight: 5 · POA&M-eligible: false
- Implementation: Security engineering principles (NIST SP 800-160 Vol.1)
- Verification method: oracle-attested-reference

- Attestation: ATT-SC.L2-3.13.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.507307+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### SC.L2-3.13.3

**Statement.** Separate user functionality from system management functionality.

- Family: SC · Weight: 1 · POA&M-eligible: true
- Implementation: VPC network segmentation (subnetworks + firewalls + Cloud Armor)
- Verification method: oracle-vpc-segmentation

- Attestation: ATT-SC.L2-3.13.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.518977+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.4

**Statement.** Prevent unauthorized and unintended information transfer via shared system resources.

- Family: SC · Weight: 1 · POA&M-eligible: true
- Implementation: VPC network segmentation (subnetworks + firewalls + Cloud Armor)
- Verification method: oracle-vpc-segmentation

- Attestation: ATT-SC.L2-3.13.4 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.530863+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.5

**Statement.** Implement subnetworks for publicly accessible system components that are physically or logically separated from internal networks.

- Family: SC · Weight: 5 · POA&M-eligible: false
- Implementation: VPC network segmentation (subnetworks + firewalls + Cloud Armor)
- Verification method: oracle-vpc-segmentation

- Attestation: ATT-SC.L2-3.13.5 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.542785+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.6

**Statement.** Deny network communications traffic by default and allow network communications traffic by exception (i.e., deny all, permit by exception).

- Family: SC · Weight: 5 · POA&M-eligible: false
- Implementation: VPC network segmentation (subnetworks + firewalls + Cloud Armor)
- Verification method: oracle-vpc-segmentation

- Attestation: ATT-SC.L2-3.13.6 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.554320+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.7

**Statement.** Prevent remote devices from simultaneously establishing non-remote connections with organizational systems and communicating via some other connection to resources in external networks (i.e., split tunneling).

- Family: SC · Weight: 1 · POA&M-eligible: true
- Implementation: VPC network segmentation (subnetworks + firewalls + Cloud Armor)
- Verification method: oracle-vpc-segmentation

- Attestation: ATT-SC.L2-3.13.7 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.565467+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.8

**Statement.** Implement cryptographic mechanisms to prevent unauthorized disclosure of CUI during transmission unless otherwise protected by alternative physical safeguards.

- Family: SC · Weight: 3 · POA&M-eligible: false
- Implementation: VPC network segmentation (subnetworks + firewalls + Cloud Armor)
- Verification method: oracle-vpc-segmentation

- Attestation: ATT-SC.L2-3.13.8 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.577819+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.9

**Statement.** Terminate network connections associated with communications sessions at the end of the sessions or after a defined period of inactivity.

- Family: SC · Weight: 1 · POA&M-eligible: true
- Implementation: VPC network segmentation (subnetworks + firewalls + Cloud Armor)
- Verification method: oracle-vpc-segmentation

- Attestation: ATT-SC.L2-3.13.9 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.589435+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SI.L2-3.14.1

**Statement.** Identify, report, and correct system flaws in a timely manner.

- Family: SI · Weight: 5 · POA&M-eligible: false
- Implementation: GCP Security Command Center — vulnerability management
- Verification method: oracle-scc-vuln-mgmt

- Attestation: ATT-SI.L2-3.14.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.600800+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SI.L2-3.14.2

**Statement.** Provide protection from malicious code at designated locations within organizational systems.

- Family: SI · Weight: 5 · POA&M-eligible: false
- Implementation: CrowdStrike Falcon EDR — malware + endpoint integrity
- Verification method: oracle-endpoint-edr

- Attestation: ATT-SI.L2-3.14.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.612826+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SI.L2-3.14.3

**Statement.** Monitor system security alerts and advisories and take action in response.

- Family: SI · Weight: 5 · POA&M-eligible: false
- Implementation: Cloud Monitoring + Workspace Alert Center (security alert monitoring/response)
- Verification method: oracle-monitoring-alerts

- Attestation: ATT-SI.L2-3.14.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.624799+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### SI.L2-3.14.4

**Statement.** Update malicious code protection mechanisms when new releases are available.

- Family: SI · Weight: 5 · POA&M-eligible: false
- Implementation: CrowdStrike Falcon EDR — malware + endpoint integrity
- Verification method: oracle-endpoint-edr

- Attestation: ATT-SI.L2-3.14.4 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.636542+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SI.L2-3.14.5

**Statement.** Perform periodic scans of organizational systems and real-time scans of files from external sources as files are downloaded, opened, or executed.

- Family: SI · Weight: 3 · POA&M-eligible: false
- Implementation: GCP Security Command Center — vulnerability management
- Verification method: oracle-scc-vuln-mgmt

- Attestation: ATT-SI.L2-3.14.5 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.649580+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SI.L2-3.14.6

**Statement.** Monitor organizational systems, including inbound and outbound communications traffic, to detect attacks and indicators of potential attacks.

- Family: SI · Weight: 5 · POA&M-eligible: false
- Implementation: Cloud Monitoring + Workspace Alert Center (security alert monitoring/response)
- Verification method: oracle-monitoring-alerts

- Attestation: ATT-SI.L2-3.14.6 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.661486+00:00
  - Adequacy assumption: Implementation reviewed; control met by human/inherited determination.
  - Sufficiency justification: No machine oracle for this control; attested MET on documentary/CSP basis.

### SI.L2-3.14.7

**Statement.** Identify unauthorized use of organizational systems.

- Family: SI · Weight: 3 · POA&M-eligible: false
- Implementation: CrowdStrike Falcon EDR — malware + endpoint integrity
- Verification method: oracle-endpoint-edr

- Attestation: ATT-SI.L2-3.14.7 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-04T20:35:19.673721+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

## 5. Colophon

| Layer | Named graph | Triples |
| --- | --- | --- |
| attestations | `http://dynamicalsystems.group/compliance-engine/attestations` | 2194 |
| audit | `http://dynamicalsystems.group/compliance-engine/audit` | 880 |
| evidence | `http://dynamicalsystems.group/compliance-engine/evidence` | 461 |
| ontology | `http://dynamicalsystems.group/compliance-engine/ontology` | 1057 |
| order | `http://dynamicalsystems.group/compliance-engine/order` | 354 |
| plan | `http://dynamicalsystems.group/compliance-engine/plan` | 0 |
| plan_execution | `http://dynamicalsystems.group/compliance-engine/plan-execution` | 225 |
| structural | `http://dynamicalsystems.group/compliance-engine/structural` | 516 |

Dataset SHA-256: `111fee7ccbee578ed03503b6d700682238ccbef4d218f3ac686d833b028bd9e6`

Document date (max prov:generatedAtTime): 2026-07-04T20:35:19.673721+00:00

SPRS summary: score 110 (Final); 49 MET-by-machine / 61 MET-by-human-only; contradictions: 0.

Artifact hashes (BOM): 61

- `00693338fb29c30f553937069f1ec3b7285cd4f02a089d18e8d029522c40e3ea`
- `00bcfd580b52bafaf2228a159b675c11b06b6719d36a470c54510daf45192841`
- `02b35ae9966c949a3a8b050ba1a5b39a698248404abeb6ff366cb9cc43ce95be`
- `072558ed5a4093921e411d5c87f3082d1fe97ccdc737cdab61f959c9d9a8bb22`
- `0ed2eedf228cfa815e80d241f2bfd62368616ba6ef2ee40ef91c317dc9e8c4a7`
- `0f4442a470be7e99b7a9936a8a822c7f2dc0278899d1fd30127b7a724b3d711c`
- `10bee86a3f6d301f24538c1caa533a0fcd7121faa529c0c9721c28497e23fae1`
- `16841fa1f816e1147f8766632e244e15285d57866efe2b0be59653709c1132ab`
- `182a76ef5a66727c534d1ccd8fb1964730d2cb84fdeee2ba142a0413d3f382ee`
- `240d2c650431b08bb7ecc7e89dcfa9b57b0d013b873b02640f15ec3ef2fa2e69`
- `2a64f51ac186a4af034db0ab9b5c56f00c86587dc4a60f455a2f86688c806c3c`
- `2d9165ac19f597a87ad36a01ebd58f042cdea08287d3b6a8325ad1297d03daba`
- `385f07ca2e587097c8fdb83a7175af8d073717180b8e9db3670d7e5bc346897e`
- `3c4af60bc14480071afa3b9486fa7514484a9b6dcc77846d325e57f2955d47ac`
- `4472a35663cebbc9ec59579789d76db8ebd76fca2a5942cf5c5bc891e5af8583`
- `4588056ec807f49a6ddd42a383289d3bb6d883ef50c6a29ad1c330e361fe7b1d`
- `45b70ef22dcb69f47a8943271206d860d8f770af1549614893f972302241af0d`
- `46854b1f1236bbc9a02a71ae82e57924a77e7782f63751d113e5e7175c0345df`
- `4ac684c2c745b9e089e31d43e6aabb5fa75c6e1eb261f0dc02ddca2a9ca03110`
- `4bba2d0adcbb48ec02d9b82a9ec4c9655c13c20b39c35136630de23b08f32f12`
- `52eb61a61772b7878d6db0b96ae3441d5f1bb66f0f1bf5cbc7565481acf23cde`
- `54f4e36505afc95a51970473c01f2ae84b427ce29b559c1ccb4de9d2910646d9`
- `5725677498b414e229ecc641b723a7e8120affbbc89e18acc133831895dfb438`
- `594252df359f78bd131ed2d4944c62907b779167f547596cc320378c69406a69`
- `59a6617d68a550cd248b61f625156d0e6b71c6c4b69c989419766456f5dc833f`
- `5aa6e088007fab5ef6b5b8db1c5d6d65d190ec16483786aae44ecedb50f51803`
- `5c41b30cc0ef81407debf3fb91b9912a1a1da06de9752eccb96dd597af1d96a0`
- `5f8e7ef2f8ffc747ece0831bf33066eb499c1f12b2c5f5bb7e8768ce1fe921fa`
- `618cca5c6a8b5754110f12d12793eb66b6c0f1a157601c21422cdbec61fbea12`
- `6549f40b7941e00ae547750979c6a06ca36b640939dae098981394e4248dd3be`
- `69dcbba5163957c242c6c0795526f1b4010a23e92c1c575ac92ed38d5d11f1c3`
- `6c69bdddaea378c058139148d6865c4cba32f0b00b86c9d24f2ba2aafb2b97c1`
- `6ce12e8ab8fe645b2baefcaad9bc34ac04b98b047ceb436561e9d8e44428f11a`
- `70d573b23771a8c3d14ec76cd557a37722ca3fc8ca97246dce7bfc454d70bcf7`
- `71518eb5abf470d29cc44d7d43ded285a268dc775f0eae602edc42bc278fcdd2`
- `753946a895a2cb9963971ad499cfb0efe07ee3ad06f61d060d5035596421c853`
- `78748c9966987bfedd68a2453a0eca06763c63d93df1a5ee3db598c507c498f4`
- `7bd99136884d5c631f4e85e907faf9bb05355091e8d765e5b7d841a65fdd6514`
- `7bf8baba37a2344c1d8dddf135eb500e4cf768754c29bdccfb4b55183338398d`
- `7c647de4e6e837b3a54f0a514b6f54f81a493520702e5265c4483ac51b34b4f4`
- `82547e55fc7112a6d34cea355f171477576cfa939bf7075bb55b27134c6b50ad`
- `82e5d2082cc9fb90786e3aeca299c3331a8cfbdb2e486a832c257cb6bd10d9c4`
- `8959f24468b8f262147051cfa413d1beebea65bd15144dcb01afd7b32689d86e`
- `951bd49a4439703fb33ac5d505697bbac13f8803712bf37766bfab9333a770bf`
- `9ab7579fe94b5f346b31d899bb9e9824ee4cbf4a43b7d729942a13736625d0f0`
- `a911dd6a6276701fffb7957d3a0dcbf8618bd137b391f2c8636734eebdcb3d55`
- `b5e9a6da66f8d13b6a81113c09cf7f0d704b9d621a6300aeee0d3df2e3e7ca29`
- `b6c67e930e8a45acefac192bf87956bcf8a39faf35630792a4568daa2cc354bc`
- `ba9e49d5a3f641ff1f1e39cdc16292d6fcbda1e73c9293ceb591936e5ecfc7e9`
- `bebab0adde65490b3c2ae58ca2698bd5412a9160fa1392a70190caabddffc454`
- `c0a98ce6e1da83ca761c6340c33df652b5e100747a63dce7e36506a19e24d5a0`
- `c227e4157499aeba329299268c7893009ccc7425a62f7aee8e68d9a3de44908b`
- `cde1f27066a7135ae7f16a9fd1bcc5fa4bdb7ac1c92f52a29c0778d362daa0d0`
- `ce20d3b1b76ec95c37328a20ddc89ff47cf667bcbb417c0757a43f8e110581b8`
- `d51b18159d04d6edf398258392cbd60434bf1609a8b89b6ee5eb5b08a47ffa52`
- `dbbec27575687acd6dd7f477539165531ff5ed1a7bff42d1f53983e165dd4584`
- `df6706e07d448f632c0f7304eb2d1ce5d78b55f7908fe70eb1535809d42df746`
- `e10a155015bcf4aedda9c2c83e35b5f29b9b0f33f401224d2a4f8600e331c134`
- `e1bec3138a1ea59f82170a1bb8b5be92f8efcf66e6345736c2651501c258763a`
- `e2aace316858ca915c076150d78d7813121c47dcea8be7b84f685c9ad8d444b2`
- `ea589346e8b68f5865c4abe045628dce5b9ae61a03a92585b1a082fd59c77982`

**NON-EVIDENTIARY stamp:** statuses present — mock. Not a submittable SSP (mock evidence).

Rebuild and drift-check:

```bash
uv run python -m documents.ssp build --input output/engine.trig
uv run python -m documents.ssp build --check
```
