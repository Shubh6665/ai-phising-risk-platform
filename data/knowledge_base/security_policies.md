# Internal Security Policies and Triage Standards

> [!IMPORTANT]
> **MOCK POLICY DOCUMENT — CREATED FOR PROJECT DEMONSTRATION ONLY**  
> This document defines fictional, internal operational security policies created specifically for the **AI Phishing Risk & Security Triage Platform**. It does not represent the real-world policies of any commercial enterprise or standards organization.

---

## 1. Purpose and Scope

This document specifies the operational triage thresholds, containment triggers, and enforcement actions mandated by the internal security policy. These policies provide the ground truth rules referenced by the security triage engine and retrieval-augmented generation (RAG) assistant during automated email assessment.

---

## 2. Policy POL-SEC-101: Risk Score Tiers and Automated Actions

The platform assigns every evaluated email an application risk score from 0.0 to 100.0, deterministically mapped to four action tiers:

### Low Risk Tier (Score: 0.0 – 39.9)
- **Classification**: `Low`
- **Triage Action**: `Allow / Standard Delivery`
- **Gateway Enforcement**: Deliver to recipient inbox without modification.
- **User Notification**: Standard mailbox delivery; no defensive banners injected.
- **Audit Requirement**: Record analysis transaction ID, request ID, model probabilities, and text hash in audit log. Retain record for 30 days.

### Medium Risk Tier (Score: 40.0 – 59.9)
- **Classification**: `Medium`
- **Triage Action**: `Defensive Delivery / Warning Injected`
- **Gateway Enforcement**: Deliver to recipient inbox with an external warning header and visual banner:
  ```
  [CAUTION: SUSPICIOUS SENDER / UNVERIFIED LINKS DETECTED]
  This email contains unusual language patterns or external links. Verify the sender before clicking links or downloading attachments.
  ```
- **Link Rewriting**: Enable click-time link protection. Disable direct link execution where technically feasible.
- **User Guidance**: Present recipient with a "Report Phish" self-service option.

### High Risk Tier (Score: 60.0 – 79.9)
- **Classification**: `High`
- **Triage Action**: `Quarantine / Security Analyst Review`
- **Gateway Enforcement**: Divert message to the centralized Security Operations Center (SOC) quarantine queue. Block delivery to user inbox pending manual or secondary automated review.
- **User Notification**: Send automated quarantine receipt to the intended recipient informing them that an incoming message from the sender was held for security verification.
- **Analyst SLA**: Security analyst must review and disposition within 4 business hours.

### Critical Risk Tier (Score: 80.0 – 100.0)
- **Classification**: `Critical`
- **Triage Action**: `Immediate Block / Perimeter Containment / Automatic Escalation`
- **Gateway Enforcement**: Immediate drop of message payload. Message is permanently quarantined and never delivered to the user inbox.
- **Automated Defensive Response**:
  1. Add sender domain and originating IP address to perimeter blocklists for 72 hours.
  2. Search all corporate mailboxes for identical message hashes (`email_hash`) received within the last 48 hours and purge matching copies.
  3. If user has active browser sessions referencing the detected URL, immediately invalidate active session tokens and force password reset.
- **Analyst SLA**: High-priority alert dispatched to on-call SOC tier-2 responder. Initial containment verification required within 15 minutes.

---

## 3. Policy POL-SEC-102: Financial Transactions and Out-of-Band Verification

- **Rule**: Any email requesting fund transfers, wire transactions, modifications to supplier banking details, or executive gift-card purchases MUST undergo out-of-band verification prior to execution.
- **Verification Requirement**: The recipient must independently verify the request via a known, pre-established phone number or in-person confirmation. Verifying via phone numbers, links, or contact details provided within the suspicious email body is strictly prohibited.
- **Enforcement**: Emails matching financial payment keywords combined with external sender addresses must be automatically escalated to at least `High` risk tier regardless of classical ML scores.

---

## 4. Policy POL-SEC-103: Credential and Authentication Requests

- **Rule**: Internal IT support, system administrators, and executive leadership will NEVER request user passwords, MFA codes, or recovery seed phrases via email.
- **Password Reset Standard**: Legitimate password reset notifications never contain direct password entry fields inside an email body, nor do they link to raw IP addresses or non-corporate root domains.
- **Enforcement**: Any inbound email soliciting password submission or containing forms requesting authentication secrets must be classified as an intentional credential harvesting lure and assigned to the `Critical` risk tier.

---

## 5. Policy POL-SEC-104: External Sender and DMARC Alignment Rules

- **External Sender Tagging**: All messages received from outside the organization must carry an `[EXTERNAL]` tag prepended to the email subject.
- **DMARC Enforcement**:
  - Inbound messages failing DMARC verification where the sender domain claims to be an internal corporate domain (`from: @our-company.com`) must be rejected or quarantined at the perimeter gateway.
  - Emails exhibiting display name spoofing (internal employee name paired with external free email address) must be flagged with `urgency_language` or `suspicious_sender` signals.
