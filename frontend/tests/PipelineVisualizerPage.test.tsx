import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { PipelineVisualizerPage } from "../src/pages/PipelineVisualizerPage";
import { AnalysisProvider } from "../src/context/AnalysisContext";

const renderPipelinePage = () => {
  return render(
    <BrowserRouter>
      <AnalysisProvider>
        <PipelineVisualizerPage />
      </AnalysisProvider>
    </BrowserRouter>
  );
};

describe("PipelineVisualizerPage Component", () => {
  it("renders page header, system design title, and live simulator section", () => {
    renderPipelinePage();

    expect(
      screen.getByRole("heading", { level: 1, name: /System Design & Pipeline Data Flow Inspector/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/Live Payload Simulator & Trace Input/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Simulate Flow Execution/i })).toBeInTheDocument();
  });

  it("renders all 7 architectural pipeline steps", () => {
    renderPipelinePage();

    expect(screen.getByText(/7 Connected Sub-systems/i)).toBeInTheDocument();
    expect(screen.getAllByText(/FastAPI Gateway/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Data Preprocessing/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Dual ML/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Phase 5/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/ChromaDB Vector/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/LangGraph Multi-Tool/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/PostgreSQL Persistence/i).length).toBeGreaterThan(0);
  });

  it("switches displayed step details when a step node is clicked", () => {
    renderPipelinePage();

    // Default step is step 1 (FastAPI Gateway)
    expect(screen.getByText(/POST \/api\/v1\/analyze/i)).toBeInTheDocument();
    expect(screen.getByText(/src\/api\/routes\/analyze\.py/i)).toBeInTheDocument();

    // Click Step 5 (ChromaDB Vector)
    const ragStepBtn = screen.getByText(/ChromaDB Vector/i).closest("button");
    expect(ragStepBtn).not.toBeNull();
    fireEvent.click(ragStepBtn!);

    expect(
      screen.getByRole("heading", { level: 2, name: /ChromaDB Vector Retrieval \(RAG Pipeline\)/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/src\/rag\/retriever\.py/i)).toBeInTheDocument();
    expect(screen.getByText(/384-dimensional Dense Embeddings/i)).toBeInTheDocument();
  });

  it("allows updating simulator subject and body payload", async () => {
    renderPipelinePage();

    const subjectInput = screen.getByPlaceholderText(/Subject line\.\.\./i);
    const bodyInput = screen.getByPlaceholderText(/Raw email payload\.\.\./i);

    await userEvent.clear(subjectInput);
    await userEvent.type(subjectInput, "Simulated Phishing Wave");
    expect(subjectInput).toHaveValue("Simulated Phishing Wave");

    await userEvent.clear(bodyInput);
    await userEvent.type(bodyInput, "Suspicious link at http://badhost.biz");
    expect(bodyInput).toHaveValue("Suspicious link at http://badhost.biz");
  });
});
