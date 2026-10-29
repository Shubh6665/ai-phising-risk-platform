import React from "react";
import { ShieldAlert, Cpu } from "lucide-react";

export const Header: React.FC = () => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/20 rounded-xl text-cyan-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              AI Phishing Risk & Triage Platform
            </h1>
            <p className="text-xs text-slate-400 font-medium">
              Multi-Layer Defense: Random Forest + DistilBERT + RAG + LangGraph SOC Agent
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-850 px-3 py-1.5 rounded-lg border border-slate-800">
          <Cpu className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span>Active Ensemble: RF + DistilBERT + RAG + Gemini/Groq</span>
        </div>
      </div>
    </header>
  );
};

