# Incident Response Plan

**Organization:** Dynamical Systems Group, LLC (DSG)
**Document ID:** POL_IR_Plan
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies to CMMC L2 Controls:** IR.L2-3.6.1, IR.L2-3.6.2, IR.L2-3.6.3 (NIST SP 800-171 Rev.2 §3.6.1–§3.6.3)

## 1. Purpose

This Incident Response Plan (IRP) establishes how DSG prepares for, detects, contains, eradicates, recovers from, and reports information security incidents affecting the DSG CUI Enclave. It satisfies:

- **IR.L2-3.6.1** — establish an operational incident-handling capability including preparation, detection, analysis, containment, recovery, and user response activities.
- **IR.L2-3.6.2** — track, document, and report incidents to designated officials and authorities.
- **IR.L2-3.6.3** — test the organizational incident response capability.

## 2. Scope

Applies to any suspected or confirmed compromise of confidentiality, integrity, or availability of CUI, the DSG CUI Enclave, or any credentials granting access to it.

## 3. Roles

- **Incident Commander (IC):** designated per incident by the Security Officer; owns the response, evidence chain, and stakeholder communication for the duration of the event.
- **Security Officer:** owns the IRP itself, appoints the IC, approves external disclosures, and is the point of contact for Government reporting.
- **Affirming Official:** briefed on incidents rated High or above; approves contractual disclosures.
- **Engineering On-Call:** executes containment and recovery actions in Workspace and GCP Assured Workloads.

## 4. Detection Criteria

Events promoted to incidents include, at minimum: confirmed CUI exposure to an unauthorized party; loss or theft of a managed endpoint holding CUI; account takeover of a user with CUI access; unauthorized change to Assured Workloads guardrails or VPC Service Controls; DLP alerts indicating attempted exfiltration; and malware detections on any device with CUI access.

## 5. Handling Lifecycle

1. **Prepare** — maintain contacts, playbooks, and forensic tooling; verify at least quarterly.
2. **Detect and Analyze** — triage alerts from Workspace Security Center, GCP Security Command Center, endpoint telemetry, and user reports.
3. **Contain** — revoke sessions, rotate credentials, isolate affected projects/buckets, and disable compromised accounts.
4. **Eradicate and Recover** — remove attacker access, restore from known-good state, and confirm integrity of CUI stores.
5. **Post-Incident** — root-cause analysis, corrective actions, and update of this plan and training content.

## 6. Escalation and Reporting

- **Internal escalation:** IC notifies the Security Officer within 1 hour of incident declaration; Affirming Official within 4 hours for High-severity events.
- **Government reporting:** cyber incidents affecting covered defense information are reported to DoD via DIBNet within 72 hours of discovery, as required by DFARS 252.204-7012.
- **CISA:** significant cyber incidents are additionally reported to CISA within 72 hours consistent with CIRCIA guidance.
- **Records:** each incident receives a tracking ID, timeline, evidence log, and closure memo retained for a minimum of six years.

## 7. Testing

The IRP is exercised at least annually through a tabletop exercise covering at least one plausible CUI-exposure scenario. Findings are recorded and drive updates to this plan.

## Attestation

The undersigned Security Officer attests that this Incident Response Plan is in effect, that reporting channels are established, and that annual testing is scheduled, satisfying IR.L2-3.6.1, IR.L2-3.6.2, and IR.L2-3.6.3.

- **Required Role:** Role_SecurityOfficer
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
