# System Maintenance Policy

**Organization:** Dynamical Systems Group, LLC
**Document ID:** POL-MA-001
**Version:** 1.0
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies To:** All maintenance activities performed on information systems that process, store, or transmit Controlled Unclassified Information (CUI).

## 1. Purpose

This policy governs system maintenance activities at Dynamical Systems Group ("DSG") to ensure that both routine and non-routine maintenance is performed by authorized personnel using approved tools and does not compromise CUI. It implements NIST SP 800-171 Rev.2 controls MA.L2-3.7.1, MA.L2-3.7.2, MA.L2-3.7.3, MA.L2-3.7.4, and MA.L2-3.7.6 for CMMC Level 2.

## 2. Scope

Because DSG is a fully remote small business, "systems" in this policy refers primarily to endpoint hardware issued to personnel, YubiKeys, and any physical media temporarily used for out-of-band backups. Cloud infrastructure maintenance (Google Workspace, GCP Assured Workloads IL4) is governed by provider FedRAMP High controls and DSG's cloud administration procedures.

## 3. Approved Maintenance and Tooling (MA.L2-3.7.1, MA.L2-3.7.2)

DSG shall maintain and review at least annually:

- **Approved Maintenance Personnel List** — authorized DSG staff and vetted third-party technicians permitted to perform maintenance on CUI-bearing endpoints.
- **Approved Maintenance Tool Inventory** — hardware and software tools (diagnostic utilities, imaging tools, hardware repair kits) approved for use during maintenance.

Only listed personnel using listed tools may perform maintenance. Introduction of a new tool requires IT Administrator approval and inventory update prior to use.

## 4. Off-Site Maintenance and CUI Sanitization (MA.L2-3.7.2)

Before any equipment leaves DSG control for off-site maintenance, repair, or warranty service, the equipment shall be sanitized of CUI per the Media Protection Policy (POL-MP-001), using the NIST SP 800-88 Rev.1 method appropriate to the media type. Sanitization is recorded in the maintenance log and verified by a second authorized person.

If sanitization is not feasible (e.g., the fault prevents disk access), the storage component shall be removed and retained on-site for destruction, and only non-storage components shipped off-site.

## 5. Diagnostic Media Scan (MA.L2-3.7.3)

Any diagnostic or test media (USB drives, bootable images, vendor utilities) introduced to a CUI system shall be scanned for malicious code on an isolated, non-CUI workstation prior to use. Media that fails scanning is quarantined and destroyed.

## 6. Sanitization Prior to Removal (MA.L2-3.7.3)

Equipment removed from service, transferred, or disposed of shall be sanitized in accordance with POL-MP-001 before leaving DSG control. Records of sanitization are retained for three (3) years.

## 7. Verification of Controls After Maintenance (MA.L2-3.7.4)

Following maintenance activities, the IT Administrator shall verify that security controls (disk encryption, MDM enrollment, endpoint protection, MFA, screen lock) remain configured as required before the device is returned to production use.

## 8. Visitor and Escort Policy for Maintenance Access (MA.L2-3.7.6)

Because DSG has no physical office, "maintenance access" is exclusively remote or shipping-based:

- Remote screen-share sessions with vendor support shall be conducted from a non-CUI environment; the DSG operator remains present and controls the session for its full duration ("virtual escort").
- Vendor personnel are never granted independent access to a CUI-bearing system. Sessions are logged.
- For shipping-based service, chain-of-custody is documented from dispatch to return.

## 9. Roles and Responsibilities

- **Operations Lead:** Maintains personnel/tool lists, approves off-site maintenance, records chain-of-custody.
- **IT Administrator:** Performs post-maintenance control verification and manages diagnostic media scanning.
- **Affirming Official:** Attests to policy implementation.

## Attestation

This policy is attested by **Role_OPs** (Operations Lead) as the Affirming Official for maintenance controls at Dynamical Systems Group.

- **Affirming Official:** Sayer Tindall
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
