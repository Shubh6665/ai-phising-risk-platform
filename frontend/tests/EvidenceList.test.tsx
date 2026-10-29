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
    source_attribution: "NIST SP 800-61 Rev. 3; CISA",
    is_mock: false,
  },
];

describe("EvidenceList Component", () => {
  it("renders retrieved evidence items with source attribution and expandable content", () => {
    render(<EvidenceList evidence={MOCK_EVIDENCE} status="retrieved" />);

    expect(screen.getByText(/2 Chunks Retrieved/i)).toBeInTheDocument();
    expect(screen.getByText(/Attack Patterns and Threat Actor Tactics/i)).toBeInTheDocument();
    expect(screen.getAllByText(/MITRE ATT&CK v20\.0/i).length).toBeGreaterThan(0);
    expect(screen.getByText("88.4%")).toBeInTheDocument();

    // First item is expanded by default
    expect(screen.getByText(/Adversaries replicate enterprise login portals/i)).toBeInTheDocument();

    // Expand second item
    const secondItemBtn = screen.getByText(/Project Triage Guidance/i);
    fireEvent.click(secondItemBtn);

    expect(screen.getByText(/Out-of-band identity verification is recommended/i)).toBeInTheDocument();
  });

  it("renders distinct status banner when knowledge base returned empty results", () => {
    render(<EvidenceList evidence={[]} status="empty" />);
    expect(screen.getByText(/No Relevant Guidance Matched/i)).toBeInTheDocument();
    expect(
      screen.getByText(/No security knowledge base chunks exceeded similarity threshold/i)
    ).toBeInTheDocument();
  });

  it("renders distinct status banner when retrieval store is unavailable/offline", () => {
    render(<EvidenceList evidence={[]} status="unavailable" />);
    expect(screen.getByText(/Retrieval Store Offline \/ Degraded/i)).toBeInTheDocument();
    expect(
      screen.getByText(/ChromaDB vector store was unavailable during analysis/i)
    ).toBeInTheDocument();
  });

  it("renders distinct status banner when RAG is disabled by configuration", () => {
    render(<EvidenceList evidence={[]} status="disabled" />);
    expect(screen.getByText(/RAG Disabled by Config/i)).toBeInTheDocument();
  });
});
