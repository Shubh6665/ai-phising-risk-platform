# Phishing Indicators and Social Engineering Patterns

> **Document Type**: Authoritative Technical Guidance  
> **Target Audience**: Security Analysts, Automated Triage Engines, Risk Aggregation Systems  
> **Sources**: National Institute of Standards and Technology (NIST), Cybersecurity and Infrastructure Security Agency (CISA), Anti-Phishing Working Group (APWG)

---

## 1. Overview and Core Indicators

Phishing is a form of social engineering where an attacker impersonates a trustworthy entity to deceive recipients into revealing sensitive credentials, executing malicious attachments, transferring funds, or granting unauthorized system access. Detection relies on evaluating indicators across multiple dimensions: sender identity, textual language, embedded hyperlinks, attachment characteristics, and message formatting.

Authoritative references:
- **CISA**: [Recognizing and Reporting Phishing](https://www.cisa.gov/secure-our-world/recognize-and-report-phishing)
- **NIST**: [NIST SP 800-177 Rev. 1: Trustworthy Email](https://csrc.nist.gov/publications/detail/sp/800-177/rev-1/final)
- **APWG**: [Phishing Activity Trends Reports](https://apwg.org/trendsreports/)

---

## 2. Sender Identity and Header Anomalies

Attackers manipulate email transport headers and envelope details to mislead users regarding message origin. Key red flags include:

### Display Name Spoofing
- The sender display name shows a recognized brand or executive (e.g., "IT Support Helpdesk" or "Executive Office"), but the actual SMTP `From` address belongs to a generic freemail provider (e.g., `gmail.com`, `outlook.com`) or an unrelated compromised external domain.
- *Indicator check*: Discrepancy between display name string and the domain in the RFC 5322 `From:` address.

### Domain Spoofing and Typosquatting
- **Exact Domain Spoofing**: Sending emails with an forged `From` header matching an authoritative domain when SPF (Sender Policy Framework), DKIM (DomainKeys Identified Mail), or DMARC (Domain-based Message Authentication, Reporting, and Conformance) policies are absent or not enforced (`p=none`).
- **Look-Alike Domains (Typosquatting & Combosquatting)**: Registering domains visually or phonetically similar to legitimate brands (e.g., `micros0ft.com`, `paypal-security-update.com`, `amaz0n-support.net`).
- **Homoglyph & Punycode Attacks**: Using internationalized domain names (IDN) with Cyrillic or Greek characters that appear visually indistinguishable from Latin letters in standard user agents (e.g., `xn--...`).
- *Indicator check*: High hostname dot counts, hyphens in brand names, or unaligned sender domains.

### Reply-To Mismatch
- The `From:` header presents a legitimate organizational address, but the `Reply-To:` header points to an external, attacker-controlled address. Any response from the victim routes directly to the adversary.
- *Indicator check*: Mismatch between `From` domain and `Reply-To` domain.

---

## 3. Social Engineering and Behavioral Manipulation

Phishing language leverages psychological triggers to bypass critical thinking and induce impulsive compliance. NIST and CISA identify five primary persuasion tactics:

### Artificial Urgency and Time Pressure
- Demanding immediate action under threat of severe negative consequences (e.g., "Account suspended within 24 hours", "Unauthorized transaction pending: verify immediately", "Urgent wire transfer required before end-of-day").
- *Indicator check*: High frequency of urgency keywords (`urgent`, `immediate`, `action required`, `suspended`, `expire`, `risk`).

### Impersonation of Authority
- Masquerading as senior executives, legal counsel, regulatory agencies, or internal IT departments to leverage organizational obedience.
- *Indicator check*: Requests originating ostensibly from leadership demanding bypass of standard procedures.

### Fear, Intimidation, or Account Invalidation
- Falsely claiming security breaches, compromised passwords, tax penalties, or legal subpoenas to panic the recipient into following malicious instructions.
- *Indicator check*: Threats of account closure, financial penalty, or legal action.

### False Rewards and Scarcity (Greed / Opportunity)
- Offering unexpected bonuses, prize notifications, tax refunds, gift cards, or promotional benefits requiring the user to "claim now" by submitting credentials or personal details.
- *Indicator check*: Unsolicited compensation or benefit notifications requiring authentication.

---

## 4. Hyperlink and URL Indicators

Malicious links constitute the primary vector for credential harvesting and drive-by malware downloads.

### IP-Address Hostnames
- Legitimate organizations rarely use raw numerical IP addresses in public customer links. URLs featuring direct IPv4 or IPv6 hostnames (e.g., `http://192.168.1.10/login` or `http://45.33.32.156/auth`) strongly correlate with hostile staging infrastructure.
- *Indicator check*: Hostname matches an IP address format (`has_ip_address_url`).

### Link Text vs. Underlying Anchor Destination
- The visible text within an HTML hyperlink displays an authentic, trusted destination (e.g., `https://www.bank.com/secure`), but the underlying HTML `href` attribute targets an external phishing domain (e.g., `href="http://phish-login.example.com"`).
- *Indicator check*: String mismatch between anchor text and destination `href`.

### Deep Subdomain Chaining and Brand Prefixes
- Placing trusted brand names inside multi-level subdomains to deceive casual inspection (e.g., `https://login.microsoft.com.account-verification.attacker-domain.com/auth`). The effective top-level domain plus one (eTLD+1) is `attacker-domain.com`, not `microsoft.com`.
- *Indicator check*: Subdomain depth > 3 or brand tokens appearing strictly in subdomain components.

### URL Shorteners and Open Redirects
- Utilizing public shortening services (e.g., `bit.ly`, `tinyurl.com`) or exploiting unvalidated redirects on reputable domains to conceal the true landing page destination from perimeter security filters.
- *Indicator check*: Shortener hostnames or redirect parameters (`?redirect=`, `?url=`, `?next=`).

---

## 5. Attachment and Payload Red Flags

Email attachments frequently deliver malware or harvest credentials via indirect execution:

- **Double Extensions**: Concealing executable payloads using confusing naming conventions (e.g., `invoice_march2026.pdf.exe` or `statement.docx.vbs`).
- **Macro-Enabled Documents**: Requesting users to "Enable Content" or "Enable Macros" in Microsoft Office formats (`.docm`, `.xlsm`) to execute embedded Visual Basic scripts.
- **HTML Smuggling & SVG Attachments**: Delivering self-contained HTML files or SVG vectors that construct and drop malicious binaries directly within the victim's web browser using JavaScript blobs, evading network gateway inspection.
- **Password-Protected Archives**: Packaging malware inside encrypted ZIP, 7z, or RAR files with the decryption password written in the email body, preventing automated gateway scanning.

---

## 6. Authoritative Source Traceability Matrix

| Indicator Category | Authoritative Reference | Official Recommendation / Finding |
|---|---|---|
| **Email Authentication** | NIST SP 800-177 Rev. 1, Sec 4 | Mandate SPF, DKIM, and DMARC with strict reject/quarantine alignment. |
| **Urgency & Social Cues** | CISA / Social Engineering Guidance | Treat unprompted urgency, fear, and deadline pressure as primary indicators. |
| **Typosquatting / Domains** | APWG Phishing Trends | Monitored exponential increases in look-alike domains and free TLS certificates. |
| **Hyperlink Deception** | CISA Technical Tip ST04-014 | Never click unverified embedded links; inspect target URL domain suffixes. |
| **Malicious Attachments** | NIST SP 800-61 Rev. 2, Sec 3.2 | Block unapproved executable, script, and macro-enabled attachments at the boundary. |
