import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { RiskScore } from "../src/components/RiskScore";

describe("RiskScore Component", () => {
  it("renders numerical score, classification tier, and progress bar", () => {
    render(
      <RiskScore
        score={84.5}
        classification="Critical"
        requiresEscalation={true}
        escalationReason="Critical risk tier (score 84.5 >= 80.0)"
        requestId="req-12345"
        analysisId="uuid-persist-001"
      />
    );

    expect(screen.getByText("84.5")).toBeInTheDocument();
    expect(screen.getByText(/Critical Tier/i)).toBeInTheDocument();
    expect(screen.getByText(/Mandatory SOC Escalation/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Escalation/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Critical risk tier/i)).toBeInTheDocument();
    // IDs are truncated to 8 chars with ellipsis
    expect(screen.getByText(/req-1234/i)).toBeInTheDocument();
    expect(screen.getByText(/uuid-per/i)).toBeInTheDocument();

    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-valuenow", "84.5");
  });

  it("renders Low tier without escalation alert", () => {
    render(
      <RiskScore
        score={15.0}
        classification="Low"
        requiresEscalation={false}
        requestId="req-clean-01"
      />
    );

    expect(screen.getByText("15.0")).toBeInTheDocument();
    expect(screen.getByText(/Low Tier/i)).toBeInTheDocument();
    expect(screen.queryByText(/Escalation Required/i)).not.toBeInTheDocument();
  });

  it("renders High tier with escalation banner", () => {
    render(
      <RiskScore
        score={72.3}
        classification="High"
        requiresEscalation={true}
        escalationReason="High confidence model divergence"
        requestId="req-high-01"
      />
    );

    expect(screen.getByText("72.3")).toBeInTheDocument();
    expect(screen.getByText(/High Tier/i)).toBeInTheDocument();
    expect(screen.getByText(/Escalation Required/i)).toBeInTheDocument();
    expect(screen.getByText(/High confidence model divergence/i)).toBeInTheDocument();
  });
});
