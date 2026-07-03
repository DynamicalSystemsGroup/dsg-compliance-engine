# Configuration Management Policy

**Organization:** Dynamical Systems Group, LLC
**Document ID:** POL-CM-001
**Version:** 1.0
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies To:** All information systems that process, store, or transmit Controlled Unclassified Information (CUI).

## 1. Purpose

This policy establishes configuration management requirements for Dynamical Systems Group ("DSG") to ensure that changes to CUI-bearing systems are analyzed for security impact before implementation and that user-installed software is controlled. It implements NIST SP 800-171 Rev.2 control CM.L2-3.4.4 for CMMC Level 2.

## 2. Scope

This policy applies to Google Workspace Enterprise Plus configuration, GCP Assured Workloads (IL4) infrastructure-as-code, endpoint MDM baselines, and any application repository whose deployment can affect CUI confidentiality, integrity, or availability.

## 3. Security Impact Analysis (CM.L2-3.4.4)

Prior to implementing any configuration change to a CUI system, the change proposer shall complete a Security Impact Analysis (SIA) covering:

- **Change description** — the specific configuration, resource, or code being modified.
- **Affected controls** — which NIST SP 800-171 Rev.2 controls the change touches.
- **Threat surface delta** — new ingress points, permission grants, data flows, or trust boundaries introduced.
- **Rollback plan** — how the change is reverted if adverse impact is detected.
- **Testing evidence** — results from non-production validation.

The SIA is recorded in the pull request description for code changes, or in the Change Log ticket for console-driven changes.

## 4. Change Enforcement via GitHub Branch Protection

For all infrastructure-as-code and application repositories:

- The `main` branch is protected. Direct pushes are prohibited.
- All changes require a pull request with at least one approving review from a code owner listed in `CODEOWNERS`.
- Required status checks (CI, security scans, IaC policy checks) must pass before merge.
- Force-pushes and branch deletions are disabled on protected branches.
- Merge commits are signed; unsigned commits are rejected.

This enforcement ensures the SIA is documented and reviewed prior to the change taking effect.

## 5. User-Installed Software

Users shall not install software on DSG-managed endpoints outside of the approved software catalog without prior authorization. The approval process is:

1. User submits a software request ticket including business justification, vendor, version, and data classification handled by the software.
2. IT Administrator evaluates against the allowlist, license compliance, and security posture (SBOM/CVE review).
3. Approved software is added to the MDM-managed catalog and deployed via the endpoint management tool; ad-hoc installations are blocked by policy.
4. Approvals are reviewed quarterly and revoked when no longer needed.

## 6. Roles and Responsibilities

- **IT Administrator:** Maintains the software catalog, reviews SIAs, and configures branch protection.
- **Engineering Lead:** Ensures repositories follow CODEOWNERS and required-review policy.
- **Affirming Official:** Attests to policy implementation.

## Attestation

This policy is attested by **Role_ITAdmin** (IT Administrator) as the Affirming Official for configuration management controls at Dynamical Systems Group.

- **Affirming Official:** Sayer Tindall
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
