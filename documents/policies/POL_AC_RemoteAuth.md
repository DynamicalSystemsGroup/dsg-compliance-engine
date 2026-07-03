# Remote Access Authorization (SSP Appendix)

**Organization:** Dynamical Systems Group, LLC
**Document ID:** POL-AC-001
**Version:** 1.0
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies To:** All DSG personnel and contractors working remotely on CUI systems.

## Purpose

Dynamical Systems Group (DSG) operates as a fully remote organization (~10 personnel).
Nearly all access to CUI systems is therefore "remote access" as defined by NIST SP 800-171
Rev.2. This appendix to the System Security Plan (SSP) documents how the following controls
are met:

- **AC.L2-3.1.15** — Authorize remote execution of privileged commands and remote access to
  security-relevant information.
- **AC.L2-3.1.21** — Limit use of portable storage devices on external systems.
- **AC.L2-3.1.22** — Control CUI posted or processed on publicly accessible systems.

## AC.L2-3.1.15 — Privileged Remote Execution

Remote execution of privileged commands (Workspace super-admin actions, GCP org / folder /
project owner or editor operations against the IL4 folder, and any `sudo` on hardened
endpoints) is permitted **only** when the following are all true:

1. The individual holds a role listed in the SSP's Access Control Matrix.
2. Written authorization exists in `documents/authorizations/remote-privileged/` and is
   signed by the Affirming Official.
3. The session originates from a managed endpoint enrolled in Workspace endpoint management
   with device policies enforced (screen lock, disk encryption, current OS).

Access to security-relevant information (audit logs, IAM policies, key material) follows
the same authorization requirement.

## AC.L2-3.1.21 — Portable Storage on External Systems

Use of DSG-owned portable storage devices (USB drives, external SSDs) on external, non-DSG
systems is **prohibited**. Personnel needing to move CUI between DSG-managed environments
do so via Google Drive containers inside the IL4-aligned tenant. Any exception requires
written pre-approval by the Security Officer and is logged in
`documents/exceptions/portable-storage/`.

## AC.L2-3.1.22 — CUI on Publicly Accessible Systems

CUI must never be posted to publicly accessible systems (public websites, public GCP
buckets, public Drive links, public GitHub repositories, public Slack workspaces, or any
third-party SaaS not covered by the SSP). Public sharing is disabled by default at the
Workspace and GCP org-policy level. Content owners are responsible for verifying that
material intended for public release has been cleared through the DFARS/ITAR review path
before publication.

## Attestation

This appendix is attested to by **Role_SecurityOfficer** (Sayer Tindall, Affirming Official)
for Dynamical Systems Group, LLC.

- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
