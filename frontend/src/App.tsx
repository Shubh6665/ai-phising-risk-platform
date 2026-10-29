import React, { useState } from "react";
import { Header } from "./components/Header";
import { AnalysisForm } from "./components/AnalysisForm";
import { RiskScore } from "./components/RiskScore";
import { ModelBreakdown } from "./components/ModelBreakdown";
import { EvidenceList } from "./components/EvidenceList";
import { InvestigationFindings } from "./components/InvestigationFindings";
import { ExplanationPanel } from "./components/ExplanationPanel";
import { AnalyzeRequest, AnalyzeResponse } from "./types/api";
import { analyzeEmail, ApiError } from "./services/api";
import { AlertCircle, Terminal, CheckCircle2 } from "lucide-react";

export const App: React.FC = () => {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleAnalyze = async (payload: AnalyzeRequest) => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await analyzeEmail(payload);
      setResult(data);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("An unexpected error occurred while communicating with the analysis service.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Analysis Form */}
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
            className="p-4 rounded-2xl bg-red-950/70 border border-red-800/80 text-red-200 flex items-start gap-3 shadow-lg"
          >
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-red-300">Analysis Request Failed</h3>
              <p className="text-xs text-red-300/90 mt-0.5">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Initial Empty State Before Analysis */}
        {!result && !isLoading && !errorMessage && (
          <div className="border border-dashed border-slate-800 rounded-2xl p-12 text-center text-slate-500 space-y-3">
            <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-cyan-400">
              <Terminal className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-300">No Analysis Executed Yet</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Submit an email above or load a sample scenario to run multi-layer Random Forest + DistilBERT inference, RAG evidence retrieval, and agent investigation.
            </p>
          </div>
        )}

        {/* Results View */}
        {result && (
          <div className="space-y-8 animate-fadeIn">
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
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <section aria-label="Structural URL observations">
                <InvestigationFindings urls={result.url_analysis} />
              </section>

              <section aria-label="Security knowledge evidence">
                <EvidenceList evidence={result.evidence} status={result.evidence_status} />
              </section>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <span>AI Phishing Risk & Triage Platform • Built with FastAPI, PyTorch, ChromaDB, LangGraph & React</span>
          <span className="flex items-center gap-1.5 text-slate-400">
            <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" /> Grounded in NIST SP 800-61 Rev. 3 & MITRE ATT&CK v20.0
          </span>
        </div>
      </footer>
    </div>
  );
};
export default App;

