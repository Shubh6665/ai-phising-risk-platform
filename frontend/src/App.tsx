import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Header } from "./components/Header";
import { AnimatedBackground } from "./components/AnimatedBackground";
import { DashboardPage } from "./pages/DashboardPage";
import { PipelineVisualizerPage } from "./pages/PipelineVisualizerPage";
import { AnalysisProvider } from "./context/AnalysisContext";
import { CheckCircle2 } from "lucide-react";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AnalysisProvider>
        <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white relative">
          {/* Subtle Background */}
          <AnimatedBackground />

          {/* Header */}
          <Header />

          {/* Page Routing */}
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/pipeline" element={<PipelineVisualizerPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          {/* Footer */}
          <footer className="border-t border-slate-800/80 py-5 text-center text-xs text-slate-500 font-mono bg-[#0d121f]/80 backdrop-blur-sm">
            <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
              <span>AI Phishing Risk & Triage Platform • Built with FastAPI, PyTorch, ChromaDB, LangGraph & React</span>
              <span className="flex items-center gap-1.5 text-slate-400">
                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                <span>Grounded in NIST SP 800-61 Rev. 3 & MITRE ATT&CK v20.0</span>
              </span>
            </div>
          </footer>
        </div>
      </AnalysisProvider>
    </BrowserRouter>
  );
};
export default App;
