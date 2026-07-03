# Media Protection Policy

**Organization:** Dynamical Systems Group, LLC
**Document ID:** POL-MP-001
**Version:** 1.0
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies To:** All digital and non-digital media that contain Controlled Unclassified Information (CUI).

## 1. Purpose

This policy establishes handling, labeling, storage, transport, sanitization, and disposal requirements for media containing CUI at Dynamical Systems Group ("DSG"). It implements NIST SP 800-171 Rev.2 controls MP.L2-3.8.1, MP.L2-3.8.2, MP.L2-3.8.3, MP.L2-3.8.4, MP.L2-3.8.5, MP.L2-3.8.6, MP.L2-3.8.8, and MP.L2-3.8.9 for CMMC Level 2.

## 2. Scope

DSG's primary CUI repositories are Google Workspace Enterprise Plus and GCP Assured Workloads (IL4). Physical media within scope includes endpoint SSDs, YubiKeys, and any transient media used for backup, transfer, or maintenance.

## 3. CUI Marking and Labeling (MP.L2-3.8.4)

All media (digital and non-digital) containing CUI shall be marked in accordance with **NARA 32 CFR Part 2002** and the CUI Registry:

- Digital documents receive a CUI banner marking at the top and bottom of each page and CUI portion markings where required by the contract.
- Physical media receive an external label reading "CONTROLLED" and, where applicable, the CUI category (e.g., "CUI//SP-EXPT" for ITAR-controlled export data).
- Removable media additionally include the owner, date created, and destruction due date.

## 4. Physical Access Controls and Storage (MP.L2-3.8.1, MP.L2-3.8.2)

Physical media containing CUI shall be:

- Stored in a locked container (safe or lockbox) at the assigned custodian's residence when not in active use.
- Accessed only by personnel on the CUI Access Roster maintained by the Operations Lead.
- Never left unattended in vehicles, coworking spaces, or shared residences.

Digital access to CUI in Google Workspace and GCP is controlled via SSO, phishing-resistant MFA, and role-based IAM.

## 5. Transport and Accountability (MP.L2-3.8.5, MP.L2-3.8.6)

- Media containing CUI transported outside a controlled area shall be encrypted using FIPS 140-3 validated cryptography (e.g., BitLocker with a FIPS-mode boot, or LUKS with an approved cipher).
- Transport is logged in the Media Transport Log, including sender, recipient, tracking number, encryption method, and receipt confirmation.
- Physical shipment uses a bonded courier with chain-of-custody documentation.

## 6. Portable Storage Prohibition (MP.L2-3.8.8)

Use of personally owned or unauthorized portable storage devices (USB drives, external HDDs, SD cards) on DSG systems is **prohibited**. Endpoint policy blocks unrecognized removable media by default. Where a business need requires portable storage, an exception is granted in writing by the IT Administrator, and only DSG-issued, encrypted, inventoried devices may be used.

## 7. Sanitization and Disposal (MP.L2-3.8.3)

Media sanitization follows **NIST SP 800-88 Rev.1** guidance, selecting the method appropriate to media type and confidentiality impact:

- **Clear** — logical techniques (e.g., overwrite) for media being reused within DSG at the same or lower classification.
- **Purge** — cryptographic erase or vendor-supported secure erase for media leaving DSG control but not destroyed.
- **Destroy** — physical destruction (shredding, disintegration) for end-of-life media or when Clear/Purge is infeasible. Destruction is performed by an NSA/CSS-listed vendor or on-site with a documented method.

A Certificate of Sanitization or Destruction is recorded for each item and retained for three (3) years.

## 8. Backup Confidentiality (MP.L2-3.8.9)

Backups of CUI (including exports from Google Workspace and GCP) shall be encrypted at rest using FIPS 140-3 validated cryptography, stored within DSG's Assured Workloads (IL4) environment, and access-controlled to backup administrators only. Backup keys are managed in Cloud KMS with separation of duties from backup operators.

## 9. Media Inventory Log

The Operations Lead maintains a Media Inventory Log recording each item of physical media containing CUI: unique ID, media type, CUI category, custodian, date issued, encryption status, and current disposition. The log is reviewed quarterly.

## 10. Roles and Responsibilities

- **Operations Lead:** Maintains inventory, transport, and sanitization records.
- **IT Administrator:** Enforces removable-media controls and manages encryption keys.
- **All Personnel:** Follow marking, storage, and transport requirements.

## Attestation

This policy is attested by **Role_OPs** (Operations Lead) as the Affirming Official for media protection controls at Dynamical Systems Group.

- **Affirming Official:** Sayer Tindall
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
