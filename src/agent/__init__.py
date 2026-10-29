"""Agent package: state, schemas, and deterministic investigation tools."""

from src.agent.schemas import (
    URLAnalyzerInput,
    URLObservation,
    PolicyLookupInput,
    PolicyGuidanceResult,
    KnowledgeSearchInput,
    KnowledgeSearchChunk,
    KnowledgeSearchResult,
    SanitizedURLObservation,
    InvestigationExplanation,
)
from src.agent.state import (
    PhishingAnalysisState,
    compute_deterministic_escalation,
    create_initial_agent_state,
)
from src.agent.tools import (
    analyze_url_structure,
    analyze_urls_in_text,
    url_structure_analyzer_tool,
    lookup_policy_guidance,
    policy_triage_lookup_tool,
    search_security_knowledge,
    knowledge_base_search_tool,
)
from src.agent.llm import (
    generate_investigation_explanation,
    generate_deterministic_degraded_explanation,
    get_primary_llm,
    get_fallback_llm,
    sanitize_url_observations,
    build_minimized_investigation_prompt,
)
from src.agent.graph import (
    build_investigation_graph,
    run_investigation,
    validate_input_node,
    analyze_urls_node,
    lookup_policy_node,
    aggregate_findings_node,
    create_generate_explanation_node,
)

__all__ = [
    "URLAnalyzerInput",
    "URLObservation",
    "PolicyLookupInput",
    "PolicyGuidanceResult",
    "KnowledgeSearchInput",
    "KnowledgeSearchChunk",
    "KnowledgeSearchResult",
    "SanitizedURLObservation",
    "InvestigationExplanation",
    "PhishingAnalysisState",
    "compute_deterministic_escalation",
    "create_initial_agent_state",
    "analyze_url_structure",
    "analyze_urls_in_text",
    "url_structure_analyzer_tool",
    "lookup_policy_guidance",
    "policy_triage_lookup_tool",
    "search_security_knowledge",
    "knowledge_base_search_tool",
    "generate_investigation_explanation",
    "generate_deterministic_degraded_explanation",
    "get_primary_llm",
    "get_fallback_llm",
    "sanitize_url_observations",
    "build_minimized_investigation_prompt",
    "build_investigation_graph",
    "run_investigation",
    "validate_input_node",
    "analyze_urls_node",
    "lookup_policy_node",
    "aggregate_findings_node",
    "create_generate_explanation_node",
]

