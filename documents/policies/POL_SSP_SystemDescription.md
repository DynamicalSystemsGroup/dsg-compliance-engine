# System Security Plan — System Description Supplement

**Organization:** Dynamical Systems Group, LLC (DSG)
**Document ID:** POL_SSP_SystemDescription
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies to CMMC L2 Control:** CA.L2-3.12.4 (NIST SP 800-171 Rev.2 §3.12.4)

## 1. Purpose

This document supplements the DSG System Security Plan (SSP) by describing the boundary, components, and information flows of the Controlled Unclassified Information (CUI) environment used to execute DFARS/ITAR SBIR contracts. It exists to satisfy CA.L2-3.12.4, which requires that a system security plan describing the system boundary, environment of operation, security requirements, and relationships with or connections to other systems be developed, documented, and periodically updated.

## 2. System Overview

- **System Name:** DSG CUI Enclave
- **Mission:** Storage, processing, and transmission of CUI generated under DFARS 252.204-7012 and ITAR-controlled SBIR programs.
- **Organization Size:** Approximately 10 personnel, fully remote (continental United States, U.S. Persons only).
- **Operating Model:** Cloud-only. No on-premises infrastructure holds CUI.

## 3. Authorized Users

- Full-time employees who have completed CUI handling training and executed the DSG Acceptable Use Agreement.
- Access is provisioned by the Security Officer and reviewed quarterly. No subcontractors, interns, or non-U.S. Persons are authorized to access the enclave.

## 4. System Components

- **Google Workspace Enterprise Plus** with Assured Controls, configured for U.S. data regions and CJIS/ITAR-compatible controls. Provides email, Drive, Docs, Meet, and identity.
- **Google Cloud Platform — Assured Workloads (IL4)** compartment, providing compute, storage (Cloud Storage buckets tagged `cui-*`), and BigQuery for analysis workloads.
- **Endpoint fleet:** Company-managed laptops enrolled in Google endpoint management with FileVault/BitLocker, screen lock, and OS patch enforcement.
- **Identity:** Google Workspace SSO with hardware-key-backed MFA required for all human accounts.

## 5. Data Flows

1. CUI is received from Government contracting officers or prime contractors via DoD SAFE or Workspace email under DLP rules that restrict external sharing of `cui-*` labeled content.
2. CUI is stored in labeled Drive folders or Assured Workloads Cloud Storage buckets. All movement between Workspace and GCP occurs over Google-internal transport under the Assured Workloads boundary.
3. Derived artifacts (reports, deliverables) are returned to the Government via DoD SAFE.

## 6. Interconnections

The DSG CUI Enclave has no persistent system-to-system interconnections with external non-Federal systems. Ad-hoc interconnections for a specific award are documented in a per-contract Interconnection Security Agreement (ISA) appendix and referenced from this SSP.

## 7. Physical and Network Boundaries

- **Physical:** Google-operated U.S. data centers within Assured Workloads scope. No DSG-operated facilities process CUI.
- **Logical:** The enclave boundary is the union of the DSG Workspace tenant and the Assured Workloads folder, joined by managed endpoints. Traffic to and from the boundary is authenticated via SSO and inspected via Workspace DLP and VPC Service Controls.

## 8. Maintenance

This description is reviewed at least annually and whenever a material change to components, users, or data flows occurs.

## Attestation

The undersigned Affirming Official attests that the system description above accurately reflects the DSG CUI Enclave as of the effective date and satisfies the documentation requirement of CA.L2-3.12.4.

- **Required Role:** Role_AffirmingOfficial
- **Affirming Official:** Sayer Tindall
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
