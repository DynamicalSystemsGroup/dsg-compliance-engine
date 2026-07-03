# System Use Notification (Login Banner) Policy

**Organization:** Dynamical Systems Group, LLC
**Document ID:** POL-AC-LoginBanner
**Version:** 1.0
**Last Reviewed:** 2026-06-15
**Next Review:** 2027-06-15
**Applies To:** All systems used to access, store, or process Controlled Unclassified Information (CUI)

## 1. Purpose

This policy implements **AC.L2-3.1.9** — "Provide privacy and security notices consistent with applicable CUI rules." It requires that a standard system use notification (login banner) be displayed at every logon to a CUI system operated by or on behalf of Dynamical Systems Group ("DSG").

## 2. Scope

The banner defined in Section 3 is displayed at the point of authentication for:

- Google Workspace Enterprise Plus (custom login-page notice for the `dynamicalsystemsgroup.com` primary domain).
- GCP Assured Workloads (IL4) — Cloud Console SSO landing page and any organization-managed VMs (SSH message-of-the-day).
- The organization VPN / bastion host used to reach private CUI resources.
- Any managed workstation configured for CUI access (Chromebook enterprise enrollment notice, macOS `PolicyBanner`).

## 3. Banner Text (Verbatim)

The following text is displayed in full, without modification, prior to the completion of authentication:

```
** WARNING **

You are accessing a U.S. Government (USG) Information System (IS) operated
on behalf of Dynamical Systems Group, LLC, that processes Controlled
Unclassified Information (CUI) subject to DFARS 252.204-7012 and, where
applicable, the International Traffic in Arms Regulations (ITAR).

By using this IS (which includes any device attached to this IS), you
consent to the following conditions:

  - The USG routinely intercepts and monitors communications on this IS
    for purposes including, but not limited to, penetration testing,
    COMSEC monitoring, network operations and defense, personnel
    misconduct (PM), law enforcement (LE), and counterintelligence (CI)
    investigations.
  - At any time, the USG may inspect and seize data stored on this IS.
  - Communications using, or data stored on, this IS are not private,
    are subject to routine monitoring, interception, and search, and may
    be disclosed or used for any USG-authorized purpose.
  - This IS includes security measures (e.g., authentication and access
    controls) to protect USG interests -- not for your personal benefit
    or privacy.
  - Notwithstanding the above, using this IS does not constitute consent
    to PM, LE, or CI investigative searching or monitoring of the content
    of privileged communications, or work product, related to personal
    representation or services by attorneys, psychotherapists, or clergy,
    and their assistants. Such communications and work product are
    private and confidential. See User Agreement for details.

Unauthorized or improper use of this system may result in disciplinary
action, as well as civil and criminal penalties.
```

## 4. Acknowledgment

Where the platform supports it (VPN, bastion, macOS `PolicyBanner`), the user must click "I Agree" or press ENTER to acknowledge the banner before authentication proceeds. Where explicit acknowledgment is not supported (Google Workspace login page), the banner is presented and continued use constitutes consent.

## 5. Maintenance

The banner text is reviewed annually and republished whenever the underlying DoD standard notice is revised. Any change requires the approval of the Security Officer and the Affirming Official.

## Attestation

I, the undersigned Affirming Official, attest that this policy is in effect for Dynamical Systems Group, LLC and reflects the organization's implementation of AC.L2-3.1.9.

- **Required Role:** Role_SecurityOfficer
- **Affirming Official:** Sayer Tindall
- **Effective Date:** 2026-06-15
- **Next Review Date:** 2027-06-15
