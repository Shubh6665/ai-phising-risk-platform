import React, { useState } from "react";
import { ChevronDown, BookOpen } from "lucide-react";
import { SecurityEvidenceItem } from "../types/api";

interface EvidenceListProps {
  evidence: SecurityEvidenceItem[];
  status: "retrieved" | "empty" | "unavailable" | "disabled";
}

const StatusInfo: React.FC<{ text: string }> = ({ text }) => (
  <div className="card p-5">
    <p className="text-sm text-zinc-500">{text}</p>
  </div>
);

export const EvidenceList: React.FC<EvidenceListProps> = ({ evidence, status }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (status === "disabled")
    return <StatusInfo text="Knowledge-base retrieval is disabled in this configuration." />;
  if (status === "unavailable")
    return <StatusInfo text="Knowledge-base retrieval is currently unavailable." />;
  if (status === "empty" || evidence.length === 0)
    return <StatusInfo text="No relevant knowledge-base context found for this email." />;

  return (
    <div className="card animate-fade-up delay-150">
      <div className="card-header">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-zinc-500" />
          <p className="text-sm font-semibold text-zinc-100">Security Evidence</p>
        </div>
        <span className="label">{evidence.length} chunk{evidence.length !== 1 ? "s" : ""}</span>
      </div>

      <div className="divide-y divide-white/[0.04]">
        {evidence.map((item) => {
          const isOpen = expandedId === item.chunk_id;
          return (
            <div key={item.chunk_id}>
              <button
                onClick={() => setExpandedId(isOpen ? null : item.chunk_id)}
                className="w-full px-5 py-3.5 flex items-center justify-between gap-3 text-left hover:bg-white/[0.02] transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-medium text-zinc-300 truncate">
                      {item.document_title || item.document_name}
                      {item.heading ? ` · ${item.heading}` : ""}
                    </span>
                    <span className="label shrink-0">
                      {(item.similarity * 100).toFixed(0)}% match
                    </span>
                  </div>
                  <span className="text-[11px] text-zinc-500 truncate block">{item.source_attribution}</span>
                </div>
                <ChevronDown
                  className={`w-4 h-4 text-zinc-600 shrink-0 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
                />
              </button>

              {isOpen && (
                <div className="px-5 pb-4 pt-3 bg-surface-raised border-t border-white/[0.04]">
                  <p className="text-xs font-mono text-zinc-400 leading-relaxed whitespace-pre-wrap">
                    {item.content}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
