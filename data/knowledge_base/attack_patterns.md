# Attack Patterns and Threat Actor Tactics

> **Document Type**: Authoritative Technical Guidance  
> **Target Audience**: Security Analysts, Detection Engineers, Automated Triage Engines  
> **Sources**: MITRE ATT&CK Framework, Open Worldwide Application Security Project (OWASP)  
> **Source Verification Date**: 2026-10-29

---

## 1. Overview and Threat Context

Phishing operations span broad, indiscriminate bulk campaigns to highly sophisticated, targeted spear-phishing operations. Threat actors employ deceptive lures to establish initial access, harvest credentials, conduct espionage, or execute financial fraud.

Authoritative references:
- **MITRE ATT&CK Enterprise Matrix**: [Phishing (T1566)](https://attack.mitre.org/techniques/T1566/)
- **MITRE ATT&CK Enterprise Matrix**: [Phishing for Information (T1598)](https://attack.mitre.org/techniques/T1598/)
- **MITRE ATT&CK Enterprise Matrix**: [Internal Spearphishing (T1534)](https://attack.mitre.org/techniques/T1534/)
- **OWASP**: [Phishing Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Phishing_Prevention_Cheat_Sheet.html)
- **OWASP**: [Automated Threats Handbook (OAT-019 / Account Takeover)](https://owasp.org/www-project-automated-threats-to-web-applications/)

---

## 2. MITRE ATT&CK Phishing Taxonomy

### T1566: Initial Access via Phishing
Adversaries send messages to gain execution access on target victim endpoints:
- **T1566.001: Spearphishing Attachment**: Delivering malicious files directly as email attachments (e.g., weaponized PDFs, macro documents, ISO/VHD images, or script loaders) that execute exploit code or droppers when opened.
- **T1566.002: Spearphishing Link**: Directing targets to click hyperlinks leading to malicious landing pages, drive-by downloads, or credential harvesting portals hosted on external attacker infrastructure.
- **T1566.003: Spearphishing via Service**: Transmitting malicious lures through third-party enterprise services, cloud communication tools, collaboration platforms, or social media rather than direct SMTP.
- **T1566.004: Spearphishing Voice (Vishing)**: Directing targets to phone numbers or placing voice calls to manipulate users into divulging MFA credentials, passwords, or installing remote administration tools.

### T1598: Phishing for Information
Adversaries send deceptive communications specifically engineered to elicit sensitive credentials, corporate intelligence, or infrastructure details without dropping executable code:
- **T1598.001: Spearphishing Service**: Coaxing users to authenticate to fake third-party portals or corporate SSO mirrors.
- **T1598.003: Spearphishing Link**: Luring users to replica portals that collect usernames, passwords, and multi-factor authentication (MFA) tokens.

### T1534: Internal Spearphishing
Adversaries who have already compromised an internal account use that trusted internal mailbox to send spear-phishing emails to colleagues. Because the email originates from a legitimate internal account within the organization, it inherently bypasses perimeter gateway filters and enjoys implicit user trust.

---

## 3. High-Impact Phishing Attack Profiles

### Profile A: Credential Harvesting and AiTM (Adversary-in-the-Middle)
- **Objective**: Intercept user credentials and session authentication tokens to bypass Multi-Factor Authentication (MFA).
- **Mechanism**: The attacker deploys a reverse-proxy server (e.g., Evilginx architecture) that proxies communications between the victim and the legitimate corporate identity provider (e.g., Microsoft Entra ID, Google Workspace, Okta).
- **Behavioral Signal**: The phishing link points to an attacker-controlled proxy domain, yet the landing page is a live mirror of the actual login portal. When the user enters their username, password, and MFA code, the proxy forwards the payload to the genuine service and captures the generated session cookie (cookie theft).
- **OWASP Alignment**: Counterpart to *A07:2021 Identification and Authentication Failures* and *OAT-019 Account Takeover*.

### Profile B: Business Email Compromise (BEC) and Executive Fraud
- **Objective**: Induce financial transfers, payroll modifications, or sensitive record extraction without deploying malware or hyperlinks.
- **Mechanism**: Attackers masquerade as corporate executives (CEO, CFO), trusted external legal counsel, or known suppliers. These emails rely strictly on pure conversational text, social hierarchy, and manufactured urgency.
- **Common Variants**:
  - *Wire Transfer Fraud*: High-priority request for an urgent foreign investment or confidential acquisition.
  - *Vendor Invoice Manipulation*: Impersonating a trusted supplier notifying accounts payable of updated banking details.
  - *Gift Card Scams*: Executive asking an employee to purchase gift cards for an urgent client gift.
- **Key Detection Challenge**: Zero malicious URLs, zero weaponized attachments, and normal language syntax make BEC undetectable by signature-based antivirus or URL reputation filters. Detection requires semantic urgency extraction, sender anomaly tracking, and financial keyword inspection.

### Profile C: Quishing (QR Code Phishing)
- **Objective**: Evade email gateway URL inspection by embedding the destination link inside a Quick Response (QR) code image.
- **Mechanism**: The email body contains an image prompting the user to scan the QR code with their personal smartphone (e.g., "MFA reconfiguration required", "Scan to view secure payroll document").
- **Evasion Impact**: Traditional email security gateways (SEGs) analyze HTML text and hyperlinks, often failing to extract and parse links embedded inside image attachments. Scanning with a personal mobile device also moves the victim outside corporate endpoint security monitoring.

### Profile D: Consent Phishing and Illicit OAuth Application Abuse
- **Objective**: Establish persistent API access to mailbox and cloud storage without stealing user credentials.
- **Mechanism**: The attacker creates a rogue multi-tenant OAuth application on a legitimate platform (e.g., Microsoft Azure / Google Cloud) and sends an authorization link disguised as a shared document or calendar invite.
- **Behavioral Signal**: When the victim clicks the link, they authenticate with their genuine provider. The application then prompts for broad permissions (e.g., `Mail.ReadWrite`, `Files.ReadWrite.All`, `offline_access`). Once granted, the attacker retains API access via persistent refresh tokens even after password resets.

---

## 4. Authoritative Source Traceability Matrix

| Attack Pattern | Framework / ID | Verified Canonical URL | Primary Defense & Detection Strategy |
|---|---|---|---|
| **Spearphishing Attachment** | MITRE ATT&CK T1566.001 | [MITRE T1566.001](https://attack.mitre.org/techniques/T1566/001/) | Attachment sandboxing, blocking dangerous file extensions, macro execution restrictions. |
| **Spearphishing Link** | MITRE ATT&CK T1566.002 | [MITRE T1566.002](https://attack.mitre.org/techniques/T1566/002/) | Click-time URL analysis, domain age inspection, brand homoglyph detection. |
| **Spearphishing Voice (Vishing)** | MITRE ATT&CK T1566.004 | [MITRE T1566.004](https://attack.mitre.org/techniques/T1566/004/) | Out-of-band identity verification, security awareness training against phone lures. |
| **Internal Spearphishing** | MITRE ATT&CK T1534 | [MITRE T1534](https://attack.mitre.org/techniques/T1534/) | Internal email scanning, anomaly detection on unusual internal sender behavior. |
| **Credential Harvesting** | MITRE ATT&CK T1056.003 / OWASP A07 | [MITRE T1056.003](https://attack.mitre.org/techniques/T1056/003/) | FIDO2 / WebAuthn phishing-resistant MFA, conditional access policies based on device health. |
| **Account Takeover via Phish** | OWASP OAT-019 | [OWASP OAT-019](https://owasp.org/www-project-automated-threats-to-web-applications/) | Anomaly-based sign-in monitoring, session token invalidation, step-up authentication. |
| **OAuth Abuse** | MITRE ATT&CK T1528 / T1566 | [MITRE T1528](https://attack.mitre.org/techniques/T1528/) | User consent restrictions, administrator approval workflows for third-party enterprise apps. |
