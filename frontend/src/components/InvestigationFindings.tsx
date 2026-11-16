import React from "react";
import { Link2, AlertCircle } from "lucide-react";
import { URLObservation } from "../types/api";

interface InvestigationFindingsProps {
  urls: URLObservation[];
}

export const InvestigationFindings: React.FC<InvestigationFindingsProps> = ({ urls }) => {
  if (urls.length === 0) {
    return (
      <div className="card p-5">
        <p className="text-sm text-zinc-500 flex items-center gap-2">
          <Link2 className="w-4 h-4" />
          No URLs detected in email body.
        </p>
      </div>
    );
  }

  return (
    <div className="card animate-fade-up delay-100">
      <div className="card-header">
        <div className="flex items-center gap-2">
          <Link2 className="w-4 h-4 text-zinc-500" />
          <p className="text-sm font-semibold text-zinc-100">URL Analysis</p>
        </div>
        <span className="label">{urls.length} url{urls.length !== 1 ? "s" : ""}</span>
      </div>

      <div className="divide-y divide-white/[0.04]">
        {urls.map((url, i) => (
          <div key={i} className="px-5 py-4 space-y-2.5">
            {/* Inert text — NEVER an anchor tag */}
            <p
              className="text-xs font-mono text-zinc-300 break-all select-text leading-relaxed"
              aria-label="Extracted URL (non-navigable, inert text display)"
            >
              {url.url}
            </p>

            {/* Anomaly tags */}
            {url.suspicious_indicators.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {url.suspicious_indicators.map((ind) => (
                  <span
                    key={ind}
                    className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400"
                  >
                    <AlertCircle className="w-3 h-3" />
                    {ind.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            )}

            {/* Metadata row */}
            <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] text-zinc-500">
              <span>scheme: {url.scheme}</span>
              {url.hostname && <span>host: {url.hostname}</span>}
              {url.port && <span>port: {url.port}</span>}
              <span>depth: {url.subdomain_depth}</span>
              <span>flags: {url.indicator_count}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
