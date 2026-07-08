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
| Dataset SHA-256 | 5bfb0f7f4967a0b96a0d8462799e6047ea2ee95c63fb5b0757f7a09071df2041 |
| Quad count | 4348 |
| Document date | 2026-07-08T18:24:37.931146+00:00 |
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

| Control | Implementation | Responsible party | Evidence location | Evidence hash | Status | Backing | Gap notes | POA&M ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AC.L2-3.1.1 | IAM groups + least-privilege role bindings for CUI access | NV012 Affirming Official | nv012/all-covered/gcp_iam_bindings.json | 4bba2d0adcbb, 6c69bdddaea3 | MET | machine | - | - |
| AC.L2-3.1.10 | Cloud Identity session control + failed-login lockout | - | nv012/all-covered/gcp_session_control.json | 8959f24468b8 | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.11 | Cloud Identity session control + failed-login lockout | - | nv012/all-covered/gcp_session_control.json | 8959f24468b8 | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.12 | BeyondCorp Enterprise remote access + TLS enforcement | - | nv012/all-covered/beyondcorp_remote.json | 753946a895a2 | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.13 | BeyondCorp Enterprise remote access + TLS enforcement | - | nv012/all-covered/beyondcorp_remote.json | 753946a895a2 | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.14 | BeyondCorp Enterprise remote access + TLS enforcement | - | nv012/all-covered/beyondcorp_remote.json | 753946a895a2 | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.15 | Remote access authorization (SSP appendix) | - | - | - | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.16 | Chrome Cloud Management + Endpoint Verification (MDM) | - | nv012/all-covered/chrome_mdm.json | df6706e07d44 | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.17 | Chrome Cloud Management + Endpoint Verification (MDM) | - | nv012/all-covered/chrome_mdm.json | df6706e07d44 | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.18 | Chrome Cloud Management + Endpoint Verification (MDM) | - | nv012/all-covered/chrome_mdm.json | df6706e07d44 | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.19 | Chrome Cloud Management + Endpoint Verification (MDM) | - | nv012/all-covered/chrome_mdm.json | df6706e07d44 | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.2 | IAM groups + least-privilege role bindings for CUI access | NV012 Affirming Official | nv012/all-covered/gcp_iam_access_enforcement.json | 9c2e2dd99b27 | MET | machine | - | - |
| AC.L2-3.1.20 | VPC Service Controls perimeter — external system authorization | - | nv012/all-covered/gcp_vpc_service_controls.json | b6c67e930e8a | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.21 | Remote access authorization (SSP appendix) | - | - | - | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.22 | Remote access authorization (SSP appendix) | - | - | - | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.3 | Drive + Gmail DLP rules (control the flow of CUI) | NV012 Affirming Official | nv012/all-covered/gcp_iam_access_enforcement.json | 9c2e2dd99b27 | MET | machine | - | - |
| AC.L2-3.1.4 | Separation of duties (RACI matrix) | - | - | - | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.5 | IAM groups + least-privilege role bindings for CUI access | NV012 Affirming Official | nv012/all-covered/gcp_iam_access_enforcement.json | 9c2e2dd99b27 | MET | machine | - | - |
| AC.L2-3.1.6 | GCP IAM policy + audit-log signals for privileged use | - | nv012/all-covered/gcp_iam_privileged.json | 594252df359f | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.7 | GCP IAM policy + audit-log signals for privileged use | - | nv012/all-covered/gcp_iam_privileged.json | 594252df359f | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.8 | Cloud Identity session control + failed-login lockout | - | nv012/all-covered/gcp_session_control.json | 8959f24468b8 | PLANNED | - | not attested (planned) | - |
| AC.L2-3.1.9 | Login banner policy (system-use notification) | - | - | - | PLANNED | - | not attested (planned) | - |
| AT.L2-3.2.1 | Annual security awareness + role-based training program | - | - | - | PLANNED | - | not attested (planned) | - |
| AT.L2-3.2.2 | Annual security awareness + role-based training program | - | - | - | PLANNED | - | not attested (planned) | - |
| AT.L2-3.2.3 | Annual security awareness + role-based training program | - | - | - | PLANNED | - | not attested (planned) | - |
| AU.L2-3.3.1 | Workspace + GCP audit log export to retained Cloud Storage bucket | NV012 Affirming Official | nv012/all-covered/gcp_cloud_audit.json | 2690e5e9a376 | MET | machine | - | - |
| AU.L2-3.3.2 | Workspace + GCP audit log export to retained Cloud Storage bucket | NV012 Affirming Official | nv012/all-covered/gcp_cloud_audit.json | 2690e5e9a376 | MET | machine | - | - |
| AU.L2-3.3.3 | Audit management procedure (log review cadence + reports) | - | - | - | PLANNED | - | not attested (planned) | - |
| AU.L2-3.3.4 | Cloud Logging sinks + NTP + IAM on log buckets | - | nv012/all-covered/gcp_cloud_logging.json | dbbec2757568 | PLANNED | - | not attested (planned) | - |
| AU.L2-3.3.5 | Workspace + GCP audit log export to retained Cloud Storage bucket | NV012 Affirming Official | nv012/all-covered/gcp_cloud_audit.json | 2690e5e9a376 | MET | machine | - | - |
| AU.L2-3.3.6 | Audit management procedure (log review cadence + reports) | - | - | - | PLANNED | - | not attested (planned) | - |
| AU.L2-3.3.7 | Cloud Logging sinks + NTP + IAM on log buckets | - | nv012/all-covered/gcp_cloud_logging.json | dbbec2757568 | PLANNED | - | not attested (planned) | - |
| AU.L2-3.3.8 | Cloud Logging sinks + NTP + IAM on log buckets | - | nv012/all-covered/gcp_cloud_logging.json | dbbec2757568 | PLANNED | - | not attested (planned) | - |
| AU.L2-3.3.9 | Cloud Logging sinks + NTP + IAM on log buckets | - | nv012/all-covered/gcp_cloud_logging.json | dbbec2757568 | PLANNED | - | not attested (planned) | - |
| CA.L2-3.12.1 | Continuous monitoring: engine run history + POA&M tracker | - | - | - | PLANNED | - | not attested (planned) | - |
| CA.L2-3.12.2 | Continuous monitoring: engine run history + POA&M tracker | - | - | - | PLANNED | - | not attested (planned) | - |
| CA.L2-3.12.3 | Continuous monitoring: engine run history + POA&M tracker | - | - | - | PLANNED | - | not attested (planned) | - |
| CA.L2-3.12.4 | System Security Plan supplement (system description) | - | - | - | PLANNED | - | not attested (planned) | - |
| CM.L2-3.4.1 | Terraform baseline configuration + resource inventory (IaC) | NV012 Affirming Official | nv012/all-covered/gcp_config_baseline.json | 75ad3c7ecdfa | MET | machine | - | - |
| CM.L2-3.4.2 | Terraform baseline configuration + resource inventory (IaC) | NV012 Affirming Official | nv012/all-covered/gcp_config_baseline.json | 75ad3c7ecdfa | MET | machine | - | - |
| CM.L2-3.4.3 | GitHub branch protection + required reviews | - | nv012/all-covered/github_branch_protection.json | a911dd6a6276 | PLANNED | - | not attested (planned) | - |
| CM.L2-3.4.4 | Configuration management: security impact analysis procedure | - | - | - | PLANNED | - | not attested (planned) | - |
| CM.L2-3.4.5 | GitHub branch protection + required reviews | - | nv012/all-covered/github_branch_protection.json | a911dd6a6276 | PLANNED | - | not attested (planned) | - |
| CM.L2-3.4.6 | Disable non-FedRAMP-authorized services for the CUI OU (least functionality) | NV012 Affirming Official | nv012/all-covered/gcp_config_baseline.json | 75ad3c7ecdfa | MET | machine | - | - |
| CM.L2-3.4.7 | Disable non-FedRAMP-authorized services for the CUI OU (least functionality) | NV012 Affirming Official | nv012/all-covered/gcp_config_baseline.json | 75ad3c7ecdfa | MET | machine | - | - |
| CM.L2-3.4.8 | Binary Authorization — image allowlist / user-installed software | - | nv012/all-covered/gcp_binauth_allowlist.json | e1bec3138a1e | PLANNED | - | not attested (planned) | - |
| CM.L2-3.4.9 | Binary Authorization — image allowlist / user-installed software | - | nv012/all-covered/gcp_binauth_allowlist.json | e1bec3138a1e | PLANNED | - | not attested (planned) | - |
| IA.L2-3.5.1 | Workspace Admin identity lifecycle + password policy | - | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | PLANNED | - | not attested (planned) | - |
| IA.L2-3.5.10 | Workspace Admin identity lifecycle + password policy | - | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | PLANNED | - | not attested (planned) | - |
| IA.L2-3.5.11 | Workspace Admin identity lifecycle + password policy | - | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | PLANNED | - | not attested (planned) | - |
| IA.L2-3.5.2 | Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU | NV012 Affirming Official | nv012/all-covered/workspace_auth_hardening.json | d0cea0ecf9b3 | MET | machine | - | - |
| IA.L2-3.5.3 | Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU | NV012 Affirming Official | nv012/all-covered/workspace_2sv.json | 6549f40b7941 | MET | machine | - | - |
| IA.L2-3.5.4 | Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU | NV012 Affirming Official | nv012/all-covered/workspace_auth_hardening.json | d0cea0ecf9b3 | MET | machine | - | - |
| IA.L2-3.5.5 | Workspace Admin identity lifecycle + password policy | - | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | PLANNED | - | not attested (planned) | - |
| IA.L2-3.5.6 | Workspace Admin identity lifecycle + password policy | - | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | PLANNED | - | not attested (planned) | - |
| IA.L2-3.5.7 | Workspace Admin identity lifecycle + password policy | - | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | PLANNED | - | not attested (planned) | - |
| IA.L2-3.5.8 | Workspace Admin identity lifecycle + password policy | - | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | PLANNED | - | not attested (planned) | - |
| IA.L2-3.5.9 | Workspace Admin identity lifecycle + password policy | - | nv012/all-covered/workspace_admin_policy.json | 2d9165ac19f5 | PLANNED | - | not attested (planned) | - |
| IR.L2-3.6.1 | Incident Response Plan + annual tabletop exercise | - | - | - | PLANNED | - | not attested (planned) | - |
| IR.L2-3.6.2 | Incident Response Plan + annual tabletop exercise | - | - | - | PLANNED | - | not attested (planned) | - |
| IR.L2-3.6.3 | Incident Response Plan + annual tabletop exercise | - | - | - | PLANNED | - | not attested (planned) | - |
| MA.L2-3.7.1 | Maintenance policy: approved vendor list + maintenance log | - | - | - | PLANNED | - | not attested (planned) | - |
| MA.L2-3.7.2 | Maintenance policy: approved vendor list + maintenance log | - | - | - | PLANNED | - | not attested (planned) | - |
| MA.L2-3.7.3 | Maintenance policy: approved vendor list + maintenance log | - | - | - | PLANNED | - | not attested (planned) | - |
| MA.L2-3.7.4 | Maintenance policy: approved vendor list + maintenance log | - | - | - | PLANNED | - | not attested (planned) | - |
| MA.L2-3.7.5 | Cloud Identity MFA for ops / break-glass roles | - | nv012/all-covered/workspace_ops_mfa.json | d51b18159d04 | PLANNED | - | not attested (planned) | - |
| MA.L2-3.7.6 | Maintenance policy: approved vendor list + maintenance log | - | - | - | PLANNED | - | not attested (planned) | - |
| MP.L2-3.8.1 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | - | - | - | PLANNED | - | not attested (planned) | - |
| MP.L2-3.8.2 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | - | - | - | PLANNED | - | not attested (planned) | - |
| MP.L2-3.8.3 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | - | - | - | PLANNED | - | not attested (planned) | - |
| MP.L2-3.8.4 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | - | - | - | PLANNED | - | not attested (planned) | - |
| MP.L2-3.8.5 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | - | - | - | PLANNED | - | not attested (planned) | - |
| MP.L2-3.8.6 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | - | - | - | PLANNED | - | not attested (planned) | - |
| MP.L2-3.8.7 | Chrome Cloud Management + Endpoint Verification (MDM) | - | nv012/all-covered/chrome_mdm.json | df6706e07d44 | PLANNED | - | not attested (planned) | - |
| MP.L2-3.8.8 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | - | - | - | PLANNED | - | not attested (planned) | - |
| MP.L2-3.8.9 | Media protection: labeling, storage, sanitization (NIST SP 800-88) | - | - | - | PLANNED | - | not attested (planned) | - |
| PE.L2-3.10.1 | CSP-inherited physical protection (Google IL4 data-center controls) | NV012 Affirming Official | - | - | MET | human-only | - | - |
| PE.L2-3.10.2 | CSP-inherited physical protection (Google IL4 data-center controls) | NV012 Affirming Official | - | - | MET | human-only | - | - |
| PE.L2-3.10.3 | Physical access (visitor log + badge + WFH agreements) | - | - | - | PLANNED | - | not attested (planned) | - |
| PE.L2-3.10.4 | Physical access (visitor log + badge + WFH agreements) | - | - | - | PLANNED | - | not attested (planned) | - |
| PE.L2-3.10.5 | Physical access (visitor log + badge + WFH agreements) | - | - | - | PLANNED | - | not attested (planned) | - |
| PE.L2-3.10.6 | Physical access (visitor log + badge + WFH agreements) | - | - | - | PLANNED | - | not attested (planned) | - |
| PS.L2-3.9.1 | Personnel security: background screening + offboarding | - | - | - | PLANNED | - | not attested (planned) | - |
| PS.L2-3.9.2 | Personnel security: background screening + offboarding | - | - | - | PLANNED | - | not attested (planned) | - |
| RA.L2-3.11.1 | Formal risk assessment + finding tracker | - | - | - | PLANNED | - | not attested (planned) | - |
| RA.L2-3.11.2 | GCP Security Command Center — vulnerability management | - | nv012/all-covered/gcp_scc_findings.json | 4472a35663ce | PLANNED | - | not attested (planned) | - |
| RA.L2-3.11.3 | Formal risk assessment + finding tracker | - | - | - | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.1 | GCP Org Policy: US-only resource locations + restricted service usage | NV012 Affirming Official | nv012/all-covered/gcp_org_policy_region.json | 385f07ca2e58, 5f8e7ef2f8ff | MET | machine | - | - |
| SC.L2-3.13.10 | Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto) | NV012 Affirming Official | nv012/all-covered/gcp_sc_si_monitoring.json | 3923ae07c201 | MET | machine | - | - |
| SC.L2-3.13.11 | Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto) | NV012 Affirming Official | nv012/all-covered/gcp_kms_cmvp.json | 3c4af60bc144 | MET | machine | - | - |
| SC.L2-3.13.12 | Collaborative computing / mobile code / VoIP policies | - | - | - | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.13 | Collaborative computing / mobile code / VoIP policies | - | - | - | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.14 | Collaborative computing / mobile code / VoIP policies | - | - | - | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.15 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | - | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.16 | Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto) | NV012 Affirming Official | nv012/all-covered/gcp_cmek_at_rest.json | 52eb61a61772 | MET | machine | - | - |
| SC.L2-3.13.2 | Security engineering principles (NIST SP 800-160 Vol.1) | - | - | - | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.3 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | - | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.4 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | - | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.5 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | - | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.6 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | - | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.7 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | - | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.8 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | - | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | PLANNED | - | not attested (planned) | - |
| SC.L2-3.13.9 | VPC network segmentation (subnetworks + firewalls + Cloud Armor) | - | nv012/all-covered/gcp_vpc_segmentation.json | 2a64f51ac186 | PLANNED | - | not attested (planned) | - |
| SI.L2-3.14.1 | GCP Security Command Center — vulnerability management | - | nv012/all-covered/gcp_scc_findings.json | 4472a35663ce | PLANNED | - | not attested (planned) | - |
| SI.L2-3.14.2 | CrowdStrike Falcon EDR — malware + endpoint integrity | - | nv012/all-covered/crowdstrike_edr.json | 78748c996698 | PLANNED | - | not attested (planned) | - |
| SI.L2-3.14.3 | Cloud Monitoring + Workspace Alert Center (security alert monitoring/response) | NV012 Affirming Official | nv012/all-covered/gcp_sc_si_monitoring.json | 3923ae07c201 | MET | machine | - | - |
| SI.L2-3.14.4 | CrowdStrike Falcon EDR — malware + endpoint integrity | - | nv012/all-covered/crowdstrike_edr.json | 78748c996698 | PLANNED | - | not attested (planned) | - |
| SI.L2-3.14.5 | GCP Security Command Center — vulnerability management | - | nv012/all-covered/gcp_scc_findings.json | 4472a35663ce | PLANNED | - | not attested (planned) | - |
| SI.L2-3.14.6 | Cloud Monitoring + Workspace Alert Center (security alert monitoring/response) | NV012 Affirming Official | nv012/all-covered/gcp_sc_si_monitoring.json | 3923ae07c201 | MET | machine | - | - |
| SI.L2-3.14.7 | CrowdStrike Falcon EDR — malware + endpoint integrity | - | nv012/all-covered/crowdstrike_edr.json | 78748c996698 | PLANNED | - | not attested (planned) | - |

## 4. Per-control detail

### AC.L2-3.1.1

**Statement.** Limit system access to authorized users, processes acting on behalf of authorized users, and devices (including other systems).

- Family: AC · Weight: 5 · POA&M-eligible: false
- Implementation: IAM groups + least-privilege role bindings for CUI access
- Verification method: oracle-iam-least-privilege

- Attestation: ATT-AC.L2-3.1.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.652581+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.2

**Statement.** Limit system access to the types of transactions and functions that authorized users are permitted to execute.

- Family: AC · Weight: 5 · POA&M-eligible: false
- Implementation: IAM groups + least-privilege role bindings for CUI access
- Verification method: oracle-iam-least-privilege

- Attestation: ATT-AC.L2-3.1.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.666202+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.3

**Statement.** Control the flow of CUI in accordance with approved authorizations.

- Family: AC · Weight: 1 · POA&M-eligible: true
- Implementation: Drive + Gmail DLP rules (control the flow of CUI)
- Verification method: oracle-drive-dlp-rules

- Attestation: ATT-AC.L2-3.1.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.680718+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AC.L2-3.1.5

**Statement.** Employ the principle of least privilege, including for specific security functions and privileged accounts.

- Family: AC · Weight: 3 · POA&M-eligible: false
- Implementation: IAM groups + least-privilege role bindings for CUI access
- Verification method: oracle-iam-least-privilege

- Attestation: ATT-AC.L2-3.1.5 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.693869+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AU.L2-3.3.1

**Statement.** Create and retain system audit logs and records to the extent needed to enable the monitoring, analysis, investigation, and reporting of unlawful or unauthorized system activity.

- Family: AU · Weight: 5 · POA&M-eligible: false
- Implementation: Workspace + GCP audit log export to retained Cloud Storage bucket
- Verification method: oracle-auditlog-export

- Attestation: ATT-AU.L2-3.3.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.707000+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AU.L2-3.3.2

**Statement.** Ensure that the actions of individual system users can be uniquely traced to those users, so they can be held accountable for their actions.

- Family: AU · Weight: 3 · POA&M-eligible: false
- Implementation: Workspace + GCP audit log export to retained Cloud Storage bucket
- Verification method: oracle-auditlog-export

- Attestation: ATT-AU.L2-3.3.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.720336+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### AU.L2-3.3.5

**Statement.** Correlate audit record review, analysis, and reporting processes for investigation and response to indications of unlawful, unauthorized, suspicious, or unusual activity.

- Family: AU · Weight: 5 · POA&M-eligible: false
- Implementation: Workspace + GCP audit log export to retained Cloud Storage bucket
- Verification method: oracle-auditlog-export

- Attestation: ATT-AU.L2-3.3.5 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.733429+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### CM.L2-3.4.1

**Statement.** Establish and maintain baseline configurations and inventories of organizational systems (including hardware, software, firmware, and documentation) throughout the respective system development life cycles.

- Family: CM · Weight: 5 · POA&M-eligible: false
- Implementation: Terraform baseline configuration + resource inventory (IaC)
- Verification method: oracle-terraform-baseline

- Attestation: ATT-CM.L2-3.4.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.746462+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### CM.L2-3.4.2

**Statement.** Establish and enforce security configuration settings for information technology products employed in organizational systems.

- Family: CM · Weight: 5 · POA&M-eligible: false
- Implementation: Terraform baseline configuration + resource inventory (IaC)
- Verification method: oracle-terraform-baseline

- Attestation: ATT-CM.L2-3.4.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.759923+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### CM.L2-3.4.6

**Statement.** Employ the principle of least functionality by configuring organizational systems to provide only essential capabilities.

- Family: CM · Weight: 5 · POA&M-eligible: false
- Implementation: Disable non-FedRAMP-authorized services for the CUI OU (least functionality)
- Verification method: oracle-restrict-service-usage

- Attestation: ATT-CM.L2-3.4.6 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.773366+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### CM.L2-3.4.7

**Statement.** Restrict, disable, or prevent the use of nonessential programs, functions, ports, protocols, and services.

- Family: CM · Weight: 5 · POA&M-eligible: false
- Implementation: Disable non-FedRAMP-authorized services for the CUI OU (least functionality)
- Verification method: oracle-restrict-service-usage

- Attestation: ATT-CM.L2-3.4.7 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.786299+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.2

**Statement.** Authenticate (or verify) the identities of users, processes, or devices, as a prerequisite to allowing access to organizational systems.

- Family: IA · Weight: 5 · POA&M-eligible: false
- Implementation: Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU
- Verification method: oracle-mfa-2sv-enforced

- Attestation: ATT-IA.L2-3.5.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.799295+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.3

**Statement.** Use multifactor authentication for local and network access to privileged accounts and for network access to non-privileged accounts.

- Family: IA · Weight: 5 · POA&M-eligible: false
- Implementation: Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU
- Verification method: oracle-mfa-2sv-enforced

- Attestation: ATT-IA.L2-3.5.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.812198+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### IA.L2-3.5.4

**Statement.** Employ replay-resistant authentication mechanisms for network access to privileged and non-privileged accounts.

- Family: IA · Weight: 1 · POA&M-eligible: true
- Implementation: Google Workspace 2-Step Verification (phishing-resistant) enforced on CUI OU
- Verification method: oracle-mfa-2sv-enforced

- Attestation: ATT-IA.L2-3.5.4 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.825228+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### PE.L2-3.10.1

**Statement.** Limit physical access to organizational systems, equipment, and the respective operating environments to authorized individuals.

- Family: PE · Weight: 5 · POA&M-eligible: false
- Implementation: CSP-inherited physical protection (Google IL4 data-center controls)
- Verification method: inherited:google-workspace-crm

- Attestation: ATT-PE.L2-3.10.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.838690+00:00
  - Adequacy assumption: Control satisfied by the cloud service provider and inherited.
  - Sufficiency justification: CSP shared-responsibility inheritance; no customer-side machine check applies.

### PE.L2-3.10.2

**Statement.** Protect and monitor the physical facility and support infrastructure for organizational systems.

- Family: PE · Weight: 5 · POA&M-eligible: false
- Implementation: CSP-inherited physical protection (Google IL4 data-center controls)
- Verification method: inherited:google-workspace-crm

- Attestation: ATT-PE.L2-3.10.2 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.852939+00:00
  - Adequacy assumption: Control satisfied by the cloud service provider and inherited.
  - Sufficiency justification: CSP shared-responsibility inheritance; no customer-side machine check applies.

### SC.L2-3.13.1

**Statement.** Monitor, control, and protect communications (i.e., information transmitted or received by organizational systems) at the external boundaries and key internal boundaries of organizational systems.

- Family: SC · Weight: 5 · POA&M-eligible: false
- Implementation: GCP Org Policy: US-only resource locations + restricted service usage
- Verification method: oracle-orgpolicy-us-residency

- Attestation: ATT-SC.L2-3.13.1 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.866066+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.10

**Statement.** Establish and manage cryptographic keys for cryptography employed in organizational systems.

- Family: SC · Weight: 1 · POA&M-eligible: true
- Implementation: Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto)
- Verification method: oracle-cmek-fips-keyring

- Attestation: ATT-SC.L2-3.13.10 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.879020+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.11

**Statement.** Employ FIPS-validated cryptography when used to protect the confidentiality of CUI.

- Family: SC · Weight: 5 · POA&M-eligible: false
- Implementation: Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto)
- Verification method: oracle-cmek-fips-keyring

- Attestation: ATT-SC.L2-3.13.11 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.892099+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SC.L2-3.13.16

**Statement.** Protect the confidentiality of CUI at rest.

- Family: SC · Weight: 1 · POA&M-eligible: true
- Implementation: Cloud KMS CMEK + Workspace CSE key management (FIPS-validated crypto)
- Verification method: oracle-cmek-fips-keyring

- Attestation: ATT-SC.L2-3.13.16 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.905367+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SI.L2-3.14.3

**Statement.** Monitor system security alerts and advisories and take action in response.

- Family: SI · Weight: 5 · POA&M-eligible: false
- Implementation: Cloud Monitoring + Workspace Alert Center (security alert monitoring/response)
- Verification method: oracle-monitoring-alerts

- Attestation: ATT-SI.L2-3.14.3 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.918238+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

### SI.L2-3.14.6

**Statement.** Monitor organizational systems, including inbound and outbound communications traffic, to detect attacks and indicators of potential attacks.

- Family: SI · Weight: 5 · POA&M-eligible: false
- Implementation: Cloud Monitoring + Workspace Alert Center (security alert monitoring/response)
- Verification method: oracle-monitoring-alerts

- Attestation: ATT-SI.L2-3.14.6 — **MET** by NV012 Affirming Official
  - Timestamp: 2026-07-08T18:24:37.931146+00:00
  - Adequacy assumption: Implementation reviewed against the provisioned configuration.
  - Sufficiency justification: Machine oracle + config evidence sufficient for the Phase-I mock run.

## 5. Colophon

| Layer | Named graph | Triples |
| --- | --- | --- |
| attestations | `http://dynamicalsystems.group/compliance-engine/attestations` | 464 |
| audit | `http://dynamicalsystems.group/compliance-engine/audit` | 1138 |
| evidence | `http://dynamicalsystems.group/compliance-engine/evidence` | 578 |
| ontology | `http://dynamicalsystems.group/compliance-engine/ontology` | 1057 |
| order | `http://dynamicalsystems.group/compliance-engine/order` | 150 |
| plan | `http://dynamicalsystems.group/compliance-engine/plan` | 0 |
| plan_execution | `http://dynamicalsystems.group/compliance-engine/plan-execution` | 250 |
| structural | `http://dynamicalsystems.group/compliance-engine/structural` | 711 |

Dataset SHA-256: `5bfb0f7f4967a0b96a0d8462799e6047ea2ee95c63fb5b0757f7a09071df2041`

Document date (max prov:generatedAtTime): 2026-07-08T18:24:37.931146+00:00

SPRS summary: score 110 (Final); 20 MET-by-machine / 2 MET-by-human-only; contradictions: 0.

Artifact hashes (BOM): 37

- `00693338fb29c30f553937069f1ec3b7285cd4f02a089d18e8d029522c40e3ea`
- `0ed2eedf228cfa815e80d241f2bfd62368616ba6ef2ee40ef91c317dc9e8c4a7`
- `10bee86a3f6d301f24538c1caa533a0fcd7121faa529c0c9721c28497e23fae1`
- `2690e5e9a376ed929cedfc9ae51b2bc7c2aa600c5347d63247036b2a104842a3`
- `2a64f51ac186a4af034db0ab9b5c56f00c86587dc4a60f455a2f86688c806c3c`
- `2d9165ac19f597a87ad36a01ebd58f042cdea08287d3b6a8325ad1297d03daba`
- `385f07ca2e587097c8fdb83a7175af8d073717180b8e9db3670d7e5bc346897e`
- `3923ae07c2016872f227b66e10a806b8754ae8e64e8126289dc50c4179830c49`
- `3c4af60bc14480071afa3b9486fa7514484a9b6dcc77846d325e57f2955d47ac`
- `4472a35663cebbc9ec59579789d76db8ebd76fca2a5942cf5c5bc891e5af8583`
- `45b70ef22dcb69f47a8943271206d860d8f770af1549614893f972302241af0d`
- `4bba2d0adcbb48ec02d9b82a9ec4c9655c13c20b39c35136630de23b08f32f12`
- `52eb61a61772b7878d6db0b96ae3441d5f1bb66f0f1bf5cbc7565481acf23cde`
- `594252df359f78bd131ed2d4944c62907b779167f547596cc320378c69406a69`
- `59a6617d68a550cd248b61f625156d0e6b71c6c4b69c989419766456f5dc833f`
- `5c41b30cc0ef81407debf3fb91b9912a1a1da06de9752eccb96dd597af1d96a0`
- `5f8e7ef2f8ffc747ece0831bf33066eb499c1f12b2c5f5bb7e8768ce1fe921fa`
- `6549f40b7941e00ae547750979c6a06ca36b640939dae098981394e4248dd3be`
- `6c69bdddaea378c058139148d6865c4cba32f0b00b86c9d24f2ba2aafb2b97c1`
- `70d573b23771a8c3d14ec76cd557a37722ca3fc8ca97246dce7bfc454d70bcf7`
- `753946a895a2cb9963971ad499cfb0efe07ee3ad06f61d060d5035596421c853`
- `75ad3c7ecdfadfc75a9b15354b9cd3f31a2bd6127a30dc91f1a4c5cc8f831c47`
- `78748c9966987bfedd68a2453a0eca06763c63d93df1a5ee3db598c507c498f4`
- `82e5d2082cc9fb90786e3aeca299c3331a8cfbdb2e486a832c257cb6bd10d9c4`
- `8959f24468b8f262147051cfa413d1beebea65bd15144dcb01afd7b32689d86e`
- `9c2e2dd99b27429246d159b75a6a7bbc9b0b72aea0aceec114825f5729d3fdb7`
- `a911dd6a6276701fffb7957d3a0dcbf8618bd137b391f2c8636734eebdcb3d55`
- `b5e9a6da66f8d13b6a81113c09cf7f0d704b9d621a6300aeee0d3df2e3e7ca29`
- `b6c67e930e8a45acefac192bf87956bcf8a39faf35630792a4568daa2cc354bc`
- `cdad6fb17f7cb53728276bb24de654c87b6725e31b9bd731efa7769234afbc85`
- `ce20d3b1b76ec95c37328a20ddc89ff47cf667bcbb417c0757a43f8e110581b8`
- `d0cea0ecf9b3ce6dc1ef4d2466dd8575067e9a45c0deae9b3d0f704ee46444a4`
- `d51b18159d04d6edf398258392cbd60434bf1609a8b89b6ee5eb5b08a47ffa52`
- `dbbec27575687acd6dd7f477539165531ff5ed1a7bff42d1f53983e165dd4584`
- `df6706e07d448f632c0f7304eb2d1ce5d78b55f7908fe70eb1535809d42df746`
- `e1bec3138a1ea59f82170a1bb8b5be92f8efcf66e6345736c2651501c258763a`
- `ea589346e8b68f5865c4abe045628dce5b9ae61a03a92585b1a082fd59c77982`

**NON-EVIDENTIARY stamp:** statuses present — mock. Not a submittable SSP (mock evidence).

Rebuild and drift-check:

```bash
uv run python -m documents.ssp build --input output/engine.trig
uv run python -m documents.ssp build --check
```
