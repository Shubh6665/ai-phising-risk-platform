import React from "react";
import { ShieldCheck, ShieldAlert, AlertTriangle, AlertOctagon } from "lucide-react";

interface RiskScoreProps {
  score: number;
  classification: string;
  requiresEscalation: boolean;
  escalationReason?: string | null;
  requestId: string;
  analysisId?: string | null;
}

const getTierConfig = (tier: string) => {
  switch (tier) {
    case "Critical":
      return {
        icon: AlertOctagon,
        accent: "#ef4444",
        label: "Critical Tier",
        bar: "bg-red-500",
        badge: "text-red-300 bg-red-500/10 border-red-500/20",
        statusText: "High-Confidence Phishing — Mandatory SOC Escalation",
      };
    case "High":
      return {
        icon: ShieldAlert,
        accent: "#f97316",
        label: "High Tier",
        bar: "bg-orange-500",
        badge: "text-orange-300 bg-orange-500/10 border-orange-500/20",
        statusText: "High Uncertainty — Automated Quarantine & SOC Review Recommended",
      };
    case "Medium":
      return {
        icon: AlertTriangle,
        accent: "#eab308",
        label: "Medium Tier",
        bar: "bg-yellow-500",
        badge: "text-yellow-300 bg-yellow-500/10 border-yellow-500/20",
        statusText: "Suspicious Language — Prepend Warning Banner & User Reporting",
      };
    default:
      return {
        icon: ShieldCheck,
        accent: "#22c55e",
        label: "Low Tier",
        bar: "bg-emerald-500",
        badge: "text-emerald-300 bg-emerald-500/10 border-emerald-500/20",
        statusText: "Clean / Low Risk — Standard Gateway Delivery",
      };
  }
};

export const RiskScore: React.FC<RiskScoreProps> = ({
  score,
  classification,
  requiresEscalation,
  escalationReason,
  requestId,
  analysisId,
}) => {
  const cfg = getTierConfig(classification);
  const Icon = cfg.icon;

  return (
    <div className="card animate-fade-up">
      <div className="p-5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          {/* Score circle */}
          <div
            className="w-[72px] h-[72px] rounded-2xl flex flex-col items-center justify-center shrink-0 border border-white/[0.07]"
            style={{ background: `${cfg.accent}12` }}
          >
            <span className="text-2xl font-bold font-mono tracking-tight" style={{ color: cfg.accent }}>
              {score.toFixed(1)}
            </span>
            <span className="label mt-0.5">/ 100</span>
          </div>

          {/* Details */}
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${cfg.badge}`}>
                <Icon className="w-3.5 h-3.5" />
                {cfg.label}
              </span>
              {requiresEscalation && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold text-red-300 bg-red-500/10 border border-red-500/20">
                  Escalation Required
                </span>
              )}
            </div>
            <p className="text-sm text-zinc-300 font-medium mb-2">{cfg.statusText}</p>
            <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] text-zinc-500">
              <span>req:{requestId.slice(0, 8)}…</span>
              {analysisId && <span>db:{analysisId.slice(0, 8)}…</span>}
            </div>
          </div>

          {/* Bar */}
          <div className="w-full sm:w-48 shrink-0">
            <div className="flex justify-between font-mono text-[11px] text-zinc-500 mb-1.5">
              <span>Threat level</span>
              <span style={{ color: cfg.accent }}>{score.toFixed(1)}%</span>
            </div>
            <div className="h-1.5 w-full bg-white/[0.05] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-out ${cfg.bar}`}
                style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                role="progressbar"
                aria-valuenow={score}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
            <div className="flex justify-between font-mono text-[10px] text-zinc-600 mt-1">
              <span>0</span><span>40</span><span>60</span><span>100</span>
            </div>
          </div>
        </div>

        {/* Escalation banner */}
        {requiresEscalation && (
          <div className="mt-4 p-3 rounded-lg border border-red-500/15 bg-red-500/5 text-xs text-zinc-400 flex items-start gap-2.5">
            <AlertOctagon className="w-3.5 h-3.5 text-red-400 shrink-0 mt-0.5" />
            <span>
              <strong className="text-red-300 font-medium">Escalation triggered: </strong>
              {escalationReason || "Composite risk score or model divergence mandates analyst review."}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
