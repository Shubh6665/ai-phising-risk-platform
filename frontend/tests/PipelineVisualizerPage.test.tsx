import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { PipelineVisualizerPage } from "../src/pages/PipelineVisualizerPage";

const renderPage = () =>
  render(
    <BrowserRouter>
      <PipelineVisualizerPage />
    </BrowserRouter>
  );

describe("PipelineVisualizerPage Component", () => {
  it("renders page header and pipeline stage list", () => {
    renderPage();

    expect(screen.getByText(/Backend Request Pipeline/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Processing Stages/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/9 steps/i)).toBeInTheDocument();
  });

  it("renders all pipeline stage titles", () => {
    renderPage();

    expect(screen.getByText(/FastAPI Gateway/i)).toBeInTheDocument();
    expect(screen.getByText(/Feature Engineering/i)).toBeInTheDocument();
    expect(screen.getByText(/Dual ML/i)).toBeInTheDocument();
    expect(screen.getByText(/Ensemble Scoring/i)).toBeInTheDocument();
    expect(screen.getByText(/PostgreSQL Persistence/i)).toBeInTheDocument();
    expect(screen.getByText(/RAG Evidence Retrieval/i)).toBeInTheDocument();
    expect(screen.getByText(/LangGraph Agent/i)).toBeInTheDocument();
    expect(screen.getByText(/LLM Explanation/i)).toBeInTheDocument();
    expect(screen.getByText(/Response Assembly/i)).toBeInTheDocument();
  });

  it("displays step detail panel when a step is clicked", () => {
    renderPage();

    const gatewayBtn = screen.getByText(/FastAPI Gateway/).closest("button");
    expect(gatewayBtn).not.toBeNull();
    fireEvent.click(gatewayBtn!);

    expect(screen.getAllByText(/POST \/api\/v1\/analyze/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/src\/api\/routes\/analyze\.py/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Internal Operations/i).length).toBeGreaterThan(0);
  });

  it("renders input and output schema sections in detail view", () => {
    renderPage();

    const ragBtn = screen.getByText(/RAG Evidence Retrieval/i).closest("button");
    expect(ragBtn).not.toBeNull();
    fireEvent.click(ragBtn!);

    expect(screen.getAllByText(/Input Schema/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Output Contract/i).length).toBeGreaterThan(0);
  });
});
