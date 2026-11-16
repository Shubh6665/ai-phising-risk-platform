import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Header } from "./components/Header";
import { AnimatedBackground } from "./components/AnimatedBackground";
import { DashboardPage } from "./pages/DashboardPage";
import { PipelineVisualizerPage } from "./pages/PipelineVisualizerPage";
import { AnalysisProvider } from "./context/AnalysisContext";
import { useLenis } from "./hooks/useLenis";

/** Inner wrapper — useLenis needs to be inside BrowserRouter */
const AppInner: React.FC = () => {
  useLenis();

  return (
    <AnalysisProvider>
      <div className="min-h-screen flex flex-col">
        <AnimatedBackground />
        <Header />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/pipeline" element={<PipelineVisualizerPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="border-t border-white/[0.05] py-6 mt-auto">
          <div className="max-w-6xl mx-auto px-5 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
            <span className="text-xs text-zinc-600">
              AI Phishing Risk &amp; Triage Platform · FastAPI · PyTorch · ChromaDB · LangGraph · React
            </span>
            <span className="text-xs text-zinc-600">
              Grounded in NIST SP 800-61 Rev. 3 · MITRE ATT&amp;CK v20.0
            </span>
          </div>
        </footer>
      </div>
    </AnalysisProvider>
  );
};

export const App: React.FC = () => (
  <BrowserRouter>
    <AppInner />
  </BrowserRouter>
);

export default App;
