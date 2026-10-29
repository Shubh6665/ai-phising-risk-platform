import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ExplanationPanel } from "../src/components/ExplanationPanel";
import { InvestigationExplanation } from "../src/types/api";

const LLM_EXPLANATION: InvestigationExplanation = {
  summary: "Email triage detected an urgent credential harvesting campaign hosted on an IP address.",
  key_findings: [
    "Observed direct IP literal 192.168.1.100",
    "High classical probability (0.82) and transformer probability (0.86)",
  ],
  risk_explanation: "The email was classified as Critical risk based on multi-model convergence and explicit urgency cues.",
  recommended_actions: [
    "Immediate perimeter blocklist enforcement",
    "Advise targeted recipients to report suspicious communications",
  ],
  limitations: [
    "Static lexical analysis only; dynamic sandbox detonation was not performed",
  ],
  evidence_references: ["attack_patterns_001_abc"],
  provider_used: "google",
  generation_status: "completed",
};

const DEGRADED_EXPLANATION: InvestigationExplanation = {
  summary: "Email analysis completed with risk score 72.0 (High tier). Automated recommended operational action: Automated Quarantine.",
  key_findings: ["Observed 1 URL(s)", "Urgency keywords detected"],
  risk_explanation: "Categorized based on statistical and transformer semantic classification.",
  recommended_actions: ["Quarantine payload", "Secondary SOC analyst review"],
  limitations: ["Generative narrative unavailable; fallback to deterministic rules."],
  evidence_references: [],
  provider_used: null,
  generation_status: "degraded",
};

describe("ExplanationPanel Component", () => {
  it("renders LLM-generated narrative, key findings, and recommendations", () => {
    render(<ExplanationPanel explanation={LLM_EXPLANATION} />);

    expect(screen.getByText(/Google Gemini 3\.8 Flash \(Primary LLM\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Status: completed/i)).toBeInTheDocument();
    expect(screen.getByText(/Email triage detected an urgent credential harvesting campaign/i)).toBeInTheDocument();
    expect(screen.getByText(/Observed direct IP literal 192\.168\.1\.100/i)).toBeInTheDocument();
    expect(screen.getByText(/Immediate perimeter blocklist enforcement/i)).toBeInTheDocument();
    expect(screen.getByText(/Advisory Controls/i)).toBeInTheDocument();
    expect(screen.getByText(/Citations: attack_patterns_001_abc/i)).toBeInTheDocument();
  });

  it("renders deterministic degraded generator metadata when LLM was unavailable", () => {
    render(<ExplanationPanel explanation={DEGRADED_EXPLANATION} />);

    expect(screen.getByText(/Deterministic Degraded Generator/i)).toBeInTheDocument();
    expect(screen.getByText(/Status: degraded/i)).toBeInTheDocument();
    expect(screen.getByText(/Automated recommended operational action: Automated Quarantine/i)).toBeInTheDocument();
  });

  it("renders fallback message when explanation is null or undefined", () => {
    render(<ExplanationPanel explanation={null} />);
    expect(screen.getByText(/Agent investigation narrative is unavailable/i)).toBeInTheDocument();
  });
});

