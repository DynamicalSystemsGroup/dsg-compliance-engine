# Security Awareness and Training Policy

**Organization:** Dynamical Systems Group, LLC (DSG)
**Document ID:** POL_AT_Training
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies to CMMC L2 Controls:** AT.L2-3.2.1, AT.L2-3.2.2, AT.L2-3.2.3 (NIST SP 800-171 Rev.2 §3.2.1–§3.2.3)

## 1. Purpose

This policy establishes DSG's annual security awareness and training program covering all personnel with access to the DSG CUI Enclave. It satisfies:

- **AT.L2-3.2.1** — ensure managers, system administrators, and users are made aware of security risks associated with their activities.
- **AT.L2-3.2.2** — ensure personnel are trained to carry out their assigned information-security-related duties.
- **AT.L2-3.2.3** — provide security awareness training on recognizing and reporting insider threats.

## 2. Scope

All DSG employees and any authorized long-term contractors with access to Workspace, GCP Assured Workloads, or managed endpoints.

## 3. Baseline Curriculum (All Personnel, Annual)

Each authorized user completes the following modules within 30 days of onboarding and at least annually thereafter:

1. **CUI Handling** — identification of CUI markings, permitted storage locations (labeled Drive folders, Assured Workloads buckets), transmission via DoD SAFE, prohibition on personal email, personal cloud storage, and unmanaged devices.
2. **Phishing and Social Engineering** — recognition of business-email-compromise patterns, prime-contractor impersonation, and reporting through the `security@dsg` alias. Includes at least two simulated phishing exercises per year.
3. **Insider Threat Awareness** — behavioral indicators, non-retaliation reporting channels, and the obligation to report suspected insider activity to the Security Officer.
4. **Password and Credential Hygiene** — hardware-key MFA usage, password manager use, prohibition on credential reuse, and handling of lost keys.
5. **Mobile Device Policy** — enrollment requirement for any device touching CUI, remote-wipe consent, prohibition on jailbroken/rooted devices, and travel guidance for ITAR-relevant destinations.

## 4. Role-Based Content

In addition to the baseline curriculum:

- **Operations / Business:** contract-flowdown awareness (DFARS 252.204-7012, ITAR §120–130), export-control basics, visitor and shipping controls for CUI-marked physical media.
- **Engineering / Administrators:** secure development practices for the CUI Enclave, GCP Assured Workloads guardrails, VPC Service Controls, secret management, incident-preserving log handling, and least-privilege administration.

## 5. Delivery and Records

Training is delivered via a designated learning platform tracked in Workspace. The Security Officer maintains completion records, including user, module, version, and completion date, for a minimum of three years. Non-completion within the annual window results in temporary suspension of enclave access until remediated.

## 6. Program Review

The curriculum is reviewed at least annually and updated when threat intelligence, contract requirements, or the technology stack materially change.

## Attestation

The undersigned Security Officer attests that the training program described above is in effect and that annual completion is tracked for all in-scope personnel, satisfying AT.L2-3.2.1, AT.L2-3.2.2, and AT.L2-3.2.3.

- **Required Role:** Role_SecurityOfficer
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
