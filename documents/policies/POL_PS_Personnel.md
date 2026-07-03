# Personnel Security Policy

**Organization:** Dynamical Systems Group, LLC
**Document ID:** POL-PS-001
**Version:** 1.0
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies To:** All employees, contractors, and authorized personnel with access to Controlled Unclassified Information (CUI).

## 1. Purpose

This policy establishes personnel security requirements for Dynamical Systems Group ("DSG"), a fully remote small business (~10 personnel) executing DFARS/ITAR SBIR contracts. It implements NIST SP 800-171 Rev.2 controls PS.L2-3.9.1 and PS.L2-3.9.2 as required for CMMC Level 2.

## 2. Scope

This policy covers all individuals granted logical or physical access to systems that process, store, or transmit CUI, including Google Workspace Enterprise Plus tenants and GCP Assured Workloads (IL4) environments operated by DSG.

## 3. Personnel Screening (PS.L2-3.9.1)

Prior to authorizing access to systems containing CUI, DSG shall:

- Verify U.S. person status where required by ITAR (22 CFR 120.62).
- Complete a background investigation appropriate to role sensitivity, including identity verification, employment history, education verification, and criminal history check.
- Require signed acknowledgment of the DSG Acceptable Use Policy and CUI Handling Acknowledgment.
- Re-screen personnel every five (5) years or upon a material change in role.

Screening results are retained by the Operations Lead in the HR records system for the duration of employment plus three (3) years.

## 4. Termination and Transfer (PS.L2-3.9.2)

Upon separation, role change, or extended leave, the following actions shall be completed **within 24 hours** of the effective separation time:

1. **Account revocation** — Disable Google Workspace, GCP, GitHub, and all federated SSO identities. Revoke active OAuth grants and refresh tokens.
2. **Credential rotation** — Rotate any shared secrets, service account keys, or API tokens the individual had access to.
3. **MFA/device deregistration** — Remove enrolled hardware keys, TOTP registrations, and managed devices from MDM.
4. **Badge and physical access** — Recover any issued physical access credentials; notify colocation providers if applicable.
5. **Equipment recovery** — Coordinate return of laptops, YubiKeys, and any other DSG-issued equipment via prepaid shipping; confirm receipt and initiate wipe.
6. **Access review** — Operations Lead confirms full revocation in the offboarding checklist and files the record.

Transfers between projects follow the same review process, scoped to access changes rather than full revocation.

## 5. Roles and Responsibilities

- **Operations Lead:** Executes screening, maintains records, and runs the offboarding checklist.
- **IT Administrator:** Performs technical revocation and credential rotation actions.
- **Affirming Official:** Attests to policy implementation and effectiveness.

## Attestation

This policy is attested by **Role_OPs** (Operations Lead) as the Affirming Official for personnel security controls at Dynamical Systems Group.

- **Affirming Official:** Sayer Tindall
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
