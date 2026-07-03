# Collaborative Computing, Mobile Code, and VoIP Policy

**Organization:** Dynamical Systems Group, LLC
**Document ID:** POL-SC-Collab
**Version:** 1.0
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies To:** All personnel, contractors, and systems processing Controlled Unclassified Information (CUI)

## 1. Purpose

This policy establishes controls governing collaborative computing devices, mobile code, and Voice over Internet Protocol (VoIP) technologies used in the handling of CUI. It implements the following NIST SP 800-171 Rev. 2 requirements:

- **SC.L2-3.13.12** — Prohibit remote activation of collaborative computing devices and provide indication of devices in use to users present at the device.
- **SC.L2-3.13.13** — Control and monitor the use of mobile code.
- **SC.L2-3.13.14** — Control and monitor the use of VoIP technologies.

## 2. Scope

Dynamical Systems Group ("DSG") is a fully remote, ~10-person defense contractor executing DFARS/ITAR SBIR work. CUI is stored and processed in Google Workspace Enterprise Plus and Google Cloud Assured Workloads (IL4). This policy applies to all endpoints, meeting platforms, and communication channels used for CUI.

## 3. Collaborative Computing (SC.L2-3.13.12)

- Cameras and microphones on CUI-authorized endpoints are disabled by default via managed device policy in Google Workspace and enabled only during active user-initiated sessions.
- Google Meet and Zoom (Zoom for Government tenant) are the only approved conferencing tools for CUI discussions. Remote activation of cameras or microphones by meeting hosts is disabled.
- All conferencing clients must display a visible on-screen indicator (camera light, mic status) whenever the device is active. Users are trained to verify these indicators before discussing CUI.
- Recording of meetings involving CUI requires explicit approval from the Security Officer and is stored only in the CUI-scoped Google Drive.

## 4. Mobile Code (SC.L2-3.13.13)

- Permitted mobile code categories: signed JavaScript served over HTTPS from Google Workspace, Google Cloud Console, GitHub, and other explicitly allowlisted SaaS providers used for contract execution.
- Prohibited categories: ActiveX, unsigned Java applets, Flash, and any mobile code loaded from unknown or unclassified origins.
- Endpoint browsers are managed via Google Chrome Enterprise policies that block prohibited categories and enforce Safe Browsing.
- Any new SaaS tool requiring mobile code execution must be reviewed and authorized by the IT Administrator prior to use in CUI workflows.

## 5. VoIP (SC.L2-3.13.14)

- Approved VoIP services for CUI-adjacent conversations: Google Meet (Workspace Enterprise Plus) and Zoom for Government. Consumer VoIP (personal Zoom, Skype, WhatsApp, FaceTime) is prohibited for CUI discussions.
- VoIP call metadata and admin audit logs are exported to the central logging pipeline in GCP Assured Workloads for review.
- Users must confirm the meeting tenant and participant list before disclosing CUI on any VoIP call.
- Dial-in PSTN bridges are disabled for meetings scheduled in the CUI calendar scope.

## 6. Enforcement

Violations are handled under the DSG Acceptable Use Policy and may result in access revocation, disciplinary action, and reporting to the contracting officer where required by DFARS 252.204-7012.

## Attestation

I, the undersigned Affirming Official, attest that this policy is in effect for Dynamical Systems Group, LLC and reflects the organization's implementation of SC.L2-3.13.12, SC.L2-3.13.13, and SC.L2-3.13.14.

- **Required Role:** Role_ITAdmin
- **Affirming Official:** Sayer Tindall
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
