import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { EvidenceList } from "../src/components/EvidenceList";
import { SecurityEvidenceItem } from "../src/types/api";

const MOCK_EVIDENCE: SecurityEvidenceItem[] = [
  {
    chunk_id: "attack_patterns_001_abc",
    content: "Adversaries replicate enterprise login portals to harvest single sign-on credentials.",
    similarity: 0.884,
    document_name: "attack_patterns.md",
    document_title: "Attack Patterns and Threat Actor Tactics",
    heading: "Profile A: Credential Harvesting",
    document_type: "source_backed_guidance",
    source_attribution: "MITRE ATT&CK v20.0",
    is_mock: false,
  },
  {
    chunk_id: "security_policies_002_def",
    content: "Out-of-band identity verification is recommended for all urgent executive financial requests.",
    similarity: 0.765,
    document_name: "security_policies.md",
    document_title: "Project Triage Guidance",
    heading: "Out-of-Band Verification",
    document_type: "source_backed_guidance",
    source_attribution: "NIST SP 800-61 Rev. 3",
    is_mock: false,
  },
];

describe("EvidenceList Component", () => {
  it("renders retrieved evidence items with source attribution", () => {
    render(<EvidenceList evidence={MOCK_EVIDENCE} status="retrieved" />);

    expect(screen.getByText(/Profile A: Credential Harvesting/i)).toBeInTheDocument();
    expect(screen.getByText(/MITRE ATT&CK v20\.0/i)).toBeInTheDocument();
    // 88% match displayed
    expect(screen.getByText(/88% match/i)).toBeInTheDocument();
  });

  it("expands evidence content when clicked", () => {
    render(<EvidenceList evidence={MOCK_EVIDENCE} status="retrieved" />);

    const firstBtn = screen.getByText(/Profile A: Credential Harvesting/i).closest("button");
    expect(firstBtn).not.toBeNull();
    fireEvent.click(firstBtn!);

    expect(screen.getByText(/Adversaries replicate enterprise login portals/i)).toBeInTheDocument();
  });

  it("renders status message when knowledge base returned empty results", () => {
    render(<EvidenceList evidence={[]} status="empty" />);
    expect(screen.getByText(/No relevant knowledge-base context found/i)).toBeInTheDocument();
  });

  it("renders status message when RAG is disabled by configuration", () => {
    render(<EvidenceList evidence={[]} status="disabled" />);
    expect(screen.getByText(/Knowledge-base retrieval is disabled/i)).toBeInTheDocument();
  });
});
