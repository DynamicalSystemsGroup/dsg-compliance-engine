# Security Engineering Principles

**Organization:** Dynamical Systems Group, LLC
**Document ID:** POL-SC-001
**Version:** 1.0
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies To:** Design and modification of any DSG system that handles CUI.

## Purpose

This policy establishes the security engineering principles applied to the design, acquisition,
configuration, and modification of systems that store, process, or transmit CUI at Dynamical
Systems Group (DSG). It implements NIST SP 800-171 Rev.2 control:

- **SC.L2-3.13.2** — Employ architectural designs, software development techniques, and
  systems engineering principles that promote effective information security within
  organizational systems.

## Baseline Reference

DSG adopts **NIST SP 800-160 Vol.1 (Systems Security Engineering)** as its baseline framework.
Design choices for the Google Workspace Enterprise Plus tenant, the GCP Assured Workloads IL4
folder, and any bespoke SBIR deliverables are evaluated against the principles below before
being approved by the Security Officer.

## Principles

1. **Least Privilege.** Human and service identities are granted only the minimum permissions
   required. IAM roles are scoped to specific projects; standing super-admin access is
   prohibited outside break-glass procedures.
2. **Defense in Depth.** Overlapping controls at identity (Google SSO + MFA), network
   (VPC-SC perimeters), workload (Binary Authorization, OS Login), and data (CMEK, DLP) layers.
3. **Fail-Secure Defaults.** New GCP projects inherit deny-by-default org policies; new
   Workspace groups default to internal-only sharing. Errors in policy evaluation deny access.
4. **Separation of Duties.** Personnel who develop or deploy code do not also approve
   IAM policy changes in the IL4 folder; approval and execution are split across roles.
5. **Minimize Attack Surface.** Unused Workspace apps, GCP APIs, and third-party marketplace
   add-ons are disabled; public IPs and public buckets are prohibited by org policy.

## Application

Any new system, integration, or material configuration change is documented in a short
design note (`documents/design/`) that explicitly maps the change to each principle above
and to the 800-160 Vol.1 stages of *problem*, *solution*, and *trustworthiness*.

## Attestation

This policy is attested to by **Role_SecurityOfficer** (Sayer Tindall, Affirming Official)
for Dynamical Systems Group, LLC.

- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
