import React, { useState } from "react";
import { Send, RefreshCw, AlertCircle, Mail, RotateCcw } from "lucide-react";
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
    <div className="bg-[#111726] border border-slate-800 rounded-xl p-6 shadow-sm">
      {/* Top Header & Presets */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-800 gap-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Mail className="w-4 h-4 text-cyan-400" />
            <span>Analyze Suspicious Email</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Submit raw header metadata and message body for real-time model inference and investigation.
          </p>
        </div>

        {/* Sample Loaders */}
        <div className="flex items-center flex-wrap gap-2">
          <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wide mr-1 hidden sm:inline">
            Load Preset:
          </span>
          <button
            type="button"
            onClick={() => loadSample(PHISHING_SAMPLE)}
            disabled={isLoading}
            className="text-xs bg-red-950/40 hover:bg-red-900/50 text-red-300 border border-red-900/50 px-3 py-1.5 rounded-lg transition-colors font-medium disabled:opacity-50"
          >
            Phishing Sample
          </button>
          <button
            type="button"
            onClick={() => loadSample(LEGITIMATE_SAMPLE)}
            disabled={isLoading}
            className="text-xs bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-300 border border-emerald-900/50 px-3 py-1.5 rounded-lg transition-colors font-medium disabled:opacity-50"
          >
            Legitimate Sample
          </button>
          {(subject || text || hasResult) && (
            <button
              type="button"
              onClick={handleClear}
              disabled={isLoading}
              className="text-xs text-slate-400 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-50 flex items-center gap-1"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-5 space-y-4">
        {/* Email Subject Field */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label
              htmlFor="email-subject"
              className="block text-xs font-medium text-slate-300 uppercase tracking-wider"
            >
              Email Subject <span className="text-slate-500 font-normal lowercase">(optional)</span>
            </label>
            <span className="text-[11px] font-mono text-slate-500">{subject.length} chars</span>
          </div>
          <input
            id="email-subject"
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={isLoading}
            placeholder="e.g. URGENT: Verify your payroll credentials"
            className="w-full bg-[#0b0f19] border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors disabled:opacity-60"
          />
        </div>

        {/* Email Body Field */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label
              htmlFor="email-body"
              className="block text-xs font-medium text-slate-300 uppercase tracking-wider"
            >
              Email Body Content <span className="text-cyan-400">*</span>
            </label>
            <span className="text-[11px] font-mono text-slate-500">{text.length} chars</span>
          </div>
          <textarea
            id="email-body"
            rows={7}
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              if (validationError) setValidationError(null);
            }}
            disabled={isLoading}
            placeholder="Paste full raw email body text or headers here..."
            className="w-full bg-[#0b0f19] border border-slate-800 rounded-lg p-3.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors font-mono disabled:opacity-60 leading-relaxed"
          />
          {validationError && (
            <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1.5" role="alert">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{validationError}</span>
            </p>
          )}
        </div>

        {/* Bottom Bar */}
        <div className="pt-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <p className="text-xs text-slate-500">
            Privacy safeguard: Raw email text is never persisted or transmitted to external LLMs.
          </p>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs px-5 py-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Analyzing Signals...</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Analyze Email</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
