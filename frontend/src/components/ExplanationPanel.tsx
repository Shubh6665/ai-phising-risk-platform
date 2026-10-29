import React from "react";
import { Sparkles, Shield, CheckCircle, AlertTriangle, Layers, FileCheck } from "lucide-react";
import { InvestigationExplanation } from "../types/api";

interface ExplanationPanelProps {
  explanation?: InvestigationExplanation | null;
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ explanation }) => {
  if (!explanation) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl text-center text-slate-500 italic text-sm">
        Agent investigation narrative is unavailable for this analysis.
      </div>
    );
  }

  const getProviderLabel = (provider?: string | null, status?: string) => {
    if (status === "disabled") {
      return { label: "LLM Synthesis Disabled by Config", color: "text-slate-400 bg-slate-800 border-slate-700" };
    }
    if (provider === "google") {
      return { label: "Google Gemini 3.8 Flash (Primary LLM)", color: "text-cyan-300 bg-cyan-950/80 border-cyan-800/60" };
    }
    if (provider === "groq") {
      return { label: "Groq OpenAI GPT-OSS 120B (Fallback LLM)", color: "text-orange-300 bg-orange-950/80 border-orange-800/60" };
    }
    return { label: "Deterministic Degraded Generator (Zero Hallucination)", color: "text-amber-300 bg-amber-950/80 border-amber-800/60" };
  };

  const providerMeta = getProviderLabel(explanation.provider_used, explanation.generation_status);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            LangGraph Investigation Explanation & Recommendations
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Synthesis grounded strictly in statistical model signals, URL anomalies, and authoritative security playbooks.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-[11px] font-mono px-3 py-1 rounded-full border ${providerMeta.color} flex items-center gap-1.5`}>
            <Shield className="w-3 h-3" />
            {providerMeta.label}
          </span>
          <span className="text-[10px] font-mono uppercase bg-slate-800 text-slate-400 px-2.5 py-1 rounded-full border border-slate-700">
            Status: {explanation.generation_status}
          </span>
        </div>
      </div>

      {/* 1. Executive Summary */}
      <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
        <h4 className="text-xs font-mono uppercase text-slate-400 tracking-wider mb-1.5 flex items-center gap-1.5 font-bold">
          <FileCheck className="w-4 h-4 text-cyan-400" />
          Executive Briefing
        </h4>
        <p className="text-sm text-slate-200 leading-relaxed font-sans select-text">
          {explanation.summary}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* 2. Key Findings */}
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
          <h4 className="text-xs font-mono uppercase text-slate-400 tracking-wider mb-2 flex items-center gap-1.5 font-bold">
            <Layers className="w-4 h-4 text-cyan-400" />
            Key Empirical Findings
          </h4>
          {explanation.key_findings.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No specific risk indicators flagged.</p>
          ) : (
            <ul className="space-y-1.5 text-xs text-slate-300">
              {explanation.key_findings.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-0.5">•</span>
                  <span className="select-text">{item}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* 3. Recommended Actions (Advisory Only) */}
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-mono uppercase text-slate-400 tracking-wider flex items-center gap-1.5 font-bold">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              Recommended Defensive Steps
            </h4>
            <span className="text-[10px] font-mono text-amber-400/90 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800/40">
              Advisory Controls
            </span>
          </div>
          {explanation.recommended_actions.length === 0 ? (
            <p className="text-xs text-slate-500 italic">Standard mail gateway hygiene applies.</p>
          ) : (
            <ul className="space-y-1.5 text-xs text-slate-300">
              {explanation.recommended_actions.map((act, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">✓</span>
                  <span className="select-text">{act}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* 4. Risk Rationale */}
      <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
        <h4 className="text-xs font-mono uppercase text-slate-400 tracking-wider mb-1.5 font-bold">
          Technical Risk Rationale
        </h4>
        <p className="text-xs text-slate-300 leading-relaxed font-sans select-text">
          {explanation.risk_explanation}
        </p>
      </div>

      {/* 5. Limitations & Grounding Evidence Citations */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-slate-400 pt-3 border-t border-slate-800/80">
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>
            Limitations: Static offline heuristics; no dynamic browser or sandbox detonation executed.
          </span>
        </div>

        {explanation.evidence_references.length > 0 && (
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-cyan-400/80 shrink-0">
            <span>Citations: {explanation.evidence_references.join(", ")}</span>
          </div>
        )}
      </div>
    </div>
  );
};

