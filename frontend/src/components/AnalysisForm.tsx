import React, { useState } from "react";
import { Send, RotateCcw, Loader2 } from "lucide-react";
import { AnalyzeRequest } from "../types/api";

interface AnalysisFormProps {
  onSubmit: (payload: AnalyzeRequest) => Promise<void>;
  isLoading: boolean;
  onReset: () => void;
  hasResult: boolean;
}

const PHISHING_SAMPLE: AnalyzeRequest = {
  subject: "URGENT: Unauthorized access detected on your corporate account",
  text: "Dear Employee,\n\nOur automated security monitors detected multiple failed login attempts from an unrecognized IP address (45.33.32.156). Your corporate single sign-on access will be terminated within 2 hours unless verified immediately.\n\nPlease authenticate your identity at our secure authentication portal:\nhttp://192.168.1.100:8080/auth/login?session=verify-now\n\nFailure to comply will result in administrative account lockout.\n\nIT Security Operations Desk",
};

const LEGITIMATE_SAMPLE: AnalyzeRequest = {
  subject: "Q3 Engineering All-Hands Meeting Agenda and Slides",
  text: "Hi Team,\n\nAttached is the agenda for our upcoming quarterly engineering all-hands scheduled for Thursday at 2:00 PM EST. We will review our Phase 8 architecture achievements, infrastructure milestones, and the Phase 9 roadmap.\n\nPlease review the preliminary slides before the session:\nhttps://docs.corp.internal/teams/engineering/q3-slides\n\nBest regards,\nEngineering Management",
};

export const AnalysisForm: React.FC<AnalysisFormProps> = ({
  onSubmit,
  isLoading,
  onReset,
  hasResult,
}) => {
  const [subject, setSubject] = useState("");
  const [text, setText] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) {
      setValidationError("Email body text cannot be empty or whitespace only.");
      return;
    }
    setValidationError(null);
    await onSubmit({
      subject: subject.trim() ? subject.trim() : undefined,
      text: text.trim(),
    });
  };

  const loadSample = (sample: AnalyzeRequest) => {
    setSubject(sample.subject || "");
    setText(sample.text);
    setValidationError(null);
  };

  const handleClear = () => {
    setSubject("");
    setText("");
    setValidationError(null);
    onReset();
  };

  return (
    <div className="card">
      {/* Card header */}
      <div className="card-header">
        <div>
          <p className="text-sm font-semibold text-zinc-100">Analyze Suspicious Email</p>
          <p className="text-xs text-zinc-500 mt-0.5">
            Paste raw email content for multi-model risk inference.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => loadSample(PHISHING_SAMPLE)}
            disabled={isLoading}
            className="text-xs px-3 py-1.5 rounded-md border border-white/[0.07] text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04] transition-colors disabled:opacity-40"
          >
            Phishing sample
          </button>
          <button
            type="button"
            onClick={() => loadSample(LEGITIMATE_SAMPLE)}
            disabled={isLoading}
            className="text-xs px-3 py-1.5 rounded-md border border-white/[0.07] text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04] transition-colors disabled:opacity-40"
          >
            Legitimate sample
          </button>
        </div>
      </div>

      {/* Form body */}
      <form onSubmit={handleSubmit} className="p-5 space-y-4">
        <div>
          <label htmlFor="email-subject" className="label block mb-1.5">
            Subject <span className="normal-case font-normal text-zinc-600">(optional)</span>
          </label>
          <input
            id="email-subject"
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={isLoading}
            placeholder="Email subject line..."
            className="input"
          />
        </div>

        <div>
          <label htmlFor="email-body-content" className="label block mb-1.5">
            Email Body Content
          </label>
          <textarea
            id="email-body-content"
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              if (validationError) setValidationError(null);
            }}
            disabled={isLoading}
            placeholder="Paste the complete email body here..."
            rows={8}
            className="input resize-y min-h-[120px] font-mono text-xs leading-relaxed"
          />
          <div className="mt-1.5 h-4">
            {validationError ? (
              <span className="text-xs text-red-400">{validationError}</span>
            ) : (
              <span className="text-xs text-zinc-600">{text.length.toLocaleString()} chars</span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 pt-1">
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary"
            aria-label={isLoading ? "Analyzing Signals" : "Analyze Email"}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing…
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                Analyze Email
              </>
            )}
          </button>

          {(subject || text || hasResult) && !isLoading && (
            <button
              type="button"
              onClick={handleClear}
              className="btn-ghost"
              aria-label="Clear"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Clear
            </button>
          )}
        </div>
      </form>
    </div>
  );
};
