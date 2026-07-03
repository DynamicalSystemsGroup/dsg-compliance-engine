# Audit Management Procedure

**Organization:** Dynamical Systems Group, LLC
**Document ID:** POL-AU-001
**Version:** 1.0
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies To:** All in-scope CUI systems (Google Workspace Enterprise Plus, GCP Assured Workloads IL4)

## Purpose

This procedure defines how Dynamical Systems Group (DSG) generates, reviews, and reports on
audit records for systems that store, process, or transmit Controlled Unclassified Information
(CUI) under DFARS 252.204-7012 and ITAR-controlled SBIR contracts. It implements the following
NIST SP 800-171 Rev.2 controls:

- **AU.L2-3.3.3** — Review and update logged events.
- **AU.L2-3.3.6** — Provide audit record reduction and report generation to support on-demand
  analysis and reporting.

## Logged Event Types

The following event categories are logged across in-scope systems (Google Workspace Admin
audit logs, GCP Cloud Audit Logs, and endpoint agent telemetry):

1. **Authentication events** — successful and failed logins, MFA challenges, session
   termination, SSO assertions.
2. **Privilege use** — role changes, super-admin actions, `sudo` / break-glass invocations,
   IAM policy edits in GCP Assured Workloads.
3. **Configuration changes** — changes to Workspace security settings, DLP rules, sharing
   controls, GCP organization policies, VPC-SC perimeter modifications.
4. **Data access** — access to CUI-labeled Drive items, exports, downloads, and reads of
   IL4 storage buckets containing CUI.

## Review Cadence

- **Weekly:** The Security Officer reviews the aggregated log-reduction dashboard produced
  by the SIEM pipeline (Chronicle / Cloud Logging sink).
- **Monthly:** A written Sample Log Review Report is filed to
  `documents/evidence/audit/YYYY-MM-log-review.md`.
- **Annually:** The event-type list above is reviewed against 800-171 Rev.2 §3.3.3 and
  updated when systems, threats, or contract requirements change.

## Audit Reduction and Reporting

Log reduction is performed by scheduled queries over Cloud Logging sinks; reports are
generated on demand by the Security Officer and made available to the Affirming Official
and government auditors. The most recent sample report is referenced in
`documents/evidence/audit/latest-log-review.md`.

## Attestation

This procedure is attested to by **Role_SecurityOfficer** (Sayer Tindall, Affirming Official)
for Dynamical Systems Group, LLC.

- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
