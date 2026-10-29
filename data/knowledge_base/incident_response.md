# Incident Response Playbook and Escalation Procedures

> [!IMPORTANT]
> **MOCK INCIDENT RESPONSE PLAYBOOK — CREATED FOR PROJECT DEMONSTRATION ONLY**  
> This playbook defines fictional incident response workflows, service level agreements (SLAs), and escalation protocols created specifically for the **AI Phishing Risk & Security Triage Platform**. It provides grounding context for the RAG and agent triage workflow.

---

## 1. Overview and Response Objectives

When an incoming email is identified as suspicious or malicious by the triage engine, incident response procedures ensure rapid containment, impact limitation, and thorough post-incident analysis. While structured around the standard lifecycle phases of NIST SP 800-61 Rev. 2 (Preparation, Detection & Analysis, Containment, Eradication, and Recovery), the specific action thresholds and SLAs in this document are project-specific fictional standards.

---

## 2. Response Lifecycle Procedures

### Phase 1: Detection, Analysis, and Automated Triage
1. **Automated Evaluation**: Ingestion through `POST /api/v1/analyze` generates model probabilities (Random Forest, DistilBERT), evaluates heuristic rule signals, and calculates the application risk score (0–100).
2. **Context Enrichment (RAG)**: The triage engine queries the security knowledge base to retrieve relevant attack profiles (MITRE ATT&CK references) and matching internal policies.
3. **Evidence Synthesis**: If the score meets or exceeds the escalation threshold, an investigation ticket is generated with:
   - Analysis UUID and request ID
   - Calculated risk score and classification tier
   - SHA-256 hash of normalized email body
   - Extracted indicators of compromise (IOCs: URLs, domains, sender IPs)
   - Retrieved policy violations and MITRE technique IDs

### Phase 2: Containment
1. **Mailbox Isolation**:
   - For `High` risk emails (60.0–79.9): Ensure message remains in central quarantine.
   - For `Critical` risk emails (80.0–100.0): Immediately purge message from all target mailboxes via tenant-wide API call.
2. **Perimeter Network Containment**:
   - Push malicious URLs and domains to email gateway and firewall blocklists.
   - Block originating IP addresses at the perimeter security boundary.
3. **Identity and Session Containment**:
   - If user interaction logs indicate the recipient accessed an embedded link:
     - Terminate all active cloud and SSO sessions for the user.
     - Temporarily restrict account privileges to prevent lateral movement.

### Phase 3: Eradication
1. **Tenant-Wide Search & Purge**:
   - Execute a cross-mailbox query using the message's `email_hash` or subject line to identify all identical or variant messages delivered to other employees.
   - Permanently delete all instances from inboxes, junk folders, and trash.
2. **Infrastructure Takedown**:
   - Report phishing domains, hosting infrastructure, and look-alike domains to registrars, cloud hosts, and APWG reporting channels (`reportphishing@apwg.org`).

### Phase 4: Recovery
1. **Account Restoration**:
   - Reset compromised credentials using an out-of-band verification procedure (e.g., manager approval via secure phone call).
   - Re-issue FIDO2 hardware tokens or re-register MFA authenticator apps.
2. **False Positive Remediation**:
   - If manual analyst review determines the email was legitimate business communication, release the message from quarantine, notify the recipient, and log a false-positive feedback record to the database for model fine-tuning.

### Phase 5: Post-Incident Review and Continuous Improvement
1. **Threat Intelligence Update**: Record verified IOCs into the internal threat intelligence registry.
2. **Training Data Enhancement**: Flag false-positive or false-negative records for periodic ML feature and model retraining review.

---

## 3. SLA and Escalation Matrix

| Risk Classification | Application Score | Containment SLA | Responsible Role | Mandatory Escalation Criteria |
|---|---|---|---|---|
| **Low** | 0.0 – 39.9 | N/A (Standard Delivery) | Automated Gateway | None |
| **Medium** | 40.0 – 59.9 | 4 hours (Audit review) | Tier-1 Security Analyst | User reports clicking unverified link |
| **High** | 60.0 – 79.9 | 1 hour | Tier-1 Security Analyst | Credential submission or executive impersonation |
| **Critical** | 80.0 – 100.0 | 15 minutes | Tier-2 Senior Analyst / Incident Commander | Active session compromise, malware execution, or wire fraud attempt |

---

## 4. Scenario-Specific Escalation Playbooks

### Playbook SC-01: Credential Harvesting with Suspected User Submission
- **Trigger**: Critical-tier email with an AiTM login mirror link where user telemetry shows outbound HTTP POST to the suspicious URL.
- **Immediate Actions**:
  1. Revoke active refresh tokens and user sessions within 5 minutes.
  2. Force immediate password reset.
  3. Inspect identity provider sign-in logs for anomalous IP addresses, unfamiliar user agents, or geographically improbable access.
  4. Review email forwarding rules created within the last 2 hours.

### Playbook SC-02: Executive Impersonation / CEO Wire Fraud
- **Trigger**: Email claiming to be from senior leadership requesting immediate financial wire transfer or payroll modification.
- **Immediate Actions**:
  1. Direct contact with the impersonated executive via pre-established telephone line to confirm fraudulent nature.
  2. Immediate notification to the corporate treasury and accounts payable team to hold all pending outgoing disbursements.
  3. Extract banking details and recipient account numbers from email body; report to receiving financial institution's fraud unit.
