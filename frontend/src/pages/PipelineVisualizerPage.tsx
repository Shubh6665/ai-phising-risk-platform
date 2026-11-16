import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  ArrowDown,
  ChevronRight,
  Code2,
  FileJson,
  GitBranch,
  Layers,
  Cpu,
  Database,
  Search,
  Bot,
  Zap,
  PackageCheck,
  X,
} from "lucide-react";

/* ─── Types ──────────────────────────────────────── */
interface PipelineStep {
  id: string;
  num: number;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  subtitle: string;
  route: string;
  file: string;
  inputLabel: string;
  inputSchema: string;
  outputLabel: string;
  outputSchema: string;
  operations: string[];
  spec: string;
}

/* ─── Pipeline Data ────────────────────────────────── */
const STEPS: PipelineStep[] = [
  {
    id: "gateway",
    num: 1,
    icon: Zap,
    title: "FastAPI Gateway & Validation",
    subtitle: "HTTP ingestion, UUID middleware, Pydantic v2 schema enforcement",
    route: "POST /api/v1/analyze",
    file: "src/api/routes/analyze.py",
    inputLabel: "HTTP request body",
    inputSchema: `{
  "text":    string   // min_length=1, non-whitespace-only
  "subject": string?  // optional email subject
}`,
    outputLabel: "Dependency-injected service call",
    outputSchema: `{
  "request_id": UUID v4   // from RequestIDMiddleware
  "text":       str
  "subject":    str | None
}`,
    operations: [
      "Uvicorn ASGI server receives HTTP/1.1 or HTTP/2 connection and dispatches to FastAPI router.",
      "RequestIDAndLoggingMiddleware generates a UUID v4, injects into request.state, and starts structured logging.",
      "CORSMiddleware validates request origin against whitelist (localhost:5173, 127.0.0.1:5173).",
      "Pydantic v2 AnalyzeRequest enforces min_length=1, rejects whitespace-only bodies with 422 response.",
      "FastAPI Depends() provisions classical model, NLP model, tokenizer, DB session, RAG retriever, and LangGraph graph.",
    ],
    spec: "Pydantic V2 Rust core validator · RFC 4122 UUID v4 · HTTP/ASGI multiplexing",
  },
  {
    id: "features",
    num: 2,
    icon: Layers,
    title: "Text Preprocessing & Feature Engineering",
    subtitle: "19 handcrafted lexical, structural, and heuristic signal extractors",
    route: "src.features.feature_pipeline.extract_features()",
    file: "src/features/feature_pipeline.py",
    inputLabel: "Raw subject + body DataFrame",
    inputSchema: `DataFrame {
  "subject": Series[str]
  "body":    Series[str]
}`,
    outputLabel: "19-dimensional feature vector",
    outputSchema: `DataFrame [1 × 19] {
  "url_count", "has_ip_address_url",
  "suspicious_tld_count", "at_symbol_count",
  "subdomain_depth_max", "phishing_keyword_count",
  "urgency_keyword_count", "excessive_cap_ratio",
  ... (11 more)
}`,
    operations: [
      "build_email_text() concatenates subject + body into normalized combined string.",
      "extract_url_features() uses RFC 3986 regex to detect URL schemes and decompose URIs.",
      "IP literal detection: regex matches /http:\\/\\/\\d{1,3}(\\.\\d{1,3}){3}/ pattern for raw IP hosts.",
      "extract_text_features() tokenizes content and scores against curated phishing urgency lexicons.",
      "Column order is validated against training-time feature schema to prevent distribution shift.",
    ],
    spec: "RFC 3986 URI parsing · Regex tokenization · Lexical entropy ratios",
  },
  {
    id: "inference",
    num: 3,
    icon: Cpu,
    title: "Dual ML + Transformer Inference",
    subtitle: "Random Forest (tabular) ∥ Fine-tuned DistilBERT (contextual) — independent parallel paths",
    route: "RandomForest.predict_proba() ∥ sample_probabilities(DistilBERT)",
    file: "src/models/ensemble.py · src/models/nlp_classifier.py",
    inputLabel: "Feature vector + tokenized sequence",
    inputSchema: `{
  "tabular":      DataFrame (1, 19)
  "token_ids":    Tensor (batch=1, seq≤512)
  "attn_mask":    Tensor (batch=1, seq≤512)
}`,
    outputLabel: "Independent phishing probabilities",
    outputSchema: `{
  "ml_probability":  float ∈ [0, 1]  // RF weight 0.40
  "nlp_probability": float ∈ [0, 1]  // BERT weight 0.60
}`,
    operations: [
      "RandomForestClassifier (100 estimators) traverses decision trees over 19 tabular features.",
      "DistilBERT tokenizer encodes text into WordPiece subwords with right-side truncation at 512 tokens.",
      "PyTorch evaluates 6 Transformer encoder blocks with multi-head self-attention (12 heads).",
      "Classification head outputs logits; Softmax(dim=-1) yields P(benign) and P(phishing).",
      "RF probability extracted from predict_proba()[:,1]; NLP from softmax output index [1].",
    ],
    spec: "scikit-learn RandomForest · HuggingFace DistilBERT · PyTorch Softmax · WordPiece tokenization",
  },
  {
    id: "ensemble",
    num: 4,
    icon: GitBranch,
    title: "Ensemble Scoring & Rule Signals",
    subtitle: "Weighted combination + deterministic rule bonus → 0–100 risk score + classification tier",
    route: "src.models.ensemble.compute_risk_score()",
    file: "src/models/ensemble.py",
    inputLabel: "ML prob + NLP prob + rule signals dict",
    inputSchema: `{
  "ml_probability":    float
  "nlp_probability":   float
  "has_suspicious_url": bool
  "urgency_language":   bool
}`,
    outputLabel: "Risk assessment",
    outputSchema: `RiskAssessment {
  "risk_score":     float ∈ [0, 100]
  "classification": "Low" | "Medium" | "High" | "Critical"
  "rule_bonus":     float ≥ 0
}`,
    operations: [
      "Weighted ensemble: score_base = 100 × (0.40 × ml_prob + 0.60 × nlp_prob).",
      "Rule signal evaluation: has_ip_address_url → +10.0 bonus; urgency_language → +5.0 bonus.",
      "Final risk_score = min(100, score_base + rule_bonus).",
      "Tier classification: <40 → Low, 40–60 → Medium, 60–80 → High, ≥80 → Critical.",
      "Divergence check: |ml_prob - nlp_prob| > 0.30 triggers uncertainty flag.",
    ],
    spec: "Weighted linear combination · Deterministic rule bonus · Hard threshold classification",
  },
  {
    id: "db",
    num: 5,
    icon: Database,
    title: "PostgreSQL Persistence",
    subtitle: "Analysis record saved to relational DB for audit trail and deduplication",
    route: "AnalysisRepository.save_analysis_result()",
    file: "src/db/repository.py",
    inputLabel: "Analysis result + email hash",
    inputSchema: `{
  "request_id":    UUID
  "email_hash":    SHA-256 hex
  "ml_probability", "nlp_probability",
  "rule_bonus",    "rule_signals",
  "risk_score",    "classification"
}`,
    outputLabel: "Persisted record ID",
    outputSchema: `{
  "analysis_id": UUID  // PostgreSQL primary key
                       // None if DB not configured
}`,
    operations: [
      "hash_email_text() computes SHA-256 of combined email text for PII-safe deduplication lookup.",
      "SQLAlchemy session.add() inserts AnalysisRecord ORM object into the analyses table.",
      "analysis_id (UUID) returned and threaded through the entire response for audit correlation.",
      "DatabasePersistenceError triggers FastAPI exception handler → 500 ErrorResponse.",
      "If DATABASE_URL is not configured, persistence step is skipped and analysis_id is None.",
    ],
    spec: "PostgreSQL 15 · SQLAlchemy 2.0 ORM · SHA-256 email hashing · UUID primary keys",
  },
  {
    id: "rag",
    num: 6,
    icon: Search,
    title: "RAG Evidence Retrieval",
    subtitle: "Sentence-transformer embeddings → ChromaDB ANN search → top-k knowledge-base chunks",
    route: "retriever(combined_text, RAG_TOP_K)",
    file: "src/rag/retriever.py · src/rag/embeddings.py",
    inputLabel: "Combined email text + k",
    inputSchema: `{
  "query_text": str         // combined subject+body
  "top_k":      int = 5    // from settings.RAG_TOP_K
}`,
    outputLabel: "Retrieved evidence chunks",
    outputSchema: `List[{
  "id":                str
  "content":           str
  "similarity":        float ∈ [0, 1]
  "document_name":     str
  "source_attribution": str  // MITRE / NIST ref
  "is_mock":           bool
}]`,
    operations: [
      "SentenceTransformerEmbedder encodes query into 384-dim dense vector using all-MiniLM-L6-v2.",
      "ChromaDB cosine similarity ANN search retrieves top-k chunks from indexed knowledge base.",
      "Knowledge base: MITRE ATT&CK T1566, NIST SP 800-61 Rev.3, NIST SP 800-53 Rev.5, RFC 5321/5322.",
      "Raw hits filtered; similarity clamped to [0.0, 1.0]; is_mock flag preserved for transparency.",
      "On retrieval failure → evidence_status='unavailable'; if RAG_ENABLED=false → 'disabled'.",
    ],
    spec: "all-MiniLM-L6-v2 (384-dim) · ChromaDB ANN · Cosine similarity · 4-document knowledge base",
  },
  {
    id: "agent",
    num: 7,
    icon: Bot,
    title: "LangGraph Agent Investigation",
    subtitle: "StateGraph workflow: URL decomposition → evidence analysis → escalation decision",
    route: "investigation_graph.invoke(agent_state)",
    file: "src/agent/graph.py · src/agent/tools/",
    inputLabel: "Agent initial state",
    inputSchema: `AgentState {
  "request_id", "email_text", "email_subject",
  "ml_probability", "nlp_probability",
  "risk_score", "classification",
  "retrieved_evidence": List[EvidenceChunk],
  "rule_bonus", "analysis_id"
}`,
    outputLabel: "Enriched agent state",
    outputSchema: `{
  "url_analysis":        List[URLObservation]
  "requires_escalation": bool
  "escalation_reason":   str | None
  "structured_explanation": InvestigationExplanation
}`,
    operations: [
      "LangGraph StateGraph defines nodes: url_extractor → evidence_analyzer → escalation_checker → explainer.",
      "url_extractor tool: RFC 3986 URL parsing, IP literal detection, subdomain depth, punycode, port anomalies.",
      "evidence_analyzer node: correlates retrieved RAG chunks with detected URL patterns and ML signals.",
      "escalation_checker: rule-based trigger (score ≥ 80 OR divergence > 0.30 OR IP literal) → bool + reason.",
      "Conditional edges route to LLM explainer if enabled, else deterministic fallback generator.",
    ],
    spec: "LangGraph StateGraph · RFC 3986 URL parser · Deterministic tool nodes · Conditional edges",
  },
  {
    id: "llm",
    num: 8,
    icon: Zap,
    title: "LLM Explanation Generation",
    subtitle: "Grounded narrative from Gemini / Groq, with deterministic fallback generator",
    route: "generate_explanation(agent_state, llm)",
    file: "src/agent/llm.py · src/agent/graph.py",
    inputLabel: "Enriched agent state + LLM provider",
    inputSchema: `{
  "agent_state": AgentState  // with URL analysis
  "primary_llm": Gemini | None
  "fallback_llm": Groq | None
}`,
    outputLabel: "Structured explanation",
    outputSchema: `InvestigationExplanation {
  "summary":             str
  "key_findings":        List[str]
  "risk_explanation":    str
  "recommended_actions": List[str]  // advisory only
  "limitations":         List[str]
  "evidence_references": List[str]
  "provider_used":       "gemini" | "groq" | None
  "generation_status":   "completed" | "fallback" | "degraded"
}`,
    operations: [
      "Primary LLM (Gemini) invoked with grounding prompt referencing evidence, URLs, and risk score.",
      "On Gemini failure → automatic fallback to Groq LLM with identical structured output schema.",
      "On both LLM failures → generate_deterministic_degraded_explanation() builds rule-based narrative.",
      "All containment recommendations explicitly framed as advisory SOC actions (never claimed as executed).",
      "LangChain LLM abstraction normalizes provider-specific API differences to consistent interface.",
    ],
    spec: "Google Gemini API · Groq API · LangChain abstraction · Pydantic output parsing · Fallback chain",
  },
  {
    id: "response",
    num: 9,
    icon: PackageCheck,
    title: "Response Assembly",
    subtitle: "All pipeline outputs merged into a single validated AnalyzeResponse Pydantic model",
    route: "return AnalyzeResponse(**result)",
    file: "src/api/schemas.py · src/api/services.py",
    inputLabel: "All collected stage outputs",
    inputSchema: `{
  all fields from stages 1–8
  assembled into result dict
}`,
    outputLabel: "HTTP 200 JSON response",
    outputSchema: `AnalyzeResponse {
  "request_id", "analysis_id",
  "risk_score", "classification",
  "ml_probability", "nlp_probability", "rule_bonus",
  "evidence": List[SecurityEvidenceItem],
  "evidence_status": "retrieved" | "empty" | ...
  "requires_escalation": bool,
  "escalation_reason": str | None,
  "url_analysis": List[URLObservation],
  "explanation": InvestigationExplanation | None
}`,
    operations: [
      "AnalysisService.analyze_email() collects outputs from all 8 prior stages into result dict.",
      "AnalyzeResponse(**result) validates all fields against Pydantic v2 frozen model constraints.",
      "FastAPI serializes model to JSON using Pydantic .model_dump() with camelCase/snake_case aliases.",
      "structlog logs analysis_completed event with non-PII fields (score, classification, evidence_count).",
      "HTTP 200 response with Content-Type: application/json and CORS headers sent back to client.",
    ],
    spec: "Pydantic V2 response model · FastAPI JSON serialization · structlog audit logging",
  },
];

/* ─── Component: Step pill ──────────────────────────── */
const StepPill: React.FC<{
  step: PipelineStep;
  isActive: boolean;
  onClick: () => void;
}> = ({ step, isActive, onClick }) => {
  const Icon = step.icon;
  return (
    <button
      onClick={onClick}
      className={`w-full text-left flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-150 group ${
        isActive
          ? "bg-white/[0.08] text-zinc-100"
          : "text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.03]"
      }`}
    >
      <div
        className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 transition-colors ${
          isActive ? "bg-zinc-700" : "bg-white/[0.04] group-hover:bg-white/[0.07]"
        }`}
      >
        <Icon className="w-3.5 h-3.5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-zinc-600 shrink-0">{String(step.num).padStart(2, "0")}</span>
          <span className="text-sm font-medium truncate">{step.title}</span>
        </div>
      </div>
      <ChevronRight className={`w-3.5 h-3.5 shrink-0 transition-transform ${isActive ? "rotate-90 text-zinc-400" : "text-zinc-700"}`} />
    </button>
  );
};

/* ─── Component: Schema block ──────────────────────── */
const Schema: React.FC<{ label: string; badge: string; badgeColor: string; schema: string; description: string }> = ({
  label, badge, badgeColor, schema, description,
}) => (
  <div className="rounded-xl border border-white/[0.06] bg-surface-raised overflow-hidden">
    <div className="px-4 py-3 border-b border-white/[0.05] flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Code2 className="w-3.5 h-3.5 text-zinc-500" />
        <span className="text-xs font-semibold text-zinc-300">{label}</span>
      </div>
      <span className={`label px-2 py-0.5 rounded font-mono ${badgeColor}`}>{badge}</span>
    </div>
    <div className="px-4 py-3 space-y-2">
      <p className="text-xs text-zinc-500 leading-relaxed">{description}</p>
      <pre className="p-3 rounded-lg bg-bg text-xs font-mono text-zinc-400 overflow-x-auto leading-relaxed whitespace-pre-wrap">
        {schema}
      </pre>
    </div>
  </div>
);

/* ─── Main page ─────────────────────────────────────── */
const PipelineVisualizerPage: React.FC = () => {
  const [activeId, setActiveId] = useState<string | null>(null);
  const activeStep = STEPS.find((s) => s.id === activeId) ?? null;

  return (
    <div className="max-w-6xl mx-auto px-5 sm:px-8 py-10 space-y-10">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-5">
        <div>
          <div className="flex items-center gap-3 mb-3">
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Analysis
            </Link>
          </div>
          <p className="label mb-2">System Architecture</p>
          <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">
            Backend Request Pipeline
          </h1>
          <p className="text-sm text-zinc-500 mt-1.5 max-w-lg">
            Every email submission passes through {STEPS.length} sequential processing stages.
            Click any step to inspect its input schema, internal operations, and output contract.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-600 font-mono self-start sm:self-auto">
          <FileJson className="w-4 h-4" />
          <span>POST /api/v1/analyze → AnalyzeResponse</span>
        </div>
      </div>

      {/* Main two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">

        {/* Left: step list */}
        <div className="card">
          <div className="card-header">
            <span className="text-sm font-semibold text-zinc-100">Processing Stages</span>
            <span className="label font-mono">{STEPS.length} steps</span>
          </div>
          <div className="p-2 space-y-0.5">
            {STEPS.map((step, idx) => (
              <React.Fragment key={step.id}>
                <StepPill
                  step={step}
                  isActive={activeId === step.id}
                  onClick={() => setActiveId(activeId === step.id ? null : step.id)}
                />
                {idx < STEPS.length - 1 && (
                  <div className="flex justify-center py-0.5">
                    <ArrowDown className="w-3 h-3 text-zinc-700" />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Right: detail panel */}
        <div>
          {!activeStep ? (
            <div className="h-full min-h-[400px] rounded-xl border border-dashed border-white/[0.07] flex flex-col items-center justify-center p-10 text-center">
              <div className="w-12 h-12 rounded-xl bg-surface-raised border border-white/[0.07] flex items-center justify-center mb-4">
                <Layers className="w-5 h-5 text-zinc-600" />
              </div>
              <p className="text-sm font-medium text-zinc-400 mb-1">Select a stage</p>
              <p className="text-xs text-zinc-600 max-w-xs leading-relaxed">
                Click any step on the left to inspect its input schema, internal operations, output types,
                and technical specification.
              </p>
            </div>
          ) : (
            <div className="card animate-fade-up">
              {/* Detail header */}
              <div className="card-header">
                <div>
                  <div className="flex items-center gap-2.5 mb-1">
                    <span className="label font-mono">Step {String(activeStep.num).padStart(2, "0")}</span>
                    <span className="text-sm font-semibold text-zinc-100">{activeStep.title}</span>
                  </div>
                  <p className="text-xs text-zinc-500">{activeStep.subtitle}</p>
                </div>
                <button
                  onClick={() => setActiveId(null)}
                  className="text-zinc-600 hover:text-zinc-300 transition-colors p-1"
                  aria-label="Close detail"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Route + file pills */}
              <div className="px-5 py-3 border-b border-white/[0.05] flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-surface-raised border border-white/[0.06] font-mono text-xs text-zinc-400">
                  <Code2 className="w-3 h-3 text-zinc-500" />
                  {activeStep.route}
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-surface-raised border border-white/[0.06] font-mono text-xs text-zinc-500">
                  {activeStep.file}
                </span>
              </div>

              <div className="p-5 space-y-6">
                {/* Internal operations */}
                <div>
                  <span className="label block mb-3">Internal Operations</span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {activeStep.operations.map((op, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 p-3 rounded-lg bg-surface-raised border border-white/[0.05] text-xs text-zinc-400 leading-relaxed"
                      >
                        <span className="label font-mono mt-0.5 shrink-0 w-5 text-right">{i + 1}.</span>
                        <span>{op}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Technical spec */}
                <div className="p-3.5 rounded-lg bg-surface-raised border border-white/[0.05] flex items-start gap-3">
                  <Cpu className="w-4 h-4 text-zinc-500 shrink-0 mt-0.5" />
                  <div>
                    <span className="label block mb-1">Technical Specification</span>
                    <p className="text-xs font-mono text-zinc-400 leading-relaxed">{activeStep.spec}</p>
                  </div>
                </div>

                {/* Input + Output schemas */}
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                  <Schema
                    label="Input Schema"
                    badge="→ incoming"
                    badgeColor="text-sky-400 bg-sky-500/10"
                    schema={activeStep.inputSchema}
                    description={activeStep.inputLabel}
                  />
                  <Schema
                    label="Output Contract"
                    badge="← return"
                    badgeColor="text-emerald-400 bg-emerald-500/10"
                    schema={activeStep.outputSchema}
                    description={activeStep.outputLabel}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Flow summary bar at bottom */}
      <div className="card">
        <div className="p-5">
          <span className="label block mb-3">Complete request flow</span>
          <div className="flex flex-wrap items-center gap-1.5">
            {STEPS.map((step, i) => (
              <React.Fragment key={step.id}>
                <button
                  onClick={() => setActiveId(step.id)}
                  className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
                    activeId === step.id
                      ? "bg-zinc-700 text-zinc-100"
                      : "bg-surface-raised border border-white/[0.05] text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.05]"
                  }`}
                >
                  {step.num}. {step.title.split(" ")[0]}
                </button>
                {i < STEPS.length - 1 && (
                  <ChevronRight className="w-3 h-3 text-zinc-700 shrink-0" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export { PipelineVisualizerPage };
export default PipelineVisualizerPage;
