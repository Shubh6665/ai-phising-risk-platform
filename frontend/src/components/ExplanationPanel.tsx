import React from "react";
import { FileText, Lightbulb, ShieldCheck, AlertCircle } from "lucide-react";
import { InvestigationExplanation } from "../types/api";

interface ExplanationPanelProps {
  explanation?: InvestigationExplanation | null;
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ explanation }) => {
  if (!explanation) {
    return (
      <div className="card p-5">
        <p className="text-sm text-zinc-500">Agent investigation narrative is unavailable.</p>
      </div>
    );
  }

  const providerLabel =
    explanation.provider_used === "gemini" || explanation.provider_used === "google"
      ? "Gemini"
      : explanation.provider_used === "groq"
        ? "Groq"
        : "Deterministic";

  return (
    <div className="card animate-fade-up delay-200">
      <div className="card-header">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-zinc-500" />
          <p className="text-sm font-semibold text-zinc-100">Investigation Summary</p>
        </div>
        <span className="label font-mono">{providerLabel} · {explanation.generation_status}</span>
      </div>

      <div className="p-5 space-y-5">
        {/* Summary */}
        <p className="text-sm text-zinc-300 leading-relaxed">{explanation.summary}</p>

        {/* Key Findings */}
        {explanation.key_findings.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-3">
              <Lightbulb className="w-3.5 h-3.5 text-zinc-500" />
              <span className="label">Key Findings</span>
            </div>
            <ul className="space-y-2">
              {explanation.key_findings.map((f, i) => (
                <li key={i} className="text-sm text-zinc-400 pl-4 relative before:absolute before:left-0 before:top-[7px] before:w-1 before:h-1 before:rounded-full before:bg-zinc-600">
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Risk explanation */}
        {explanation.risk_explanation && (
          <div className="p-4 rounded-lg bg-surface-raised border border-white/[0.05]">
            <span className="label block mb-2">Risk Assessment</span>
            <p className="text-sm text-zinc-400 leading-relaxed">{explanation.risk_explanation}</p>
          </div>
        )}

        {/* Advisory actions */}
        {explanation.recommended_actions.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-3">
              <ShieldCheck className="w-3.5 h-3.5 text-zinc-500" />
              <span className="label">Advisory SOC Actions</span>
            </div>
            <div className="space-y-2">
              {explanation.recommended_actions.map((a, i) => (
                <div key={i} className="flex items-start gap-3 text-sm text-zinc-400">
                  <span className="label mt-0.5 shrink-0 w-5 text-right font-mono">{i + 1}.</span>
                  <span>{a}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Limitations */}
        {explanation.limitations.length > 0 && (
          <div className="pt-4 border-t border-white/[0.05]">
            <div className="flex items-start gap-2 text-xs text-zinc-600">
              <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              <p>{explanation.limitations.join(" ")}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
