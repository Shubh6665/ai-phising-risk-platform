import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Network,
  ArrowRight,
  CheckCircle2,
  Code2,
  Play,
  Brackets,
  Binary,
  GitBranch,
  Info,
  Terminal,
} from "lucide-react";
import { useAnalysis } from "../context/AnalysisContext";

interface PipelineStep {
  id: string;
  number: number;
  title: string;
  subtitle: string;
  route: string;
  sourceFile: string;
  inputDescription: string;
  inputSchema: string;
  outputDescription: string;
  outputSchema: string;
  whatIsUndergoing: string[];
  algorithmsAndMath: string;
}

const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: "gateway",
    number: 1,
    title: "FastAPI Gateway & Route Ingestion",
    subtitle: "HTTP POST Ingestion, Request ID Middleware & Pydantic Validation",
    route: "POST /api/v1/analyze",
    sourceFile: "src/api/routes/analyze.py",
    inputDescription: "Client HTTP request body containing email body text and optional subject.",
    inputSchema: `{
  "text": "string (min_length=1, non-whitespace)",
  "subject": "string | null (optional)"
}`,
    outputDescription: "Dependency-injected AnalysisService invocation with tracked Request UUID.",
    outputSchema: `{
  "request_id": "UUID v4 (from RequestState)",
  "text": "str",
  "subject": "str | None"
}`,
    whatIsUndergoing: [
      "Client request hits FastAPI ASGI application router via Uvicorn.",
      "RequestIdMiddleware generates a persistent UUID v4 and injects it into request.state.",
      "CORSMiddleware validates origin against whitelist (http://localhost:5173, etc.).",
      "Pydantic v2 AnalyzeRequest model enforces min_length=1 and rejects whitespace-only spoofing payloads.",
      "FastAPI dependency injection (Depends) provisions model instances, ChromaDB retriever, and PostgreSQL session.",
    ],
    algorithmsAndMath: "Pydantic V2 Rust core validation • RFC 4122 UUID v4 generation • HTTP/1.1 & HTTP/2 ASGI multiplexing",
  },
  {
    id: "features",
    number: 2,
    title: "Data Preprocessing & Feature Engineering",
    subtitle: "19 Handcrafted Lexical, Structural & Heuristic Signal Extractors",
    route: "Internal: src.features.feature_pipeline.extract_features()",
    sourceFile: "src/features/feature_pipeline.py",
    inputDescription: "Combined subject and body string pandas DataFrame.",
    inputSchema: `DataFrame {
  "subject": Series[str],
  "body": Series[str]
}`,
    outputDescription: "19-dimensional numeric vector formatted as pandas DataFrame for classical inference.",
    outputSchema: `DataFrame [1 row x 19 columns]:
[
  "url_count", "has_ip_address_url", "suspicious_tld_count",
  "at_symbol_count", "subdomain_depth_max", "phishing_keyword_count",
  "urgency_keyword_count", "excessive_capitalization_ratio", ...
]`,
    whatIsUndergoing: [
      "build_email_text() combines subject and body into a normalized string stream.",
      "extract_url_features() scans for HTTP/HTTPS URI schemes and RFC 3986 lexical structures.",
      "Regex checks identify raw IP address literals (e.g. http://192.168.1.100) bypassing DNS reputation.",
      "extract_text_features() analyzes token frequency against curated phishing urgency lexicons.",
      "Validates feature vector column ordering to guarantee zero distribution shift with model training schema.",
    ],
    algorithmsAndMath: "RFC 3986 URI parsing • Regular Expression tokenization • Lexical entropy & ratio calculations",
  },
  {
    id: "models",
    number: 3,
    title: "Dual ML & Transformer NLP Inference",
    subtitle: "Parallel Execution: Random Forest (Tabular) + Fine-Tuned DistilBERT (Contextual)",
    route: "Internal: RandomForest.predict_proba() + sample_probabilities(DistilBERT)",
    sourceFile: "src/models/ensemble.py & src/models/nlp_classifier.py",
    inputDescription: "19-feature tabular vector + tokenized text sequence [CLS] ... [SEP].",
    inputSchema: `{
  "tabular_features": "DataFrame (1, 19)",
  "token_ids": "Tensor(batch=1, max_len=512)",
  "attention_mask": "Tensor(batch=1, max_len=512)"
}`,
    outputDescription: "Independent class probabilities for benign (0) and phishing (1).",
    outputSchema: `{
  "ml_probability": "float ∈ [0.0, 1.0] (Weight: 0.40)",
  "nlp_probability": "float ∈ [0.0, 1.0] (Weight: 0.60)"
}`,
    whatIsUndergoing: [
      "RandomForestClassifier (100 estimators) traverses decision trees over 19 tabular features.",
      "DistilBERT tokenizer encodes raw email text into 512-token WordPiece subwords with attention masking.",
      "PyTorch evaluates 6 Transformer encoder blocks with multi-head self-attention.",
      "Classification head outputs logits: Softmax computes P(phishing) reflecting contextual deceptive intent.",
      "Evaluation completes in isolated forward pass without gradient calculations (torch.no_grad).",
    ],
    algorithmsAndMath: "Random Forest Gini Impurity splits • DistilBERT 6-layer Transformer • Softmax: P(y=1) = e^z1 / (e^z0 + e^z1)",
  },
  {
    id: "ensemble",
    number: 4,
    title: "Phase 5 Risk Scoring & Heuristic Rules Engine",
    subtitle: "Weighted Hybrid Combination, Heuristic Boosters & Divergence Detection",
    route: "Internal: src.models.ensemble.compute_risk_score()",
    sourceFile: "src/models/ensemble.py",
    inputDescription: "Classical ML probability, transformer NLP probability, and extracted rule flags.",
    inputSchema: `{
  "ml_prob": "float",
  "nlp_prob": "float",
  "rule_signals": {
    "has_suspicious_url": "bool",
    "urgency_language": "bool"
  }
}`,
    outputDescription: "Composite risk score (0-100), classification tier, and escalation requirement.",
    outputSchema: `{
  "risk_score": "float ∈ [0.0, 100.0]",
  "classification": "'Low' | 'Medium' | 'High' | 'Critical'",
  "rule_bonus": "float",
  "requires_escalation": "bool",
  "escalation_reason": "str | None"
}`,
    whatIsUndergoing: [
      "Computes base score: Base = (0.40 * ml_prob + 0.60 * nlp_prob) * 100.",
      "Evaluates deterministic rules: +10.0 pts for raw IP literal host; +5.0 pts for urgency language.",
      "Calculates model divergence: Δ = |ml_prob - nlp_prob|.",
      "If Δ > 0.30, flags operational divergence escalation for mandatory human review.",
      "Maps bounded composite score [0, 100] to operational tiers: Low (<40), Medium (40-59), High (60-79), Critical (>=80).",
    ],
    algorithmsAndMath: "Score = min(100, (0.40 * P_ML + 0.60 * P_NLP) * 100 + Bonus) • Divergence Δ = |P_ML - P_NLP|",
  },
  {
    id: "rag",
    number: 5,
    title: "ChromaDB Vector Retrieval (RAG Pipeline)",
    subtitle: "Dense Semantic Search over Curated NIST SP 800-61 Rev. 3 & MITRE ATT&CK v20.0",
    route: "Internal: src.rag.retriever.retrieve_security_guidance()",
    sourceFile: "src/rag/retriever.py & src/rag/embeddings.py",
    inputDescription: "Semantic query constructed from email subject and body prefix (up to 300 characters).",
    inputSchema: `{
  "query": "str (Subject + Body excerpt)",
  "top_k": 3
}`,
    outputDescription: "Ranked list of authoritative security knowledge-base chunks with cosine similarity.",
    outputSchema: `list[SecurityEvidenceItem] [
  {
    "chunk_id": "str",
    "content": "str",
    "similarity": "float ∈ [0.0, 1.0]",
    "document_title": "str",
    "source_attribution": "str",
    "is_mock": "bool"
  }
]`,
    whatIsUndergoing: [
      "Embedder encodes query using sentence-transformers/all-MiniLM-L6-v2 into a 384-dimensional dense vector.",
      "ChromaDB executes HNSW (Hierarchical Navigable Small World) approximate nearest neighbor vector search.",
      "Computes cosine similarity: sim(u, v) = 1 - (u·v) / (||u|| * ||v||).",
      "Filters retrieved guidance by configured minimum similarity threshold (RAG_SIMILARITY_THRESHOLD).",
      "Attaches authoritative source metadata (NIST SP 800-61 Rev. 3, MITRE ATT&CK v20.0, RFC 5321/5322).",
    ],
    algorithmsAndMath: "384-dimensional Dense Embeddings • HNSW Graph Indexing • Cosine Similarity Metric",
  },
  {
    id: "agent",
    number: 6,
    title: "LangGraph Multi-Tool SOC Agent Workflow",
    subtitle: "StateGraph Coordination: Validation, URL Lexical Analysis, Policy Mapping & Grounded LLM",
    route: "Internal: src.agent.graph.run_investigation()",
    sourceFile: "src/agent/graph.py",
    inputDescription: "PhishingAnalysisState containing model scores, RAG evidence, and email content.",
    inputSchema: `PhishingAnalysisState {
  "request_id": "str",
  "email_text": "str",
  "risk_score": "float",
  "retrieved_evidence": "list[dict]", ...
}`,
    outputDescription: "Synthesized executive briefing, key findings, and advisory defensive containment steps.",
    outputSchema: `InvestigationExplanation {
  "summary": "str",
  "key_findings": "list[str]",
  "risk_explanation": "str",
  "recommended_actions": "list[str] (Advisory)",
  "provider_used": "'google' | 'groq' | null",
  "generation_status": "'completed' | 'degraded'"
}`,
    whatIsUndergoing: [
      "Node 1: validate_input verifies identifier presence and mathematical probability bounds.",
      "Node 2: retrieve_knowledge reuses pre-retrieved RAG chunks to prevent redundant vector embeddings.",
      "Node 3: analyze_urls inspects URL components (IP literal, non-standard port, punycode, TLD depth).",
      "Node 4: lookup_policy maps composite risk score to NIST incident containment recommendations.",
      "Node 5: aggregate_findings verifies deterministic escalation rules.",
      "Node 6: generate_explanation synthesizes grounded explanation via Google Gemini / Groq or deterministic degraded generator.",
    ],
    algorithmsAndMath: "LangGraph Directed Acyclic StateGraph • Prompt Grounding Constraints • Advisory SOC Action Taxonomy",
  },
  {
    id: "db",
    number: 7,
    title: "PostgreSQL Persistence & Response Serialization",
    subtitle: "Cryptographic Hashing, Audit Trail Logging & Pydantic v2 JSON Response",
    route: "Output: 200 OK -> AnalyzeResponse JSON",
    sourceFile: "src/db/repository.py & src/api/schemas.py",
    inputDescription: "Assembled dictionary containing analysis IDs, scores, evidence, and explanation.",
    inputSchema: `dict {
  "analysis_id": "UUID",
  "request_id": "UUID",
  "risk_score": 84.5,
  "url_analysis": [...], ...
}`,
    outputDescription: "Strict JSON payload adhering to AnalyzeResponse schema returned to frontend.",
    outputSchema: `AnalyzeResponse {
  "request_id": "string",
  "risk_score": "float (0-100)",
  "classification": "'Low' | 'Medium' | 'High' | 'Critical'",
  "ml_probability": "float",
  "nlp_probability": "float",
  "rule_bonus": "float",
  "evidence": "list[SecurityEvidenceItem]",
  "url_analysis": "list[URLObservation]",
  "explanation": "InvestigationExplanation"
}`,
    whatIsUndergoing: [
      "Computes SHA-256 cryptographic hash of email text for audit de-duplication without storing raw body text.",
      "AnalysisRepository saves metadata record into PostgreSQL 16 database (analysis_results table).",
      "Analysis UUID is minted and linked to the active HTTP request_id.",
      "Pydantic v2 validates complete AnalyzeResponse schema with frozen ConfigDict constraints.",
      "FastAPI serializes payload to JSON and dispatches HTTP 200 OK with security headers.",
    ],
    algorithmsAndMath: "SHA-256 Message Digest • ACID Transaction Commit • Pydantic V2 Fast C-Core JSON Serialization",
  },
];

export const PipelineVisualizerPage: React.FC = () => {
  const { result, lastPayload, handleAnalyze, isLoading } = useAnalysis();
  const [selectedStepId, setSelectedStepId] = useState<string>("gateway");
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [activeSimulationIndex, setActiveSimulationIndex] = useState<number>(-1);
  const [customInputText, setCustomInputText] = useState<string>(
    lastPayload?.text ||
      "Dear Employee,\nOur security monitor detected unauthorized logins from IP 45.33.32.156.\nPlease verify immediately: http://192.168.1.100:8080/auth/login?session=verify-now\nFailure to comply will result in account lockout.\nIT Security Desk"
  );
  const [customSubject, setCustomSubject] = useState<string>(
    lastPayload?.subject || "URGENT: Unauthorized access detected"
  );

  const selectedStep = PIPELINE_STEPS.find((s) => s.id === selectedStepId) || PIPELINE_STEPS[0];

  const handleRunSimulator = async () => {
    setIsSimulating(true);
    for (let i = 0; i < PIPELINE_STEPS.length; i++) {
      setActiveSimulationIndex(i);
      setSelectedStepId(PIPELINE_STEPS[i].id);
      await new Promise((resolve) => setTimeout(resolve, 400));
    }
    setIsSimulating(false);
  };

  const handleTriggerAnalysisFromSimulator = async () => {
    if (!customInputText.trim()) return;
    await handleAnalyze({
      subject: customSubject.trim() ? customSubject.trim() : undefined,
      text: customInputText.trim(),
    });
    handleRunSimulator();
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-md bg-slate-900 border border-slate-800 text-violet-400">
              <Network className="w-4 h-4" />
            </span>
            <span className="text-xs font-mono uppercase text-violet-400 font-semibold">
              System Design & Architecture
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white mt-1.5">
            System Design & Pipeline Data Flow Inspector
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 max-w-2xl">
            Explore each internal step of the analysis pipeline: routing, feature extraction, ML/NLP inference, RAG retrieval, LangGraph agent, and database persistence.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={handleRunSimulator}
            disabled={isSimulating || isLoading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-750 text-white text-xs font-medium border border-slate-700 transition-colors disabled:opacity-50"
          >
            <Play className={`w-3 h-3 text-cyan-400 ${isSimulating ? "animate-spin" : ""}`} />
            <span>{isSimulating ? "Simulating..." : "Simulate Flow Execution"}</span>
          </button>

          <Link
            to="/"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-850 text-slate-300 hover:text-white border border-slate-800 text-xs font-medium transition-colors"
          >
            <span>Back to Dashboard</span>
            <ArrowRight className="w-3 h-3 text-slate-500" />
          </Link>
        </div>
      </div>

      {/* Interactive Live Input Bar */}
      <section
        aria-label="Interactive Pipeline Input Simulator"
        className="bg-[#111726] border border-slate-800 rounded-xl p-5 shadow-sm"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3.5 border-b border-slate-800 gap-2">
          <div>
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Terminal className="w-4 h-4 text-cyan-400" />
              <span>Live Payload Simulator & Trace Input</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Enter or modify an email payload to see values trace through the backend steps.
            </p>
          </div>
          {result && (
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 flex items-center gap-1.5 self-start sm:self-auto">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>Live Request: {result.request_id}</span>
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <div className="md:col-span-1 space-y-3">
            <div>
              <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1 font-medium">
                Subject Header
              </label>
              <input
                type="text"
                value={customSubject}
                onChange={(e) => setCustomSubject(e.target.value)}
                placeholder="Subject line..."
                className="w-full bg-[#0b0f19] border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1 font-medium">
                Execute Pipeline
              </label>
              <button
                type="button"
                onClick={handleTriggerAnalysisFromSimulator}
                disabled={isLoading || isSimulating}
                className="w-full py-2 px-3.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Play className="w-3 h-3" />
                <span>{isLoading ? "Executing Backend..." : "Run Real Analysis Flow"}</span>
              </button>
            </div>

            {result && (
              <div className="p-3 rounded-lg bg-[#0b0f19] border border-slate-800 text-xs space-y-1 font-mono">
                <div className="text-slate-500 text-[10px] uppercase font-semibold">Latest Evaluated Result</div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Risk Score:</span>
                  <span className="text-cyan-400 font-bold">{result.risk_score.toFixed(1)}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Classification:</span>
                  <span className="text-violet-400 font-bold">{result.classification}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Escalation:</span>
                  <span className={result.requires_escalation ? "text-red-400" : "text-emerald-400"}>
                    {result.requires_escalation ? "Mandatory" : "Standard"}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="md:col-span-2">
            <label className="block text-[11px] font-mono uppercase text-slate-400 mb-1 font-medium">
              Email Body Payload
            </label>
            <textarea
              rows={5}
              value={customInputText}
              onChange={(e) => setCustomInputText(e.target.value)}
              placeholder="Raw email payload..."
              className="w-full bg-[#0b0f19] border border-slate-800 rounded-lg p-3 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 font-mono leading-relaxed"
            />
          </div>
        </div>
      </section>

      {/* Step Progression Strip */}
      <section aria-label="Pipeline Steps Navigation">
        <div className="flex items-center justify-between mb-2.5">
          <span className="text-xs font-mono uppercase text-slate-400 font-semibold flex items-center gap-1.5">
            <GitBranch className="w-3.5 h-3.5 text-cyan-400" />
            <span>Architecture Steps (Click any step to inspect)</span>
          </span>
          <span className="text-xs font-mono text-slate-500">7 Connected Sub-systems</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
          {PIPELINE_STEPS.map((step, idx) => {
            const isSelected = selectedStepId === step.id;
            const isSimActive = activeSimulationIndex === idx;

            return (
              <button
                key={step.id}
                type="button"
                onClick={() => setSelectedStepId(step.id)}
                className={`p-3 rounded-lg border text-left transition-colors flex flex-col justify-between ${
                  isSelected
                    ? "bg-slate-850 border-cyan-500/80 text-white"
                    : "bg-[#111726] border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900"
                } ${isSimActive ? "border-violet-500 bg-violet-950/30" : ""}`}
              >
                <div className="flex items-center justify-between w-full mb-1.5">
                  <span
                    className={`w-5 h-5 rounded flex items-center justify-center text-[11px] font-mono font-bold ${
                      isSelected
                        ? "bg-cyan-500 text-slate-950"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {step.number}
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400">OK</span>
                </div>

                <div>
                  <h3
                    className={`text-xs font-semibold truncate ${
                      isSelected ? "text-cyan-300" : "text-slate-200"
                    }`}
                  >
                    {step.title.split(" ")[0]} {step.title.split(" ")[1] || ""}
                  </h3>
                  <p className="text-[10px] text-slate-500 font-mono truncate mt-0.5">
                    {step.sourceFile.split("/").pop()}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Selected Step Detailed Inspector */}
      <section
        aria-label="Selected Step Detailed Inspector"
        className="bg-[#111726] border border-slate-800 rounded-xl p-6 shadow-sm space-y-5"
      >
        {/* Step Header */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-4 border-b border-slate-800 gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <span className="w-6 h-6 rounded bg-slate-800 text-cyan-400 flex items-center justify-center font-mono font-bold text-xs border border-slate-700">
                {selectedStep.number}
              </span>
              <h2 className="text-base font-bold text-white">
                {selectedStep.title}
              </h2>
            </div>
            <p className="text-xs text-slate-400">
              {selectedStep.subtitle}
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-[#0b0f19] border border-slate-800 text-cyan-400">
              {selectedStep.route}
            </span>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-[#0b0f19] border border-slate-800 text-slate-400">
              {selectedStep.sourceFile}
            </span>
          </div>
        </div>

        {/* Undergoing Operations */}
        <div>
          <h3 className="text-xs font-mono uppercase text-slate-400 tracking-wider mb-2.5 font-semibold flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span>Internal Execution Operations</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {selectedStep.whatIsUndergoing.map((item, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-[#0b0f19] border border-slate-850 flex items-start gap-2.5 text-xs text-slate-300 leading-relaxed"
              >
                <span className="w-4 h-4 rounded bg-slate-850 text-cyan-400 border border-slate-800 flex items-center justify-center shrink-0 font-mono text-[10px] font-bold mt-0.5">
                  {idx + 1}
                </span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Technical Specification */}
        <div className="p-3.5 rounded-lg bg-[#0b0f19] border border-slate-800 flex items-start gap-2.5">
          <Binary className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-semibold text-violet-300 font-mono uppercase tracking-wider block mb-0.5">
              Technical Specification:
            </span>
            <span className="text-slate-300 font-mono leading-relaxed">
              {selectedStep.algorithmsAndMath}
            </span>
          </div>
        </div>

        {/* Input & Output Schemas */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-1">
          {/* Input Schema */}
          <div className="bg-[#0b0f19] border border-slate-800 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between pb-1.5 border-b border-slate-850">
              <span className="text-xs font-mono uppercase text-slate-400 font-semibold flex items-center gap-1.5">
                <Code2 className="w-3.5 h-3.5 text-cyan-400" />
                <span>Input Schema & Types</span>
              </span>
              <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-900/60">
                Incoming Args
              </span>
            </div>
            <p className="text-xs text-slate-400">{selectedStep.inputDescription}</p>
            <pre className="p-3 rounded-md bg-[#070a12] border border-slate-850 text-xs font-mono text-cyan-300/90 overflow-x-auto leading-relaxed">
              {selectedStep.inputSchema}
            </pre>
          </div>

          {/* Output Schema */}
          <div className="bg-[#0b0f19] border border-slate-800 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between pb-1.5 border-b border-slate-850">
              <span className="text-xs font-mono uppercase text-slate-400 font-semibold flex items-center gap-1.5">
                <Brackets className="w-3.5 h-3.5 text-emerald-400" />
                <span>Output Return Types</span>
              </span>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-900/60">
                Return Contract
              </span>
            </div>
            <p className="text-xs text-slate-400">{selectedStep.outputDescription}</p>
            <pre className="p-3 rounded-md bg-[#070a12] border border-slate-850 text-xs font-mono text-emerald-300/90 overflow-x-auto leading-relaxed">
              {selectedStep.outputSchema}
            </pre>
          </div>
        </div>
      </section>
    </div>
  );
};
export default PipelineVisualizerPage;
