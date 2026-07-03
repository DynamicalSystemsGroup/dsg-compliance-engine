# Security Assessment and Continuous Monitoring Policy

**Organization:** Dynamical Systems Group, LLC
**Document ID:** POL-CA-Monitoring
**Version:** 1.0
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies To:** All CUI-processing systems and the personnel who operate them

## 1. Purpose

This policy establishes the security assessment and continuous monitoring program for Dynamical Systems Group ("DSG"). It implements the following NIST SP 800-171 Rev. 2 requirements:

- **CA.L2-3.12.1** — Periodically assess the security controls in organizational systems to determine if the controls are effective in their application.
- **CA.L2-3.12.2** — Develop and implement plans of action designed to correct deficiencies and reduce or eliminate vulnerabilities in organizational systems.
- **CA.L2-3.12.3** — Monitor security controls on an ongoing basis to ensure the continued effectiveness of the controls.

## 2. What Is Monitored

- **Authentication events** — Google Workspace login audit log and GCP Cloud Identity events (successful and failed sign-ins, MFA challenges, session revocations).
- **Configuration drift** — Terraform plan output on the CUI infrastructure repository, run daily against the deployed GCP Assured Workloads (IL4) state.
- **Cloud logs** — GCP Cloud Audit Logs (Admin Activity, Data Access, System Event) and VPC Flow Logs, streamed to a dedicated Cloud Logging sink.
- **Endpoint posture** — Managed Chromebook and macOS fleet status via Google Workspace Endpoint Management.
- **Source-code integrity** — GitHub branch-protection and required-review status on CUI repositories.

## 3. Monitoring Cadence

- **Daily (automated):** Log ingestion, alerting rules, Terraform drift detection, and dependency vulnerability scans run automatically. High-severity alerts page the Security Officer.
- **Weekly (human review):** The Security Officer reviews the aggregated dashboard covering authentication anomalies, drift findings, and open alerts. Findings are recorded in the monitoring log.
- **Monthly:** Access recertification for privileged roles.
- **Annually:** Full self-assessment of all NIST SP 800-171 Rev. 2 controls using this compliance engine, producing an SSP delta and an updated POA&M.

## 4. Roles

- **Security Officer** — owns the weekly review, triages alerts, and maintains the POA&M.
- **IT Administrator** — remediates configuration and endpoint findings.
- **Affirming Official** — reviews the annual self-assessment output and attests to the SSP.

## 5. Annual Self-Assessment

The annual self-assessment is scheduled each June, culminating in an updated System Security Plan (SSP) and POA&M by 30 June. The compliance engine in this repository is the system of record for control status, evidence, and attestation.

## 6. Plan of Action and Milestones (POA&M)

Any deficiency identified through monitoring, assessment, or third-party audit is recorded in the POA&M with:

1. Control ID and finding description.
2. Risk rating and interim mitigation.
3. Named remediation owner.
4. Target closure date (not to exceed 180 days for High findings).
5. Evidence link on closure.

The POA&M is reviewed at each weekly monitoring session and reported to the Affirming Official monthly.

## Attestation

I, the undersigned Affirming Official, attest that this policy is in effect for Dynamical Systems Group, LLC and reflects the organization's implementation of CA.L2-3.12.1, CA.L2-3.12.2, and CA.L2-3.12.3.

- **Required Role:** Role_SecurityOfficer
- **Affirming Official:** Sayer Tindall
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
