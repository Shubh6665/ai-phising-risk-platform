"""Pydantic schemas for agent state, tool inputs, and tool outputs."""

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# 1. URL Analyzer Tool Schemas
# ============================================================================

class URLAnalyzerInput(BaseModel):
    """Input schema for URL structure analysis."""
    model_config = ConfigDict(frozen=True)

    url: str = Field(
        ...,
        min_length=1,
        description="The URL to structurally analyze without making network requests.",
    )


class URLObservation(BaseModel):
    """Detailed structural observations extracted from a single URL."""
    model_config = ConfigDict(frozen=True)

    url: str = Field(..., description="The parsed URL string.")
    scheme: str = Field(..., description="URL scheme (e.g., http, https, or mailto).")
    hostname: str | None = Field(default=None, description="Host / domain name.")
    port: int | None = Field(default=None, description="Explicit port number if present.")
    path: str = Field(default="", description="Hierarchical path segment.")
    query: str = Field(default="", description="Query parameter string.")
    is_ip_literal: bool = Field(default=False, description="True if hostname is an IPv4 or IPv6 address.")
    ip_type: str | None = Field(default=None, description="'ipv4', 'ipv6', or None if not an IP.")
    has_userinfo: bool = Field(default=False, description="True if URL contains '@' userinfo credentials syntax.")
    has_punycode: bool = Field(default=False, description="True if hostname contains 'xn--' IDN punycode prefix.")
    has_unusual_port: bool = Field(default=False, description="True if a non-standard web port (not 80/443) is specified.")
    subdomain_depth: int = Field(default=0, description="Count of domain labels preceding the primary domain.")
    url_length: int = Field(default=0, description="Total character length of the URL.")
    suspicious_indicators: list[str] = Field(
        default_factory=list,
        description="Structural anomalies detected (e.g. IP host, userinfo token, punycode).",
    )
    indicator_count: int = Field(default=0, description="Total count of structural anomaly flags.")
    notes: str = Field(
        default="Indicators represent structural anomalies and must be correlated with threat intelligence; "
                "presence of an indicator does not alone confirm maliciousness.",
        description="Operational context for analysts.",
    )


# ============================================================================
# 2. Policy / Triage Lookup Tool Schemas
# ============================================================================

class PolicyLookupInput(BaseModel):
    """Input schema for project triage policy lookup."""
    model_config = ConfigDict(frozen=True)

    risk_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Application composite risk score (0.0 to 100.0) from the ensemble.",
    )


class PolicyGuidanceResult(BaseModel):
    """Project triage actions and recommended technical controls for a given risk score."""
    model_config = ConfigDict(frozen=True)

    risk_score: float = Field(..., ge=0.0, le=100.0, description="Input composite risk score.")
    classification: str = Field(..., description="Operational triage tier: Low, Medium, High, or Critical.")
    score_range: str = Field(..., description="Numerical score bracket (e.g. '60.0 – 79.9').")
    triage_action: str = Field(..., description="Primary automated action (e.g. 'Automated Quarantine').")
    technical_handling: str = Field(..., description="SOC / mail gateway technical routing instructions.")
    recommended_controls: list[str] = Field(
        default_factory=list,
        description="Applicable defensive controls from NIST SP 800-61 / CISA guidance.",
    )
    source_attribution: str = Field(..., description="Issuing bodies and canonical source references.")
    is_project_triage_choice: bool = Field(
        default=True,
        description="True indicates score cutoffs are project technical choices, not universal NIST/CISA mandates.",
    )
    disclaimer: str = Field(
        default="This guidance specifies application triage choices for this platform and does not constitute "
                "an organization-approved enterprise security policy.",
        description="Governance disclaimer.",
    )


# ============================================================================
# 3. Knowledge Base Search Tool Schemas
# ============================================================================

class KnowledgeSearchInput(BaseModel):
    """Input schema for security knowledge base retrieval."""
    model_config = ConfigDict(frozen=True)

    query: str = Field(
        ...,
        min_length=1,
        description="Search query describing a phishing indicator, attack pattern, or security control.",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of relevant knowledge-base chunks to retrieve.",
    )


class KnowledgeSearchChunk(BaseModel):
    """A single retrieved chunk from the persistent security knowledge base."""
    model_config = ConfigDict(frozen=True)

    chunk_id: str = Field(..., description="Deterministic chunk identifier.")
    content: str = Field(..., description="Verbatim markdown excerpt.")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Normalized cosine similarity [0.0, 1.0].")
    document_name: str = Field(..., description="Source document filename (e.g. attack_patterns.md).")
    document_title: str | None = Field(default=None, description="Title of the source document.")
    heading: str | None = Field(default=None, description="Section heading hierarchy.")
    document_type: str = Field(..., description="Metadata label: 'source_backed_guidance' or 'mock'.")
    source_attribution: str = Field(..., description="Authoritative issuing body attribution.")
    is_mock: bool = Field(default=False, description="Whether the chunk contains synthetic mock content.")


class KnowledgeSearchResult(BaseModel):
    """Aggregate result from a knowledge base search invocation."""
    model_config = ConfigDict(frozen=True)

    query: str = Field(..., description="Executed search query string.")
    status: str = Field(..., description="'retrieved', 'empty', or 'error'.")
    results_count: int = Field(default=0, description="Number of chunks returned.")
    chunks: list[KnowledgeSearchChunk] = Field(default_factory=list, description="Retrieved chunks.")
    error_message: str | None = Field(default=None, description="Error details if status is 'error'.")


# ============================================================================
# 4. LLM Explanation & Grounding Schemas (Phase 8C)
# ============================================================================

class SanitizedURLObservation(BaseModel):
    """Sanitized representation of a URL observation stripped of sensitive query strings/tokens."""
    model_config = ConfigDict(frozen=True)

    scheme: str = Field(..., description="URL scheme (http, https).")
    hostname: str | None = Field(default=None, description="Host / domain name.")
    port: int | None = Field(default=None, description="Port number if specified.")
    is_ip_literal: bool = Field(default=False, description="True if host is an IP literal.")
    has_userinfo: bool = Field(default=False, description="True if authority contains '@' userinfo syntax.")
    has_punycode: bool = Field(default=False, description="True if host contains 'xn--' punycode prefix.")
    has_unusual_port: bool = Field(default=False, description="True if non-standard web port specified.")
    subdomain_depth: int = Field(default=0, description="Nesting depth of subdomains.")
    indicator_count: int = Field(default=0, description="Count of detected anomalies.")
    suspicious_indicators: list[str] = Field(default_factory=list, description="List of detected anomalies.")


class InvestigationExplanation(BaseModel):
    """Structured security investigation narrative and recommendations generated by LLM."""
    model_config = ConfigDict(frozen=True)

    summary: str = Field(
        ...,
        description="Executive summary of the email triage investigation and risk level.",
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Specific observed risk indicators (e.g. IP-literal host, urgency cues, high ML probability).",
    )
    risk_explanation: str = Field(
        ...,
        description="Detailed contextual explanation explaining why the email received its risk classification.",
    )
    recommended_actions: list[str] = Field(
        default_factory=list,
        description="Recommended defensive response steps aligned with NIST SP 800-61 and CISA guidance.",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Investigation limitations (e.g. offline URL parsing only, no dynamic sandbox execution).",
    )
    evidence_references: list[str] = Field(
        default_factory=list,
        description="Identifiers or citations of retrieved security knowledge base chunks used in the explanation.",
    )
    provider_used: str | None = Field(
        default=None,
        description="LLM provider that generated the response ('google', 'groq', or None if degraded).",
    )
    generation_status: str = Field(
        default="completed",
        description="Status of generation: 'completed', 'fallback', 'degraded', 'error', or 'disabled'.",
    )


