import React from "react";
import { Link } from "react-router-dom";
import { AnalysisForm } from "../components/AnalysisForm";
import { RiskScore } from "../components/RiskScore";
import { ModelBreakdown } from "../components/ModelBreakdown";
import { EvidenceList } from "../components/EvidenceList";
import { InvestigationFindings } from "../components/InvestigationFindings";
import { ExplanationPanel } from "../components/ExplanationPanel";
import { useAnalysis } from "../context/AnalysisContext";
import { AlertCircle, Terminal, Network, ArrowRight } from "lucide-react";

export const DashboardPage: React.FC = () => {
  const { result, isLoading, errorMessage, handleAnalyze, handleReset } = useAnalysis();

  return (
    <div className="space-y-6">
      {/* Clean Top Bar / Sub-header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-2 border-b border-slate-800/80 gap-3">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">
            Email Threat Assessment
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time inference using Random Forest (0.40) + DistilBERT (0.60) + ChromaDB RAG + LangGraph Agent.
          </p>
        </div>

        <Link
          to="/pipeline"
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white transition-colors self-start sm:self-auto"
        >
          <Network className="w-3.5 h-3.5 text-violet-400" />
          <span>View Backend Architecture & Flow</span>
          <ArrowRight className="w-3 h-3 text-slate-500" />
        </Link>
      </div>

      {/* Analysis Form Section */}
      <section aria-label="Email submission form">
        <AnalysisForm
          onSubmit={handleAnalyze}
          isLoading={isLoading}
          onReset={handleReset}
          hasResult={result !== null}
        />
      </section>

      {/* Global Error Alert */}
      {errorMessage && (
        <div
          role="alert"
          className="p-4 rounded-xl bg-red-950/70 border border-red-900/80 text-red-200 flex items-start gap-3 shadow-sm"
        >
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-xs font-semibold text-red-300">Analysis Request Failed</h3>
            <p className="text-xs text-red-300/90 mt-0.5 leading-relaxed">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Initial Empty State Before Analysis */}
      {!result && !isLoading && !errorMessage && (
        <div className="border border-dashed border-slate-800 rounded-xl p-10 text-center text-slate-500 space-y-3 bg-[#0d121f]/50">
          <div className="w-10 h-10 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-cyan-400">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-300">No Analysis Executed Yet</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 leading-relaxed">
              Submit an email above or load a sample scenario to run multi-layer Random Forest + DistilBERT inference, RAG evidence retrieval, and agent investigation.
            </p>
          </div>
          <div className="pt-1">
            <Link
              to="/pipeline"
              className="inline-flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 hover:underline"
            >
              <span>Inspect how the backend pipeline processes requests →</span>
            </Link>
          </div>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* Top Score Banner */}
          <section aria-label="Risk score assessment">
            <RiskScore
              score={result.risk_score}
              classification={result.classification}
              requiresEscalation={result.requires_escalation}
              escalationReason={result.escalation_reason}
              requestId={result.request_id}
              analysisId={result.analysis_id}
            />
          </section>

          {/* Model Breakdown */}
          <section aria-label="Model probability breakdown">
            <ModelBreakdown
              mlProbability={result.ml_probability}
              nlpProbability={result.nlp_probability}
              ruleBonus={result.rule_bonus}
            />
          </section>

          {/* Investigation Explanation & Recommendations */}
          <section aria-label="Investigation explanation and recommendations">
            <ExplanationPanel explanation={result.explanation} />
          </section>

          {/* Two-Column Grid: URL Findings + RAG Evidence */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <section aria-label="Structural URL observations">
              <InvestigationFindings urls={result.url_analysis} />
            </section>

            <section aria-label="Security knowledge evidence">
              <EvidenceList evidence={result.evidence} status={result.evidence_status} />
            </section>
          </div>
        </div>
      )}
    </div>
  );
};
export default DashboardPage;
