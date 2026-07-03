# Separation of Duties Policy

**Organization:** Dynamical Systems Group, LLC
**Document ID:** POL-AC-SoD
**Version:** 1.0
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies To:** All personnel with privileged or change-approval responsibilities over CUI systems

## 1. Purpose

This policy defines the separation of duties (SoD) required by **AC.L2-3.1.4** — "Separate the duties of individuals to reduce the risk of malevolent activity without collusion." It ensures that no single individual at Dynamical Systems Group ("DSG") can both authorize and execute a sensitive change to CUI-bearing systems.

## 2. Scope

Applies to all changes to production infrastructure hosting CUI, including Google Workspace Enterprise Plus admin configuration, GCP Assured Workloads (IL4) projects, source-code repositories that build CUI-processing artifacts, and IAM role bindings.

## 3. Role Definitions and RACI Matrix

| Activity                                   | Affirming Official | Security Officer | IT Administrator | Engineer |
|--------------------------------------------|--------------------|------------------|------------------|----------|
| Approve new user provisioning              | A                  | R                | C                | I        |
| Execute user provisioning                  | I                  | C                | R                | I        |
| Approve production code merge              | A                  | R                | I                | C        |
| Execute production code merge              | I                  | C                | I                | R        |
| Approve IAM role change (GCP/Workspace)    | A                  | R                | C                | I        |
| Execute IAM role change                    | I                  | C                | R                | I        |
| Approve firewall / VPC change              | A                  | R                | C                | C        |
| Execute firewall / VPC change              | I                  | C                | R                | I        |

Legend: **R**esponsible, **A**ccountable, **C**onsulted, **I**nformed.

No role appears as both "A" (approver) and "R" (executor) in the same row. Where staffing forces overlap, a compensating peer review is required and recorded.

## 4. Technical Enforcement

- **GitHub branch protection** on the `main` branch of every CUI-relevant repository requires at least one Required Reviewer distinct from the pull-request author. Force-push and direct-commit are disabled.
- **CODEOWNERS** designates the Security Officer as a required reviewer for changes to `iam/`, `terraform/`, `documents/policies/`, and any file under `.github/`.
- **Google Workspace super-admin actions** require a second-factor confirmation from an admin account distinct from the initiating admin.
- **GCP** privileged role grants (e.g., `roles/owner`, `roles/iam.securityAdmin`) require an approval workflow via Access Approval before taking effect.

## 5. Exceptions and Break-Glass

Break-glass credentials are held in a sealed offline record accessible only to the Affirming Official. Any use is logged and reviewed within 24 hours by the Security Officer.

## 6. Review

The RACI matrix and technical enforcement configuration are reviewed at least annually and whenever organizational headcount or role structure changes.

## Attestation

I, the undersigned Affirming Official, attest that this policy is in effect for Dynamical Systems Group, LLC and reflects the organization's implementation of AC.L2-3.1.4.

- **Required Role:** Role_SecurityOfficer
- **Affirming Official:** Sayer Tindall
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
