"""LangGraph investigation workflow for phishing analysis.

Implements a deterministic state graph coordinating input validation, knowledge-base
retrieval, lexical URL structure analysis, and policy triage guidance lookup.
"""

from typing import Any, Callable
import structlog
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from src.agent.llm import generate_investigation_explanation
from src.agent.schemas import KnowledgeSearchChunk
from src.agent.state import (
    PhishingAnalysisState,
    compute_deterministic_escalation,
)
from src.agent.tools.url_analyzer import analyze_url_structure
from src.agent.tools.policy_lookup import lookup_policy_guidance
from src.agent.tools.knowledge_search import search_security_knowledge
from src.features.url_features import extract_urls
from src.rag.embeddings import Embedder

logger = structlog.get_logger(__name__)


def validate_input_node(state: PhishingAnalysisState) -> dict[str, Any]:
    """Validate incoming state fields, identifiers, and probability bounds."""
    errors = list(state.get("tool_errors", []))
    tool_outputs = list(state.get("tool_outputs", []))

    request_id = state.get("request_id")
    if not request_id or not isinstance(request_id, str) or not request_id.strip():
        errors.append("Invalid or missing 'request_id'.")

    email_text = state.get("email_text")
    if email_text is None or not isinstance(email_text, str) or not email_text.strip():
        errors.append("Invalid or empty 'email_text'.")

    risk_score = state.get("risk_score")
    if risk_score is None or not isinstance(risk_score, (int, float)) or not (0.0 <= float(risk_score) <= 100.0):
        errors.append(f"Invalid 'risk_score' ({risk_score}); must be numeric between 0.0 and 100.0.")

    ml_prob = state.get("ml_probability")
    if ml_prob is None or not isinstance(ml_prob, (int, float)) or not (0.0 <= float(ml_prob) <= 1.0):
        errors.append(f"Invalid 'ml_probability' ({ml_prob}); must be numeric between 0.0 and 1.0.")

    nlp_prob = state.get("nlp_probability")
    if nlp_prob is None or not isinstance(nlp_prob, (int, float)) or not (0.0 <= float(nlp_prob) <= 1.0):
        errors.append(f"Invalid 'nlp_probability' ({nlp_prob}); must be numeric between 0.0 and 1.0.")

    validation_status = "passed" if not errors else "failed"
    tool_outputs.append({
        "tool": "validate_input",
        "status": validation_status,
        "error_count": len(errors),
    })

    logger.debug(
        "investigation_node_executed",
        node="validate_input",
        request_id=request_id,
        status=validation_status,
    )

    return {
        "tool_errors": errors,
        "tool_outputs": tool_outputs,
    }


def route_after_validation(state: PhishingAnalysisState) -> str:
    """Conditional edge: route to retrieval if valid, or skip to aggregation if errors exist."""
    errors = state.get("tool_errors", [])
    if errors:
        return "aggregate_findings"
    return "retrieve_knowledge"


def create_retrieve_knowledge_node(
    embedder: Embedder | None = None,
) -> Callable[[PhishingAnalysisState], dict[str, Any]]:
    """Node factory creating the knowledge retrieval node with injected embedder."""
    def retrieve_knowledge_node(state: PhishingAnalysisState) -> dict[str, Any]:
        tool_outputs = list(state.get("tool_outputs", []))
        tool_errors = list(state.get("tool_errors", []))

        # Query construction: combines subject and body prefix (up to 300 chars)
        subject = state.get("email_subject") or ""
        body = state.get("email_text") or ""
        query = f"{subject} {body[:300]}".strip()
        if not query:
            query = "phishing security guidance"

        search_result = search_security_knowledge(
            query=query,
            top_k=3,
            embedder=embedder,
        )

        evidence_items: list[dict[str, Any]] = [
            chunk.model_dump() for chunk in search_result.chunks
        ]

        if search_result.status == "error":
            tool_errors.append(f"Knowledge search error: {search_result.error_message}")

        tool_outputs.append({
            "tool": "knowledge_search",
            "status": search_result.status,
            "results_count": search_result.results_count,
        })

        logger.debug(
            "investigation_node_executed",
            node="retrieve_knowledge",
            request_id=state.get("request_id"),
            status=search_result.status,
            results_count=search_result.results_count,
        )

        return {
            "retrieved_evidence": evidence_items,
            "tool_outputs": tool_outputs,
            "tool_errors": tool_errors,
        }

    return retrieve_knowledge_node


def analyze_urls_node(state: PhishingAnalysisState) -> dict[str, Any]:
    """Inspect all URLs present in the email text using local lexical parsing."""
    tool_outputs = list(state.get("tool_outputs", []))
    email_text = state.get("email_text") or ""

    # Reuse explicit extracted_urls if provided, or extract from email body text
    urls = state.get("extracted_urls")
    if not urls:
        urls = extract_urls(email_text)

    observations = [analyze_url_structure(u) for u in urls]
    total_indicators = sum(obs.indicator_count for obs in observations)

    tool_outputs.append({
        "tool": "url_structure_analyzer",
        "status": "completed",
        "urls_analyzed": len(observations),
        "suspicious_indicators_count": total_indicators,
    })

    logger.debug(
        "investigation_node_executed",
        node="analyze_urls",
        request_id=state.get("request_id"),
        urls_analyzed=len(observations),
        total_indicators=total_indicators,
    )

    return {
        "url_analysis": [obs.model_dump() for obs in observations],
        "tool_outputs": tool_outputs,
    }


def lookup_policy_node(state: PhishingAnalysisState) -> dict[str, Any]:
    """Retrieve operational triage actions and technical defensive controls for the risk score."""
    tool_outputs = list(state.get("tool_outputs", []))
    tool_errors = list(state.get("tool_errors", []))

    risk_score = float(state.get("risk_score", 0.0))
    policy_data: dict[str, Any] | None = None

    try:
        guidance = lookup_policy_guidance(risk_score)
        policy_data = guidance.model_dump()
        tool_outputs.append({
            "tool": "policy_lookup",
            "status": "completed",
            "classification": guidance.classification,
            "action": guidance.triage_action,
        })
    except Exception as e:
        tool_errors.append(f"Policy lookup failed: {str(e)}")
        tool_outputs.append({
            "tool": "policy_lookup",
            "status": "error",
            "error": str(e),
        })

    logger.debug(
        "investigation_node_executed",
        node="lookup_policy",
        request_id=state.get("request_id"),
        classification=policy_data.get("classification") if policy_data else None,
    )

    return {
        "policy_guidance": policy_data,
        "tool_outputs": tool_outputs,
        "tool_errors": tool_errors,
    }


def aggregate_findings_node(state: PhishingAnalysisState) -> dict[str, Any]:
    """Aggregate tool outputs and re-verify deterministic escalation rules."""
    tool_outputs = list(state.get("tool_outputs", []))

    risk_score = float(state.get("risk_score", 0.0))
    ml_prob = float(state.get("ml_probability", 0.0))
    nlp_prob = float(state.get("nlp_probability", 0.0))

    requires_escalation, escalation_reason = compute_deterministic_escalation(
        risk_score=risk_score,
        ml_probability=ml_prob,
        nlp_probability=nlp_prob,
    )

    urls_count = len(state.get("url_analysis", []))
    evidence_count = len(state.get("retrieved_evidence", []))
    has_policy = state.get("policy_guidance") is not None

    tool_outputs.append({
        "tool": "aggregate_findings",
        "status": "completed",
        "requires_escalation": requires_escalation,
        "summary": {
            "urls_analyzed": urls_count,
            "evidence_retrieved": evidence_count,
            "policy_looked_up": has_policy,
            "errors_logged": len(state.get("tool_errors", [])),
        },
    })

    logger.info(
        "investigation_workflow_completed",
        request_id=state.get("request_id"),
        analysis_id=state.get("analysis_id"),
        risk_score=risk_score,
        classification=state.get("classification"),
        requires_escalation=requires_escalation,
        urls_analyzed=urls_count,
        evidence_retrieved=evidence_count,
    )

    return {
        "requires_escalation": requires_escalation,
        "escalation_reason": escalation_reason,
        "tool_outputs": tool_outputs,
    }


def create_generate_explanation_node(
    primary_llm: BaseChatModel | None = None,
    fallback_llm: BaseChatModel | None = None,
) -> Callable[[PhishingAnalysisState], dict[str, Any]]:
    """Node factory creating the grounded explanation generation node."""
    def generate_explanation_node(state: PhishingAnalysisState) -> dict[str, Any]:
        tool_outputs = list(state.get("tool_outputs", []))

        explanation = generate_investigation_explanation(
            state=state,
            primary_llm=primary_llm,
            fallback_llm=fallback_llm,
        )

        tool_outputs.append({
            "tool": "explanation_generator",
            "status": explanation.generation_status,
            "provider_used": explanation.provider_used,
            "evidence_references_count": len(explanation.evidence_references),
        })

        logger.debug(
            "investigation_node_executed",
            node="generate_explanation",
            request_id=state.get("request_id"),
            provider_used=explanation.provider_used,
            generation_status=explanation.generation_status,
        )

        return {
            "explanation": explanation.summary,
            "recommendations": explanation.recommended_actions,
            "structured_explanation": explanation.model_dump(),
            "tool_outputs": tool_outputs,
        }

    return generate_explanation_node


def route_after_aggregation(state: PhishingAnalysisState) -> str:
    """Conditional edge: skip LLM explanation if validation errors occurred."""
    if state.get("tool_errors"):
        return END
    return "generate_explanation"


def build_investigation_graph(
    embedder: Embedder | None = None,
    primary_llm: BaseChatModel | None = None,
    fallback_llm: BaseChatModel | None = None,
) -> CompiledStateGraph:
    """Build and compile the Phase 8 LangGraph investigation workflow.

    Sequential, deterministic flow:
    START -> validate_input -> (conditional: retrieve_knowledge or aggregate_findings)
          -> analyze_urls -> lookup_policy -> aggregate_findings
          -> (conditional: generate_explanation or END) -> END
    """
    builder = StateGraph(PhishingAnalysisState)

    # 1. Register nodes
    builder.add_node("validate_input", validate_input_node)
    builder.add_node("retrieve_knowledge", create_retrieve_knowledge_node(embedder=embedder))
    builder.add_node("analyze_urls", analyze_urls_node)
    builder.add_node("lookup_policy", lookup_policy_node)
    builder.add_node("aggregate_findings", aggregate_findings_node)
    builder.add_node(
        "generate_explanation",
        create_generate_explanation_node(primary_llm=primary_llm, fallback_llm=fallback_llm),
    )

    # 2. Register edges
    builder.add_edge(START, "validate_input")

    # Conditional edge: validate_input branches to retrieve_knowledge or directly to aggregate_findings
    builder.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {
            "retrieve_knowledge": "retrieve_knowledge",
            "aggregate_findings": "aggregate_findings",
        },
    )

    builder.add_edge("retrieve_knowledge", "analyze_urls")
    builder.add_edge("analyze_urls", "lookup_policy")
    builder.add_edge("lookup_policy", "aggregate_findings")

    # Conditional edge: aggregate_findings skips explanation if tool_errors exist
    builder.add_conditional_edges(
        "aggregate_findings",
        route_after_aggregation,
        {
            "generate_explanation": "generate_explanation",
            END: END,
        },
    )

    builder.add_edge("generate_explanation", END)

    return builder.compile()


def run_investigation(
    initial_state: PhishingAnalysisState,
    embedder: Embedder | None = None,
    primary_llm: BaseChatModel | None = None,
    fallback_llm: BaseChatModel | None = None,
) -> PhishingAnalysisState:
    """Execute the full compiled investigation workflow on the given initial state."""
    graph = build_investigation_graph(
        embedder=embedder,
        primary_llm=primary_llm,
        fallback_llm=fallback_llm,
    )
    result = graph.invoke(initial_state)
    return result

