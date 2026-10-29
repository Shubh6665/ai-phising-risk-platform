# Phishing Incident Response Guidance and Recommended Handling Procedures

> [!NOTE]
> **REFERENCE GUIDANCE — NOT AN ORGANIZATION-APPROVED INCIDENT RESPONSE PLAN**  
> This document provides general, source-backed cybersecurity incident response guidance for managing phishing campaigns and email-borne threats. It provides reference context for the automated triage pipeline and retrieval-augmented generation (RAG) assistant in the **AI Phishing Risk & Security Triage Platform**.
> 
> This document is technical reference material and does not constitute an officially approved organizational Incident Response Plan (IRP). According to primary guidance from CISA (*Incident Response Plan Basics*) and NIST (*SP 800-61 Rev. 3*), an effective incident response capability requires a formal, written IRP customized to the organization's unique operational environment, authorized by executive leadership, reviewed by legal counsel, and drilled through periodic tabletop exercises.
> 
> **Document Type**: Authoritative Reference Guidance  
> **Target Audience**: Incident Responders, Security Analysts, Automated Triage Engines  
> **Sources**: NIST (SP 800-61 Rev. 3), CISA (Incident Response Plan Basics, Phishing Guidance), MITRE ATT&CK (T1566)  
> **Source Verification Date**: 2026-10-29

---

## 1. Incident Response Framework Alignment

### NIST Cybersecurity Framework (CSF) 2.0 Integration (SP 800-61 Rev. 3)
In NIST Special Publication 800-61 Revision 3 (*Incident Response Recommendations and Considerations for Cybersecurity Risk Management: A CSF 2.0 Community Profile*, published April 3, 2025), incident response is structured as an integral component of ongoing enterprise risk management rather than a standalone, isolated four-phase procedure. 

Incident management activities align across the six core functions of the NIST Cybersecurity Framework 2.0:

```
┌────────────────────────────────────────────────────────────────────────┐
│               NIST CSF 2.0 Functions in Incident Management             │
├───────────────┬────────────────────────────────────────────────────────┤
│ Govern (GV)   │ Incident response policies, oversight, and legal review│
│ Identify (ID) │ Asset visibility, threat modeling, improvement tracking│
│ Protect (PR)  │ Phishing-resistant MFA, email authentication, training │
│ Detect (DE)   │ Automated triage, anomaly detection, IOC correlation   │
│ Respond (RS)  │ Threat scoping, containment, eradication, communication│
│ Recover (RC)  │ Account restoration, service recovery, post-mortems    │
└───────────────┴────────────────────────────────────────────────────────┘
```

### Operational Phases from CISA Incident Response Plan Basics
CISA's *Incident Response Plan Basics* (published February 1, 2024) organizes organizational preparedness into three essential phases:
1. **Before an Incident (Preparation & Readiness)**: Train staff to recognize phishing lures; establish relationships with regional CISA teams and law enforcement; review plans with legal counsel; maintain offline, physical copies of the plan and critical contact lists.
2. **During an Incident (Execution & Containment)**: Coordinate technical triage; isolate impacted accounts and endpoints; preserve digital evidence; maintain open communication trees across technical and executive stakeholders.
3. **After an Incident (Post-Mortem & Evolution)**: Convene a structured lessons-learned session; remediate root-cause vulnerabilities; update technical detection rules and the response plan itself immediately.

---

## 2. Technical Incident Handling Procedures for Phishing

When an incoming email or reported message indicates potential phishing or malicious intent, response teams and automated triage engines should execute structured handling procedures:

### Step 1: Detection, Triage, and Threat Scoping (Detect / DE)
- **Ingestion & Automated Assessment**: Evaluate the suspicious message via `POST /api/v1/analyze` to compute predictive probabilities (classical Random Forest, DistilBERT NLP), evaluate heuristic indicators (URL count, IP hosts, urgency language), and calculate the application risk score (0.0–100.0).
- **Indicator Extraction**: Extract key Indicators of Compromise (IOCs) from the email:
  - Sender RFC 5322 `From` and `Reply-To` headers, originating IP address, and SMTP HELO/EHLO values.
  - SPF, DKIM, and DMARC authentication and alignment statuses.
  - All embedded hyperlinks, destination hostnames, and shortened URL redirect targets.
  - Attachment file names, MIME types, and cryptographic hashes (SHA-256).
- **Tenant-Wide Scoping**: Query enterprise mail server logs or messaging APIs using the subject line, sender domain, or body hash (`email_hash`) to determine the total number of delivered copies and identify which organizational recipients received or opened the message.

### Step 2: Containment Actions (Respond / RS)
- **Mailbox-Level Containment**:
  - For messages triaged in the High risk tier (60.0–79.9): Ensure the message remains quarantined and inaccessible to users pending analyst review.
  - For messages triaged in the Critical risk tier (80.0–100.0): Immediately purge or revoke access to the message across all recipient inboxes via tenant-wide administrative commands.
- **Perimeter Network & Gateway Blocking**:
  - Ingest extracted malicious hostnames, phishing domains, and staging URLs into email gateway blocklists and web security filters.
  - Block originating IP addresses at perimeter firewalls where malicious infrastructure is confirmed.
- **Identity & Session Containment**:
  - If telemetry or user reporting confirms that a recipient clicked an embedded link or submitted credentials to a suspicious portal, immediately revoke all active cloud SSO sessions and refresh tokens (citing CISA / NSA / FBI *Phishing Guidance*).
  - Temporarily restrict account privileges to prevent lateral movement within corporate cloud resources.

### Step 3: Eradication (Respond / RS)
- **Cross-Tenant Message Removal**: Execute an enterprise-wide purge to ensure all identical or variant messages are completely removed from all mailboxes, deleted item folders, and transit queues.
- **Infrastructure Reporting & External Takedown**:
  - Report confirmed phishing infrastructure, fraudulent domains, and hosting servers to the relevant domain registrars and web hosting providers.
  - Submit phishing samples to external intelligence repositories:
    - Cybersecurity and Infrastructure Security Agency: `report@cisa.gov`
    - Anti-Phishing Working Group (APWG): `reportphishing@apwg.org`
    - Federal Bureau of Investigation Internet Crime Complaint Center (IC3): `ic3.gov` (for financial or wire fraud attempts).

### Step 4: Recovery and Account Restoration (Recover / RC)
- **Trusted Credential Rotation**:
  - Reset passwords for compromised accounts using verified, out-of-band communication procedures (e.g., manager approval or direct voice confirmation). Never transmit temporary credentials through channels derived from the suspicious email.
  - Mandate enrollment in phishing-resistant MFA (FIDO2 hardware tokens or WebAuthn keys) before restoring account access.
- **Mailbox Rule and Delegate Audit**:
  - Audit compromised accounts for attacker-created persistence mechanisms, such as unauthorized email forwarding rules, hidden inbox rules, or added delegate mailbox permissions.
- **False-Positive Handling**: If manual review determines a quarantined message was a benign false positive, release the message to the recipient, notify the sender, and record feedback to support model evaluation and threshold tuning.

### Step 5: Post-Incident Review and Continuous Improvement (Govern / GV & Identify / ID)
- Conduct a blameless post-mortem with responders and relevant stakeholders to evaluate detection speed, containment efficacy, and tool performance.
- Incorporate validated indicators of compromise into internal threat intelligence platforms.
- Review and refine heuristic rule extractors and model training data to address novel attacker evasion techniques.

---

## 3. Technical Triage Priority vs. Organizational Response SLAs

The platform provides an objective application risk score (0.0–100.0) to prioritize investigation queues. However, concrete Service Level Agreements (SLAs), staffing allocations, and escalation deadlines must be established by each organization's leadership.

The following table contrasts application-level triage priorities with considerations for organizational response planning:

| Risk Classification | Application Score Tier | Automated Application Action | Recommended Technical Triage Focus | Organizational SLA & Policy Considerations |
|---|---|---|---|---|
| **Low** | 0.0 – 39.9 | Standard delivery; log telemetry | Baseline telemetry retention; no immediate analyst action required | Automated handling; periodically audited for false negatives |
| **Medium** | 40.0 – 59.9 | Defensive delivery with warning header injected | User reporting review; click-time protection monitoring | Queue for Tier-1 analyst triage if user submits a phishing report |
| **High** | 60.0 – 79.9 | Divert to SOC quarantine repository | In-depth header analysis; URL and attachment sandboxing | Prioritized analyst review queue; SLA determined by enterprise policy |
| **Critical** | 80.0 – 100.0 | Immediate message drop; high-priority alert | Immediate tenant-wide purge; edge domain blocking; session review | High-priority escalation to incident commander; expedited response |

> [!IMPORTANT]
> Specific containment timeframes (e.g., "15-minute response" or "1-hour SLA"), role assignments, and legal reporting obligations (such as GDPR 72-hour notification or SEC incident disclosure rules) must be defined and authorized by the deploying organization's executive management and legal counsel.

---

## 4. Recommended Handling Procedures for High-Impact Phishing Scenarios

### Scenario A: Suspected Credential Disclosure and Adversary-in-the-Middle (AiTM)
- **Threat Mechanism**: The recipient interacted with a replica login portal or reverse-proxy server (e.g., Evilginx), potentially disclosing credentials and active session cookies (MITRE ATT&CK T1566.002, T1598.003).
- **Recommended Handling Steps**:
  1. **Immediate Session Termination**: Terminate all active browser sessions, cloud application tokens, and refresh tokens for the affected identity across Microsoft Entra ID, Google Workspace, or Okta.
  2. **Out-of-Band Credential Reset**: Execute an immediate password reset via verified out-of-band channels.
  3. **Sign-In Telemetry Audit**: Query identity provider sign-in logs for the preceding 4 hours, inspecting for anomalous IP addresses, unexpected user agents, or geographically improbable access events.
  4. **Persistence Inspection**: Check for illicit OAuth enterprise application consent grants (MITRE ATT&CK T1528) and newly created mailbox forwarding or redirect rules.

### Scenario B: Business Email Compromise (BEC) and Payment Diversion
- **Threat Mechanism**: Impersonation of an executive, legal representative, or established vendor requesting urgent wire transfers, bank account changes, or gift card purchases (MITRE ATT&CK T1566).
- **Recommended Handling Steps**:
  1. **Out-of-Band Verification**: Contact the purported requester immediately using an established, pre-existing internal telephone extension or in-person verification. Do not respond to the email or use contact numbers listed in the email body.
  2. **Disbursement Hold**: Immediately alert organizational finance and treasury teams to place a temporary hold on all pending disbursements associated with the identified accounts or vendor.
  3. **Financial Fraud Reporting**: If funds were already disbursed, contact the sending and receiving financial institutions' fraud departments immediately to request an emergency wire recall, and file an IC3 complaint with the FBI.

---

## 5. Authoritative Source Traceability and Verification Matrix

The procedures in this guidance are grounded in the following official publications:

| Source Title | Issuing Body | Publication Date | Verified Canonical URL | Verification Date |
|---|---|---|---|---|
| **NIST SP 800-61 Rev. 3: Incident Response Recommendations** | NIST | April 3, 2025 (Final) | [NIST CSRC SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final) | 2026-10-29 |
| **Incident Response Plan Basics** | CISA | February 1, 2024 | [CISA IRP Basics (PDF)](https://www.cisa.gov/sites/default/files/2024-02/Incident-Response-Plan-Basics_508c_1Feb2024.pdf) | 2026-10-29 |
| **Phishing Guidance: Stopping the Attack Cycle at Phase One** | CISA / NSA / FBI / MS-ISAC | October 18, 2023 (PDF refreshed March 2025) | [CISA Phishing Guidance](https://www.cisa.gov/resources-tools/resources/phishing-guidance-stopping-attack-cycle-phase-one) | 2026-10-29 |
| **Secure Our World: Phishing Tip Sheet** | CISA | September 2024 | [CISA Phishing Tip Sheet (PDF)](https://www.cisa.gov/sites/default/files/2024-09/Secure-Our-World-Phishing-Tip-Sheet.pdf) | 2026-10-29 |
| **MITRE ATT&CK: Phishing (T1566)** | MITRE Corporation | v15 (Current) | [MITRE ATT&CK T1566](https://attack.mitre.org/techniques/T1566/) | 2026-10-29 |
