import React from "react";
import { NavLink } from "react-router-dom";
import { ShieldCheck, Cpu, Network, LayoutDashboard } from "lucide-react";

export const Header: React.FC = () => {
  return (
    <header className="border-b border-slate-800 bg-[#0d121f]/90 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Branding & Title */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-cyan-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-bold tracking-tight text-white flex items-center gap-2">
              <span>AI Phishing Risk & Triage Platform</span>
            </h1>
            <p className="text-xs text-slate-400 font-normal">
              Multi-Layer Defense: Random Forest + DistilBERT + RAG + LangGraph SOC Agent
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1.5 w-full md:w-auto justify-center" aria-label="Main Navigation">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                isActive
                  ? "bg-slate-800 text-white border border-slate-700"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
              }`
            }
          >
            <LayoutDashboard className="w-3.5 h-3.5 text-cyan-400" />
            <span>Analysis</span>
          </NavLink>

          <NavLink
            to="/pipeline"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                isActive
                  ? "bg-slate-800 text-white border border-slate-700"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
              }`
            }
          >
            <Network className="w-3.5 h-3.5 text-violet-400" />
            <span>Backend Overview & System Design</span>
          </NavLink>
        </nav>

        {/* Status Pill */}
        <div className="hidden lg:flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span>Active Ensemble: RF + DistilBERT + RAG + Gemini/Groq</span>
        </div>
      </div>
    </header>
  );
};
