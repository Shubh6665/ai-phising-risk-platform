import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ModelBreakdown } from "../src/components/ModelBreakdown";

describe("ModelBreakdown Component", () => {
  it("renders classical ML probability, transformer NLP probability, and rule bonus", () => {
    render(
      <ModelBreakdown
        mlProbability={0.785}
        nlpProbability={0.824}
        ruleBonus={10.0}
      />
    );

    expect(screen.getByText("78.5%")).toBeInTheDocument();
    expect(screen.getByText(/\(p = 0\.7850\)/i)).toBeInTheDocument();
    expect(screen.getByText("82.4%")).toBeInTheDocument();
    expect(screen.getByText(/\(p = 0\.8240\)/i)).toBeInTheDocument();
    expect(screen.getByText("+10.0")).toBeInTheDocument();
    expect(screen.getByText(/Classical ML/i)).toBeInTheDocument();
    expect(screen.getByText(/Transformer NLP/i)).toBeInTheDocument();
  });

  it("highlights significant model divergence when probability delta > 0.30", () => {
    render(
      <ModelBreakdown
        mlProbability={0.20}
        nlpProbability={0.65}
        ruleBonus={0.0}
      />
    );

    // Delta = 0.450 (45.0%) > 0.30
    expect(screen.getByText(/Δ 45\.0% \(High\)/i)).toBeInTheDocument();
  });
});

