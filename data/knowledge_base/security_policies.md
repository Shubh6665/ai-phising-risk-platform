# Project Triage Guidance and Recommended Security Controls

> [!NOTE]
> **PROJECT TRIAGE GUIDANCE — NOT AN ORGANIZATION-APPROVED SECURITY POLICY**  
> This document specifies application-level triage score boundaries, automated routing actions, and recommended baseline security controls for the **AI Phishing Risk & Security Triage Platform**.
> 
> The numerical risk score thresholds (0.0–100.0) and tier classifications (Low, Medium, High, Critical) are technical design choices of this project's ensemble architecture (`src/models/ensemble.py`). They are not standards or thresholds mandated by NIST, CISA, or MITRE.
> 
> This guidance does not constitute an officially approved organizational cybersecurity policy. Any deploying organization must formally author, approve, and maintain its own policies, acceptable use standards, and escalation authorities under the governance of organizational leadership and legal counsel.
> 
> **Document Type**: Authoritative Reference Guidance  
> **Target Audience**: Security Analysts, Triage Engineers, Automated Response Systems  
> **Sources**: CISA (Phishing Guidance, Secure Our World), NIST (SP 800-177 Rev. 1, SP 800-61 Rev. 3), MITRE ATT&CK (T1566)  
> **Source Verification Date**: 2026-10-29

---

## 1. Scope and Architectural Context

### Differentiating Application Triage from Enterprise Security Policy
In enterprise cybersecurity operations, there is an essential distinction between automated software triage and governance policy:

1. **Application Triage Engine**:
   - The algorithmic pipeline implemented by this platform accepts an incoming email message, extracts structural and lexical features, computes predictive probabilities from statistical machine learning (Random Forest) and deep learning (fine-tuned DistilBERT) models, and evaluates deterministic rule signals.
   - The engine maps these inputs to an application-level composite risk score from 0.0 to 100.0. This score provides a prioritization index for downstream filtering and analysis.

2. **Organizational Security Policy**:
   - As emphasized in NIST SP 800-61 Rev. 3 (*Govern* function GV-1 and GV-2) and CISA's *Incident Response Plan Basics*, organizational policies are legally binding governance documents. They establish mandatory security baselines, assign operational roles, mandate incident escalation authorities, and specify regulatory compliance requirements.
   - An automated tool can inform triage decisions, but it cannot unilaterally dictate organizational policy without executive approval.

Deploying organizations should evaluate this project's triage guidance as a reference starting point when drafting their own formal email security policies and operational thresholds.

---

## 2. Application Risk Scoring Tiers and Automated Actions

The platform combines statistical ML model probabilities, transformer NLP outputs, and heuristic rule signals into an application-level risk score from 0.0 to 100.0 (implemented in `src/models/ensemble.py`). The application categorizes scores into four operational triage tiers:

```
Score:  0.0 ────────────── 39.9 ────────────── 59.9 ────────────── 79.9 ────────────── 100.0
Tier:   [     Low Risk        ] [    Medium Risk    ] [     High Risk     ] [   Critical Risk   ]
Action: Standard Delivery       Warning Injected      Automated Quarantine  Immediate Block
```

### Low Risk Tier (Score: 0.0 – 39.9)
- **Application Classification**: `Low`
- **Triage Action**: `Standard Delivery / Allow`
- **Technical Handling**: Deliver message to recipient mailbox without modification or latency. Both statistical models and heuristic extractors indicate negligible phishing signals.
- **Audit & Telemetry**: Record the analysis identifier (`analysis_id`), request ID, model probabilities, and text hash in audit storage for operational monitoring and model drift detection.
- **Reference Grounding**: Consistent with CISA recommendations to maintain uninterrupted business communication when authentication checks pass and threat indicators are absent.

### Medium Risk Tier (Score: 40.0 – 59.9)
- **Application Classification**: `Medium`
- **Triage Action**: `Defensive Delivery / Warning Injected`
- **Technical Handling**: Deliver message to recipient mailbox with an informational warning banner prepended to the message body:
  ```
  [CAUTION: EXTERNAL SENDER / SUSPICIOUS PATTERNS DETECTED]
  This email originated outside the organization or contains unusual language patterns.
  Verify the sender before opening attachments or following embedded links.
  ```
- **Recommended User Controls**:
  - Advise the recipient to independently verify the sender's identity through out-of-band communication before taking action.
  - Provide a one-click "Report Phishing" self-service feature within the email client, as recommended by the CISA *Secure Our World* campaign.
- **Link Rewriting**: Where supported by the email gateway, enable click-time protection to re-evaluate destination URLs dynamically upon user interaction.

### High Risk Tier (Score: 60.0 – 79.9)
- **Application Classification**: `High`
- **Triage Action**: `Automated Quarantine / Security Analyst Review`
- **Technical Handling**: Divert message from the standard delivery stream into an administrative or SOC quarantine repository. The message remains inaccessible to the recipient pending secondary evaluation.
- **User Notification**: Deliver an automated receipt notifying the recipient that an incoming message from the claimed sender is undergoing security inspection.
- **Analyst Triage**: Prioritize the message in the security operations queue. The analyst inspects header provenance, sandboxes attachments, and validates extracted indicators of compromise (IOCs).
- **Reference Grounding**: Aligns with CISA *Phishing Guidance* recommendations to prevent initial access by isolating high-probability threats at Phase One of the attack cycle.

### Critical Risk Tier (Score: 80.0 – 100.0)
- **Application Classification**: `Critical`
- **Triage Action**: `Immediate Block / Perimeter Containment / High-Priority Alert`
- **Technical Handling**: Immediately drop the message payload. Suppress delivery across all organizational mailboxes.
- **Automated Containment Recommendations**:
  1. Extract sender domains, originating IP addresses, and embedded URLs to update edge perimeter blocklists.
  2. Query mailbox logs using the normalized message body hash (`email_hash`) or subject to detect and neutralize identical messages received across the enterprise.
  3. If user telemetry reveals outbound interaction with an embedded URL, trigger identity containment workflows (session termination and token revocation).
- **Reference Grounding**: Mitigates active exploitation scenarios described in MITRE ATT&CK T1566 (Phishing) and CISA credential theft guidance.

---

## 3. Recommended Technical Controls for High-Risk Email Vectors

The following baseline controls are recommended for enterprise email deployments, supported by authoritative standards:

### Out-of-Band Verification for Financial and Executive Requests
- **Threat Vector**: Business Email Compromise (BEC) and executive impersonation (MITRE ATT&CK T1566).
- **Core Principle**: Any inbound or internal communication requesting financial transactions, wire transfers, changes to vendor payment accounts, or payroll alterations must be verified independently prior to processing.
- **Verification Rule**: Verification must use a pre-existing, trusted out-of-band communication channel (such as a known internal extension, in-person inquiry, or established phone number recorded in corporate vendor records).
- **Crucial Warning**: Never use phone numbers, email addresses, or web links provided within the suspicious message itself, as threat actors routinely furnish fraudulent contact details (CISA *Secure Our World* guidance).

### Phishing-Resistant Multi-Factor Authentication (MFA)
- **Threat Vector**: Credential harvesting and Adversary-in-the-Middle (AiTM) reverse-proxies (MITRE ATT&CK T1566.002, T1598; OWASP A07:2021).
- **Vulnerability of Legacy MFA**: Standard passwords, SMS-based one-time codes, and legacy mobile push notifications are vulnerable to interception and replay by modern reverse-proxy phishing kits (e.g., Evilginx).
- **Recommended Baseline**: CISA, the NSA, the FBI, and NIST strongly recommend transitioning enterprise identity systems to **phishing-resistant MFA**, specifically FIDO2/WebAuthn hardware security keys or PKI-based smart cards. Phishing-resistant authenticators cryptographically bind authentication tokens to the authentic browser origin, rendering harvested credentials useless on attacker domains.

### Email Domain Authentication and DMARC Enforcement
- **Threat Vector**: Domain spoofing and unauthorized sender impersonation.
- **Technical Recommendation**: Deploy and enforce the three foundational email authentication protocols as specified by NIST SP 800-177 Rev. 1 (Section 4):
  1. **SPF (Sender Policy Framework)**: Publish authoritative IP records for outbound mail servers.
  2. **DKIM (DomainKeys Identified Mail)**: Cryptographically sign outbound message headers.
  3. **DMARC (Domain-based Message Authentication, Reporting, and Conformance)**: Mandate alignment between RFC 5322 `From` headers and SPF/DKIM verification. Configure the organizational DMARC policy progressively toward `p=reject` to block unauthorized spoofed messages at the perimeter.

---

## 4. Authoritative Source Traceability and Verification Matrix

The recommendations in this document are grounded in the following official publications:

| Source Title | Issuing Body | Publication Date | Verified Canonical URL | Verification Date |
|---|---|---|---|---|
| **Phishing Guidance: Stopping the Attack Cycle at Phase One** | CISA / NSA / FBI / MS-ISAC | October 18, 2023 (PDF refreshed March 2025) | [CISA Phishing Guidance](https://www.cisa.gov/resources-tools/resources/phishing-guidance-stopping-attack-cycle-phase-one) | 2026-10-29 |
| **NIST SP 800-61 Rev. 3: Incident Response Recommendations** | NIST | April 3, 2025 (Final) | [NIST CSRC SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final) | 2026-10-29 |
| **NIST SP 800-177 Rev. 1: Trustworthy Email** | NIST | February 2019 | [NIST CSRC SP 800-177 Rev. 1](https://csrc.nist.gov/pubs/sp/800/177/r1/final) | 2026-10-29 |
| **Secure Our World: Phishing Tip Sheet** | CISA | September 2024 | [CISA Phishing Tip Sheet (PDF)](https://www.cisa.gov/sites/default/files/2024-09/Secure-Our-World-Phishing-Tip-Sheet.pdf) | 2026-10-29 |
| **Incident Response Plan Basics** | CISA | February 1, 2024 | [CISA IRP Basics (PDF)](https://www.cisa.gov/sites/default/files/2024-02/Incident-Response-Plan-Basics_508c_1Feb2024.pdf) | 2026-10-29 |
| **MITRE ATT&CK: Phishing (T1566)** | MITRE Corporation | v15 (Current) | [MITRE ATT&CK T1566](https://attack.mitre.org/techniques/T1566/) | 2026-10-29 |
