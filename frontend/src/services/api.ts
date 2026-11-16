import { AnalyzeRequest, AnalyzeResponse, ErrorResponse } from "../types/api";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");

export class ApiError extends Error {
  status: number;
  data?: ErrorResponse;

  constructor(message: string, status: number, data?: ErrorResponse) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

/**
 * Submit an email for analysis to the FastAPI backend.
 *
 * @param payload - Subject and body text to analyze
 * @returns Parsed AnalyzeResponse
 */
export async function analyzeEmail(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  const url = `${API_BASE_URL}/api/v1/analyze`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let errorData: ErrorResponse | undefined;
      try {
        errorData = await response.json();
      } catch {
        // Response was not JSON
      }

      const message = errorData?.detail || `API request failed with status ${response.status}`;
      throw new ApiError(message, response.status, errorData);
    }

    const data: AnalyzeResponse = await response.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const rawMessage = err instanceof Error ? err.message : "";
    const isConnectionError =
      !rawMessage ||
      rawMessage === "Failed to fetch" ||
      rawMessage.toLowerCase().includes("could not connect") ||
      rawMessage.toLowerCase().includes("access control") ||
      rawMessage.toLowerCase().includes("networkerror");

    const message = isConnectionError
      ? "Could not connect to the analysis backend server. Please verify the FastAPI backend is running on http://127.0.0.1:8000."
      : rawMessage || "Network error: Unable to contact analysis backend.";
    throw new ApiError(message, 0);
  }
}

