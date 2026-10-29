import React from "react";
import { Link2, AlertTriangle, ShieldCheck, Info } from "lucide-react";
import { URLObservation } from "../types/api";

interface InvestigationFindingsProps {
  urls: URLObservation[];
}

export const InvestigationFindings: React.FC<InvestigationFindingsProps> = ({ urls }) => {
  return (
    <div className="bg-[#111726] border border-slate-800 rounded-xl p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Link2 className="w-4 h-4 text-cyan-400" />
            <span>Structural URL Investigation Findings</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Offline lexical structure analysis (RFC 3986 / RFC 1034) with zero external network or DNS resolution.
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300 self-start sm:self-auto">
          {urls.length} URL{urls.length === 1 ? "" : "s"} Extracted
        </span>
      </div>

      {urls.length === 0 ? (
        <div className="p-6 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>No hyperlinks or URLs were detected in the email body content.</span>
        </div>
      ) : (
        <div className="mt-4 space-y-2.5">
          {urls.map((obs, idx) => {
            const hasAnomalies = obs.indicator_count > 0;
            return (
              <div
                key={idx}
                className="bg-[#0b0f19] border border-slate-800 rounded-lg p-3.5 transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-bold text-slate-100 break-all select-text">
                        {obs.hostname || "Unknown Host"}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-850 text-slate-400 uppercase border border-slate-800">
                        {obs.scheme}
                      </span>
                      {obs.port && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-850 text-cyan-400 border border-slate-800">
                          Port {obs.port}
                        </span>
                      )}
                    </div>

                    <div className="mt-1 text-xs font-mono text-slate-500 break-all select-text">
                      Target: {obs.url}
                    </div>
                  </div>

                  <div className="shrink-0">
                    {hasAnomalies ? (
                      <span className="text-xs font-medium text-amber-400 bg-amber-950/60 border border-amber-900/60 px-2.5 py-1 rounded-md flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>{obs.indicator_count} Anomal{obs.indicator_count === 1 ? "y" : "ies"}</span>
                      </span>
                    ) : (
                      <span className="text-xs font-medium text-emerald-400 bg-emerald-950/60 border border-emerald-900/60 px-2.5 py-1 rounded-md flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>Standard Format</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Anomalies list */}
                {hasAnomalies && (
                  <div className="mt-2.5 pt-2.5 border-t border-slate-900 flex flex-wrap gap-1.5">
                    {obs.suspicious_indicators.map((ind, indIdx) => (
                      <span
                        key={indIdx}
                        className="text-xs font-mono px-2 py-0.5 rounded bg-red-950/50 text-red-300 border border-red-900/40"
                      >
                        • {ind}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-4 p-3 rounded-lg bg-[#0b0f19] border border-slate-800 flex items-start gap-2.5 text-xs text-slate-400 leading-relaxed">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">Operational Context:</span> Indicators represent structural anomalies detected via offline lexical inspection. The presence of direct IP literals, userinfo syntax, or deep subdomains warrants SOC correlation, but does not alone confirm hostile staging infrastructure. URLs are intentionally rendered as inert text to prevent accidental browser navigation.
        </div>
      </div>
    </div>
  );
};
