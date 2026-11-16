import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { InvestigationFindings } from "../src/components/InvestigationFindings";
import { URLObservation } from "../src/types/api";

const MOCK_URLS: URLObservation[] = [
  {
    url: "http://192.168.1.100:8080/auth/login",
    scheme: "http",
    hostname: "192.168.1.100",
    port: 8080,
    is_ip_literal: true,
    has_unusual_port: true,
    has_userinfo: false,
    has_punycode: false,
    subdomain_depth: 0,
    indicator_count: 2,
    suspicious_indicators: ["IP address literal hostname", "Non-standard web port"],
  },
];

describe("InvestigationFindings Component", () => {
  it("renders URL as inert text with anomaly indicators", () => {
    render(<InvestigationFindings urls={MOCK_URLS} />);

    expect(screen.getByText("http://192.168.1.100:8080/auth/login")).toBeInTheDocument();
    expect(screen.getByText(/IP address literal hostname/i)).toBeInTheDocument();
    expect(screen.getByText(/Non-standard web port/i)).toBeInTheDocument();
  });

  it("renders URLs strictly as non-navigable text — no anchor links", () => {
    render(<InvestigationFindings urls={MOCK_URLS} />);
    const links = screen.queryAllByRole("link");
    expect(links.length).toBe(0);
  });

  it("renders empty state when no URLs detected", () => {
    render(<InvestigationFindings urls={[]} />);
    expect(screen.getByText(/No URLs detected/i)).toBeInTheDocument();
  });
});
