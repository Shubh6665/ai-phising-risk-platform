/**
 * API TypeScript contracts corresponding to backend Pydantic schemas
 * (src/api/schemas.py and src/agent/schemas.py).
 */

export interface AnalyzeRequest {
  text: string;
  subject?: string | null;
}

export interface SecurityEvidenceItem {
  chunk_id: string;
  content: string;
  similarity: number;
  document_name: string;
  document_title?: string | null;
  heading?: string | null;
  document_type: string;
  source_attribution: string;
  is_mock: boolean;
}

export interface URLObservation {
  url: string;
  scheme: string;
  hostname?: string | null;
  port?: number | null;
  path?: string;
  query?: string;
  is_ip_literal: boolean;
  ip_type?: string | null;
  has_userinfo: boolean;
  has_punycode: boolean;
  has_unusual_port: boolean;
  subdomain_depth: number;
  url_length?: number;
  suspicious_indicators: string[];
  indicator_count: number;
  notes?: string;
}

export interface InvestigationExplanation {
  summary: string;
  key_findings: string[];
  risk_explanation: string;
  recommended_actions: string[];
  limitations: string[];
  evidence_references: string[];
  provider_used?: string | null;
  generation_status: "completed" | "fallback" | "degraded" | "disabled" | "error";
}

export interface AnalyzeResponse {
  request_id: string;
  risk_score: number;
  classification: "Low" | "Medium" | "High" | "Critical";
  ml_probability: number;
  nlp_probability: number;
  rule_bonus: number;
  analysis_id?: string | null;
  evidence: SecurityEvidenceItem[];
  evidence_status: "retrieved" | "empty" | "unavailable" | "disabled";
  requires_escalation: boolean;
  escalation_reason?: string | null;
  url_analysis: URLObservation[];
  explanation?: InvestigationExplanation | null;
}

export interface ErrorResponse {
  request_id?: string | null;
  error: string;
  detail: string;
}

