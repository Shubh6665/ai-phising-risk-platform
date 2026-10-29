import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { InvestigationFindings } from "../src/components/InvestigationFindings";
import { URLObservation } from "../src/types/api";

const MOCK_URLS: URLObservation[] = [
  {
    url: "http://192.168.1.100:8080/auth/login?token=secret123",
    scheme: "http",
    hostname: "192.168.1.100",
    port: 8080,
    is_ip_literal: true,
    has_userinfo: false,
    has_punycode: false,
    has_unusual_port: true,
    subdomain_depth: 0,
    indicator_count: 2,
    suspicious_indicators: [
      "IP address literal hostname instead of FQDN",
      "Non-standard web port (8080)",
    ],
  },
];

describe("InvestigationFindings Component", () => {
  it("renders structural URL observations and detected anomalies", () => {
    render(<InvestigationFindings urls={MOCK_URLS} />);

    expect(screen.getByText(/1 URL Extracted/i)).toBeInTheDocument();
    expect(screen.getByText("192.168.1.100")).toBeInTheDocument();
    expect(screen.getByText(/Port 8080/i)).toBeInTheDocument();
    expect(screen.getByText(/2 Anomalies/i)).toBeInTheDocument();
    expect(screen.getByText(/• IP address literal hostname instead of FQDN/i)).toBeInTheDocument();
    expect(screen.getByText(/• Non-standard web port \(8080\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Operational Context:/i)).toBeInTheDocument();
  });

  it("renders empty state when no URLs were detected", () => {
    render(<InvestigationFindings urls={[]} />);
    expect(screen.getByText(/0 URLs Extracted/i)).toBeInTheDocument();
    expect(screen.getByText(/No hyperlinks or URLs were detected/i)).toBeInTheDocument();
  });

  it("renders URLs strictly as non-navigable text", () => {
    render(<InvestigationFindings urls={MOCK_URLS} />);
    // Ensure no <a href="http://192.168.1.100..."> link exists in DOM
    const links = screen.queryAllByRole("link");
    expect(links.length).toBe(0);
  });
});

