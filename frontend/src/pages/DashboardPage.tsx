import React from "react";
import { Link } from "react-router-dom";
import { AnalysisForm } from "../components/AnalysisForm";
import { RiskScore } from "../components/RiskScore";
import { ModelBreakdown } from "../components/ModelBreakdown";
import { EvidenceList } from "../components/EvidenceList";
import { InvestigationFindings } from "../components/InvestigationFindings";
import { ExplanationPanel } from "../components/ExplanationPanel";
import { useAnalysis } from "../context/AnalysisContext";
import { AlertCircle, ArrowUpRight, Layers } from "lucide-react";

export const DashboardPage: React.FC = () => {
  const { result, isLoading, errorMessage, handleAnalyze, handleReset } = useAnalysis();

  return (
    <div className="max-w-6xl mx-auto px-5 sm:px-8 py-10 space-y-10">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <p className="label mb-2">Email Threat Analysis</p>
          <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">
            AI Phishing Risk &amp; Triage Platform
          </h1>
          <p className="text-sm text-zinc-500 mt-1.5 max-w-lg">
            Dual-model ensemble (Random Forest + DistilBERT), knowledge-base evidence retrieval, and
            autonomous LangGraph investigation — all in one API call.
          </p>
        </div>
        <Link
          to="/pipeline"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-white/[0.07] text-sm text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04] transition-colors whitespace-nowrap self-start sm:self-auto"
        >
          <Layers className="w-4 h-4" />
          Backend Architecture
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Form */}
      <section aria-label="Email submission form">
        <AnalysisForm
          onSubmit={handleAnalyze}
          isLoading={isLoading}
          onReset={handleReset}
          hasResult={result !== null}
        />
      </section>

      {/* Error */}
      {errorMessage && (
        <div
          role="alert"
          className="p-4 rounded-xl border border-red-500/20 bg-red-500/5 flex items-start gap-3"
        >
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-red-300">Analysis Request Failed</p>
            <p className="text-xs text-zinc-400 mt-0.5 leading-relaxed">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !isLoading && !errorMessage && (
        <div className="rounded-xl border border-dashed border-white/[0.07] p-14 text-center">
          <p className="text-sm font-medium text-zinc-400 mb-1">No Analysis Executed Yet</p>
          <p className="text-xs text-zinc-600 max-w-sm mx-auto leading-relaxed">
            Submit an email above or load a sample to run Random Forest + DistilBERT inference,
            RAG evidence retrieval, and agent investigation.
          </p>
          <Link
            to="/pipeline"
            className="inline-flex items-center gap-1.5 mt-5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            Explore the backend pipeline
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-5">
          {/* Risk score */}
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

          {/* Model breakdown */}
          <section aria-label="Model probability breakdown">
            <ModelBreakdown
              mlProbability={result.ml_probability}
              nlpProbability={result.nlp_probability}
              ruleBonus={result.rule_bonus}
            />
          </section>

          {/* Investigation explanation */}
          <section aria-label="Investigation explanation and recommendations">
            <ExplanationPanel explanation={result.explanation} />
          </section>

          {/* Two-column: URL findings + evidence */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <section aria-label="Structural URL observations">
              <InvestigationFindings urls={result.url_analysis} />
            </section>
            <section aria-label="Security knowledge evidence">
              <EvidenceList
                evidence={result.evidence}
                status={result.evidence_status as "retrieved" | "empty" | "unavailable" | "disabled"}
              />
            </section>
          </div>
        </div>
      )}
    </div>
  );
};
export default DashboardPage;
