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
    expect(screen.getByText(/Immediate Containment & Purge Recommended/i)).toBeInTheDocument();
    expect(screen.getByText(/Mandatory Escalation/i)).toBeInTheDocument();
    expect(screen.getByText(/Critical risk tier \(score 84.5 >= 80.0\)/i)).toBeInTheDocument();
    expect(screen.getByText(/req-12345/i)).toBeInTheDocument();
    expect(screen.getByText(/uuid-persist-001/i)).toBeInTheDocument();

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
    expect(screen.getByText(/Standard Gateway Delivery/i)).toBeInTheDocument();
    expect(screen.queryByText(/Mandatory Escalation/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Operational Escalation Rule Triggered/i)).not.toBeInTheDocument();
  });

  it("renders High tier with quarantine guidance", () => {
    render(
      <RiskScore
        score={68.2}
        classification="High"
        requiresEscalation={true}
        escalationReason="High-uncertainty triage tier (score 68.2 in 60.0–79.9)"
        requestId="req-high-01"
      />
    );

    expect(screen.getByText("68.2")).toBeInTheDocument();
    expect(screen.getByText(/High Tier/i)).toBeInTheDocument();
    expect(screen.getByText(/Automated Quarantine & SOC Review Recommended/i)).toBeInTheDocument();
  });
});

