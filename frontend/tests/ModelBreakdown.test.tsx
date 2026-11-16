import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ModelBreakdown } from "../src/components/ModelBreakdown";

describe("ModelBreakdown Component", () => {
  it("renders classical ML probability, NLP probability, and rule bonus", () => {
    render(
      <ModelBreakdown
        mlProbability={0.785}
        nlpProbability={0.824}
        ruleBonus={10.0}
      />
    );

    expect(screen.getByText("78.5%")).toBeInTheDocument();
    expect(screen.getByText("82.4%")).toBeInTheDocument();
    expect(screen.getByText("+10.0")).toBeInTheDocument();
    expect(screen.getByText(/Random Forest/i)).toBeInTheDocument();
    expect(screen.getByText(/DistilBERT/i)).toBeInTheDocument();
  });

  it("highlights significant model divergence when probability delta > 0.30", () => {
    render(
      <ModelBreakdown
        mlProbability={0.20}
        nlpProbability={0.65}
        ruleBonus={0.0}
      />
    );

    // Delta = 0.45 → 45%
    expect(screen.getByText(/Δ 45% divergence/i)).toBeInTheDocument();
  });
});
