import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { App } from "../src/App";
import * as api from "../src/services/api";
import { AnalyzeResponse } from "../src/types/api";

const MOCK_RESPONSE: AnalyzeResponse = {
  request_id: "req-app-test-001",
  analysis_id: "persist-uuid-999",
  risk_score: 84.5,
  classification: "Critical",
  ml_probability: 0.82,
  nlp_probability: 0.88,
  rule_bonus: 10.0,
  requires_escalation: true,
  escalation_reason: "Critical risk tier (score 84.5 >= 80.0); recommends high-priority SOC containment review.",
  evidence_status: "retrieved",
  evidence: [
    {
      chunk_id: "attack_patterns_001",
      content: "Credential harvesting portal patterns.",
      similarity: 0.85,
      document_name: "attack_patterns.md",
      document_title: "Attack Patterns",
      heading: "AiTM Harvesting",
      document_type: "source_backed_guidance",
      source_attribution: "MITRE ATT&CK v20.0",
      is_mock: false,
    },
  ],
  url_analysis: [
    {
      url: "http://192.168.1.1:8080/login",
      scheme: "http",
      hostname: "192.168.1.1",
      port: 8080,
      is_ip_literal: true,
      has_unusual_port: true,
      has_userinfo: false,
      has_punycode: false,
      subdomain_depth: 0,
      indicator_count: 2,
      suspicious_indicators: ["IP address literal hostname", "Non-standard web port"],
    },
  ],
  explanation: {
    summary: "Critical credential harvesting threat detected.",
    key_findings: ["Observed IP literal host", "Urgent language detected"],
    risk_explanation: "High classical and deep NLP probability converged on phishing classification.",
    recommended_actions: ["Enforce perimeter blocklist", "Enterprise mailbox purge"],
    limitations: ["Static analysis only"],
    evidence_references: ["attack_patterns_001"],
    provider_used: "google",
    generation_status: "completed",
  },
};

describe("App Root Integration Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders initial empty state with header and form before analysis", () => {
    render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: /AI Phishing Risk & Triage Platform/i })).toBeInTheDocument();
    expect(screen.getByText(/No Analysis Executed Yet/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Analyze Email/i })).toBeInTheDocument();
  });

  it("submits email, receives API response, and displays full dashboard sections", async () => {
    const analyzeSpy = vi.spyOn(api, "analyzeEmail").mockResolvedValue(MOCK_RESPONSE);

    render(<App />);

    const bodyInput = screen.getByLabelText(/Email Body Content/i);
    await userEvent.type(bodyInput, "Please verify your account immediately at http://192.168.1.1:8080/login");

    const submitBtn = screen.getByRole("button", { name: /Analyze Email/i });
    fireEvent.click(submitBtn);

    // Initial state disappears and results appear
    await waitFor(() => {
      expect(screen.getByText("84.5")).toBeInTheDocument();
    });

    expect(analyzeSpy).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/Critical Tier/i)).toBeInTheDocument();
    expect(screen.getByText(/Critical credential harvesting threat detected/i)).toBeInTheDocument();
    expect(screen.getAllByText(/192\.168\.1\.1/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Attack Patterns/i)).toBeInTheDocument();
    expect(screen.queryByText(/No Analysis Executed Yet/i)).not.toBeInTheDocument();
  });

  it("displays alert when API returns an error", async () => {
    vi.spyOn(api, "analyzeEmail").mockRejectedValue(
      new api.ApiError("Failed to persist analysis result.", 500)
    );

    render(<App />);

    const bodyInput = screen.getByLabelText(/Email Body Content/i);
    await userEvent.type(bodyInput, "Suspicious message payload");

    const submitBtn = screen.getByRole("button", { name: /Analyze Email/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByText(/Analysis Request Failed/i)).toBeInTheDocument();
    expect(screen.getByText(/Failed to persist analysis result\./i)).toBeInTheDocument();
  });

  it("clears analysis results when Clear button is clicked", async () => {
    vi.spyOn(api, "analyzeEmail").mockResolvedValue(MOCK_RESPONSE);

    render(<App />);

    const bodyInput = screen.getByLabelText(/Email Body Content/i);
    await userEvent.type(bodyInput, "Email text content");
    fireEvent.click(screen.getByRole("button", { name: /Analyze Email/i }));

    await waitFor(() => {
      expect(screen.getByText("84.5")).toBeInTheDocument();
    });

    const clearBtn = screen.getByRole("button", { name: /Clear/i });
    fireEvent.click(clearBtn);

    expect(screen.queryByText("84.5")).not.toBeInTheDocument();
    expect(screen.getByText(/No Analysis Executed Yet/i)).toBeInTheDocument();
  });
});
