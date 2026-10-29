import React, { createContext, useContext, useState, ReactNode } from "react";
import { AnalyzeRequest, AnalyzeResponse } from "../types/api";
import { analyzeEmail, ApiError } from "../services/api";

interface AnalysisContextType {
  lastPayload: AnalyzeRequest | null;
  result: AnalyzeResponse | null;
  isLoading: boolean;
  errorMessage: string | null;
  handleAnalyze: (payload: AnalyzeRequest) => Promise<void>;
  handleReset: () => void;
  setResultManually: (res: AnalyzeResponse | null) => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export const AnalysisProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [lastPayload, setLastPayload] = useState<AnalyzeRequest | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleAnalyze = async (payload: AnalyzeRequest) => {
    setIsLoading(true);
    setErrorMessage(null);
    setLastPayload(payload);

    try {
      const data = await analyzeEmail(payload);
      setResult(data);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("An unexpected error occurred while communicating with the analysis service.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setLastPayload(null);
    setErrorMessage(null);
  };

  return (
    <AnalysisContext.Provider
      value={{
        lastPayload,
        result,
        isLoading,
        errorMessage,
        handleAnalyze,
        handleReset,
        setResultManually: setResult,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = (): AnalysisContextType => {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error("useAnalysis must be used within an AnalysisProvider");
  }
  return context;
};

