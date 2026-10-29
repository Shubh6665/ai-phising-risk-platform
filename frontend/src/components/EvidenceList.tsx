import React, { useState } from "react";
import { BookOpen, ChevronDown, ChevronUp, ExternalLink, ShieldAlert, CheckCircle2 } from "lucide-react";
import { SecurityEvidenceItem } from "../types/api";

interface EvidenceListProps {
  evidence: SecurityEvidenceItem[];
  status: "retrieved" | "empty" | "unavailable" | "disabled";
}

export const EvidenceList: React.FC<EvidenceListProps> = ({ evidence, status }) => {
  const [expandedChunkId, setExpandedChunkId] = useState<string | null>(
    evidence.length > 0 ? evidence[0].chunk_id : null
  );

  const toggleExpand = (chunkId: string) => {
    setExpandedChunkId(expandedChunkId === chunkId ? null : chunkId);
  };

  const renderStatusBadge = () => {
    switch (status) {
      case "retrieved":
        return (
          <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-cyan-400" />
            <span>{evidence.length} Chunks Retrieved</span>
          </span>
        );
      case "empty":
        return (
          <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
            No Relevant Guidance Matched
          </span>
        );
      case "unavailable":
        return (
          <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-amber-950/80 text-amber-300 border border-amber-800/60 flex items-center gap-1">
            <ShieldAlert className="w-3 h-3 text-amber-400" />
            <span>Retrieval Store Offline / Degraded</span>
          </span>
        );
      case "disabled":
      default:
        return (
          <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-slate-800 text-slate-400 border border-slate-700">
            RAG Disabled by Config
          </span>
        );
    }
  };

  return (
    <div className="bg-[#111726] border border-slate-800 rounded-xl p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-cyan-400" />
            <span>Security Knowledge Base Evidence (RAG)</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Grounded passages retrieved from NIST SP 800-61 Rev. 3, CISA Phishing Guidance, and MITRE ATT&CK v20.0.
          </p>
        </div>
        <div>{renderStatusBadge()}</div>
      </div>

      {status === "empty" && (
        <div className="p-6 text-center text-slate-400 text-xs italic">
          No security knowledge base chunks exceeded similarity threshold for this email.
        </div>
      )}

      {status === "unavailable" && (
        <div className="p-6 text-center text-amber-300/90 text-xs">
          ChromaDB vector store was unavailable during analysis. Risk assessment completed using ML/NLP signals and deterministic degraded fallback.
        </div>
      )}

      {status === "disabled" && (
        <div className="p-6 text-center text-slate-500 text-xs italic">
          RAG evidence retrieval is currently disabled by application configuration (`RAG_ENABLED=False`).
        </div>
      )}

      {status === "retrieved" && evidence.length > 0 && (
        <div className="mt-4 space-y-2.5">
          {evidence.map((item) => {
            const isExpanded = expandedChunkId === item.chunk_id;
            return (
              <div
                key={item.chunk_id}
                className="bg-[#0b0f19] border border-slate-800 rounded-lg overflow-hidden transition-colors"
              >
                <button
                  type="button"
                  onClick={() => toggleExpand(item.chunk_id)}
                  className="w-full text-left px-4 py-3 flex items-center justify-between hover:bg-slate-900/60 transition-colors gap-3"
                  aria-expanded={isExpanded}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-semibold text-cyan-300 truncate">
                        {item.document_title || item.document_name}
                      </span>
                      {item.heading && (
                        <span className="text-[11px] text-slate-400 truncate">
                          › {item.heading}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-[11px] font-mono text-slate-400 flex-wrap">
                      <span>Source: <span className="text-slate-300">{item.source_attribution}</span></span>
                      <span>Cosine Similarity: <span className="text-cyan-400 font-medium">{(item.similarity * 100).toFixed(1)}%</span></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-slate-400 shrink-0">
                    <span className="text-[10px] font-mono uppercase bg-slate-850 px-2 py-0.5 rounded text-slate-300 border border-slate-800">
                      {item.document_type}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </button>

                {isExpanded && (
                  <div className="px-4 py-3 bg-slate-900/40 border-t border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
                    <div className="whitespace-pre-wrap select-text bg-[#070a12] p-3 rounded-lg border border-slate-850 font-mono text-xs text-slate-200">
                      {item.content}
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[11px] font-mono text-slate-500">
                      <span>Chunk ID: {item.chunk_id}</span>
                      <span className="flex items-center gap-1 text-slate-400">
                        <ExternalLink className="w-3 h-3 text-cyan-400" />
                        <span>Authoritative Reference Guidance</span>
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
