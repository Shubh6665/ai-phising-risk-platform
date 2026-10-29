import React from "react";
import { ShieldCheck, ShieldAlert, AlertTriangle, AlertOctagon, Flame } from "lucide-react";

interface RiskScoreProps {
  score: number;
  classification: "Low" | "Medium" | "High" | "Critical";
  requiresEscalation: boolean;
  escalationReason?: string | null;
  requestId: string;
  analysisId?: string | null;
}

export const RiskScore: React.FC<RiskScoreProps> = ({
  score,
  classification,
  requiresEscalation,
  escalationReason,
  requestId,
  analysisId,
}) => {
  const getTierConfig = (tier: string) => {
    switch (tier) {
      case "Critical":
        return {
          icon: AlertOctagon,
          textColor: "text-red-400",
          bgColor: "bg-red-950/40",
          borderColor: "border-red-600/40",
          meterColor: "bg-gradient-to-r from-orange-500 to-red-600",
          badgeBg: "bg-red-900/60 text-red-200 border-red-700/60",
          statusText: "Critical Threat — Immediate Containment & Purge Recommended",
        };
      case "High":
        return {
          icon: Flame,
          textColor: "text-orange-400",
          bgColor: "bg-orange-950/40",
          borderColor: "border-orange-600/40",
          meterColor: "bg-gradient-to-r from-amber-500 to-orange-500",
          badgeBg: "bg-orange-900/60 text-orange-200 border-orange-700/60",
          statusText: "High Uncertainty — Automated Quarantine & SOC Review Recommended",
        };
      case "Medium":
        return {
          icon: AlertTriangle,
          textColor: "text-yellow-400",
          bgColor: "bg-yellow-950/40",
          borderColor: "border-yellow-600/40",
          meterColor: "bg-gradient-to-r from-emerald-500 to-yellow-500",
          badgeBg: "bg-yellow-900/60 text-yellow-200 border-yellow-700/60",
          statusText: "Suspicious Language — Prepend Warning Banner & User Reporting",
        };
      case "Low":
      default:
        return {
          icon: ShieldCheck,
          textColor: "text-emerald-400",
          bgColor: "bg-emerald-950/40",
          borderColor: "border-emerald-600/40",
          meterColor: "bg-gradient-to-r from-teal-500 to-emerald-500",
          badgeBg: "bg-emerald-900/60 text-emerald-200 border-emerald-700/60",
          statusText: "Clean / Low Risk — Standard Gateway Delivery",
        };
    }
  };

  const config = getTierConfig(classification);
  const IconComponent = config.icon;

  return (
    <div className={`rounded-2xl border ${config.borderColor} ${config.bgColor} p-6 shadow-xl relative overflow-hidden backdrop-blur-sm`}>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Left: Score and Tier */}
        <div className="flex items-center gap-5">
          <div className="relative flex items-center justify-center">
            <div className="w-24 h-24 rounded-full border-4 border-slate-800 flex flex-col items-center justify-center bg-slate-950/80 shadow-inner">
              <span className={`text-3xl font-extrabold tracking-tight ${config.textColor}`}>
                {score.toFixed(1)}
              </span>
              <span className="text-[10px] uppercase font-mono text-slate-500">
                Score / 100
              </span>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2.5">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${config.badgeBg}`}>
                <IconComponent className="w-3.5 h-3.5" />
                {classification} Tier
              </span>
              {requiresEscalation && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-red-500/20 text-red-300 border border-red-500/30 animate-pulse">
                  <ShieldAlert className="w-3 h-3" />
                  Mandatory Escalation
                </span>
              )}
            </div>
            <p className="text-sm font-medium text-slate-200 mt-2">
              {config.statusText}
            </p>
            <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] font-mono text-slate-400">
              <span>Request ID: <span className="text-slate-300">{requestId}</span></span>
              {analysisId && (
                <span>Analysis ID: <span className="text-slate-300">{analysisId}</span></span>
              )}
            </div>
          </div>
        </div>

        {/* Right: Score Progress Bar */}
        <div className="w-full md:w-64 flex flex-col justify-center">
          <div className="flex justify-between text-xs font-mono text-slate-400 mb-1.5">
            <span>Threat Severity</span>
            <span className={config.textColor}>{score.toFixed(1)}%</span>
          </div>
          <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-800">
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${config.meterColor}`}
              style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
              role="progressbar"
              aria-valuenow={score}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
          <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
            <span>0.0 (Low)</span>
            <span>40.0</span>
            <span>60.0</span>
            <span>100.0 (Critical)</span>
          </div>
        </div>
      </div>

      {/* Escalation alert banner if triggered */}
      {requiresEscalation && (
        <div className="mt-5 p-3.5 rounded-xl bg-red-950/80 border border-red-700/50 flex items-start gap-3 text-red-200 text-xs">
          <AlertOctagon className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-red-300">SOC Operational Escalation Rule Triggered:</span>{" "}
            {escalationReason || "Composite risk score or model divergence mandates analyst review."}
          </div>
        </div>
      )}
    </div>
  );
};

