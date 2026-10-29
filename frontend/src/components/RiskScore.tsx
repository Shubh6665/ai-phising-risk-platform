import React from "react";
import { ShieldCheck, ShieldAlert, AlertTriangle, AlertOctagon, Flame, ArrowRight, Network } from "lucide-react";

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
          borderColor: "border-red-900/60",
          bgColor: "bg-red-950/20",
          meterColor: "bg-red-500",
          badgeBg: "bg-red-950 text-red-300 border-red-800",
          statusText: "Critical Threat — Immediate Containment & Purge Recommended",
        };
      case "High":
        return {
          icon: Flame,
          textColor: "text-orange-400",
          borderColor: "border-orange-900/60",
          bgColor: "bg-orange-950/20",
          meterColor: "bg-orange-500",
          badgeBg: "bg-orange-950 text-orange-300 border-orange-800",
          statusText: "High Uncertainty — Automated Quarantine & SOC Review Recommended",
        };
      case "Medium":
        return {
          icon: AlertTriangle,
          textColor: "text-amber-400",
          borderColor: "border-amber-900/60",
          bgColor: "bg-amber-950/20",
          meterColor: "bg-amber-500",
          badgeBg: "bg-amber-950 text-amber-300 border-amber-800",
          statusText: "Suspicious Language — Prepend Warning Banner & User Reporting",
        };
      case "Low":
      default:
        return {
          icon: ShieldCheck,
          textColor: "text-emerald-400",
          borderColor: "border-emerald-900/60",
          bgColor: "bg-emerald-950/20",
          meterColor: "bg-emerald-500",
          badgeBg: "bg-emerald-950 text-emerald-300 border-emerald-800",
          statusText: "Clean / Low Risk — Standard Gateway Delivery",
        };
    }
  };

  const config = getTierConfig(classification);
  const IconComponent = config.icon;

  return (
    <div className={`rounded-xl border ${config.borderColor} ${config.bgColor} p-6 shadow-sm`}>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-5">
        {/* Left: Score & Tier Details */}
        <div className="flex items-center gap-5">
          {/* Crisp Numerical Badge */}
          <div className="w-20 h-20 rounded-xl bg-[#0b0f19] border border-slate-800 flex flex-col items-center justify-center shrink-0">
            <span className={`text-2xl font-black font-mono tracking-tight ${config.textColor}`}>
              {score.toFixed(1)}
            </span>
            <span className="text-[10px] uppercase font-mono text-slate-500 font-medium">
              Score / 100
            </span>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold uppercase tracking-wider border ${config.badgeBg}`}
              >
                <IconComponent className="w-3.5 h-3.5" />
                <span>{classification} Tier</span>
              </span>

              {requiresEscalation && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-red-950 text-red-300 border border-red-800">
                  <ShieldAlert className="w-3 h-3 text-red-400" />
                  <span>Mandatory Escalation</span>
                </span>
              )}
            </div>

            <p className="text-sm font-medium text-slate-200">
              {config.statusText}
            </p>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-mono text-slate-400">
              <span>Request ID: <span className="text-slate-200">{requestId}</span></span>
              {analysisId && (
                <span>Analysis ID: <span className="text-slate-200">{analysisId}</span></span>
              )}
            </div>
          </div>
        </div>

        {/* Right: Progress Bar & Pipeline Link */}
        <div className="w-full md:w-64 flex flex-col justify-center space-y-2.5 pt-3 md:pt-0 border-t md:border-t-0 border-slate-800">
          <div className="flex justify-between items-center text-xs font-mono">
            <span className="text-slate-400">Threat Severity</span>
            <span className={`font-semibold ${config.textColor}`}>{score.toFixed(1)}%</span>
          </div>

          <div className="w-full h-2.5 bg-[#0b0f19] rounded-full overflow-hidden p-0.5 border border-slate-800">
            <div
              className={`h-full rounded-full transition-all duration-500 ease-out ${config.meterColor}`}
              style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
              role="progressbar"
              aria-valuenow={score}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>

          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>0.0 (Low)</span>
            <span>40.0</span>
            <span>60.0</span>
            <span>100.0 (Critical)</span>
          </div>

          <a
            href="/pipeline"
            className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-[#0b0f19] hover:bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white transition-colors"
          >
            <span className="flex items-center gap-1.5 text-xs">
              <Network className="w-3.5 h-3.5 text-cyan-400" />
              <span>Trace in Backend Flow</span>
            </span>
            <ArrowRight className="w-3 h-3 text-slate-500" />
          </a>
        </div>
      </div>

      {/* Escalation Alert */}
      {requiresEscalation && (
        <div className="mt-4 p-3.5 rounded-lg bg-red-950/60 border border-red-900/80 flex items-start gap-2.5 text-red-200 text-xs">
          <AlertOctagon className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold text-red-300">SOC Operational Escalation Rule Triggered:</span>{" "}
            {escalationReason || "Composite risk score or model divergence mandates analyst review."}
          </div>
        </div>
      )}
    </div>
  );
};
