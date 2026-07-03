# Risk Assessment Policy

**Organization:** Dynamical Systems Group, LLC (DSG)
**Document ID:** POL_RA_Assessment
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies to CMMC L2 Controls:** RA.L2-3.11.1, RA.L2-3.11.3 (NIST SP 800-171 Rev.2 §3.11.1 and §3.11.3)

## 1. Purpose

This policy establishes how DSG assesses risk to the DSG CUI Enclave and remediates identified vulnerabilities. It satisfies:

- **RA.L2-3.11.1** — periodically assess the risk to organizational operations, assets, and individuals resulting from the operation of systems that process, store, or transmit CUI.
- **RA.L2-3.11.3** — remediate vulnerabilities in accordance with risk assessments.

## 2. Scope

All components of the DSG CUI Enclave, including the Google Workspace Enterprise Plus tenant, the GCP Assured Workloads (IL4) folder and its projects, managed endpoints, and identity infrastructure.

## 3. Asset Inventory

The Security Officer maintains a system inventory covering: Workspace tenant configuration and DLP rules; Assured Workloads projects, service accounts, and VPC Service Controls perimeters; managed endpoint fleet; hardware security keys issued to personnel; and third-party services with any nexus to CUI. The inventory is reviewed each quarter.

## 4. Threat Enumeration

Threats considered in each assessment include: credential compromise (phishing, key loss, session hijack); insider misuse (accidental or intentional); misconfiguration of Workspace sharing or Assured Workloads guardrails; supply-chain compromise of endpoint or IdP tooling; and physical loss of endpoints containing cached CUI.

## 5. Likelihood and Impact Ratings

Each identified risk is rated on a three-point scale (Low, Moderate, High) for both likelihood and impact. Composite risk is derived from the pairing, with any risk containing a High rating in either axis escalated to the Affirming Official.

## 6. Risk Decisions

For each rated risk, the Security Officer records one of the following dispositions, with justification:

- **Accept** — residual risk is within tolerance; documented and revisited at the next assessment.
- **Mitigate** — controls are added or strengthened; a remediation item is opened.
- **Transfer** — risk is shifted (for example, via insurance or by pushing a function to a compliant provider).
- **Avoid** — the associated activity or component is discontinued.

Accepted risks require Affirming Official concurrence when rated Moderate or above.

## 7. Remediation Tracker

Mitigation items are recorded in the DSG remediation tracker with owner, severity, target completion date, and status. High-severity items carry a target of 30 days; Moderate 90 days; Low tracked but not date-bound. The tracker is reviewed monthly by the Security Officer and referenced in the next assessment cycle to close the loop with RA.L2-3.11.3.

## 8. Cadence

A full risk assessment is performed at least annually. An interim assessment is triggered by any material change to the enclave, a High-severity incident, or a new contract that alters CUI scope.

## Attestation

The undersigned Security Officer attests that risk assessments are performed on the cadence described and that identified vulnerabilities are remediated in accordance with the ratings above, satisfying RA.L2-3.11.1 and RA.L2-3.11.3.

- **Required Role:** Role_SecurityOfficer
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
