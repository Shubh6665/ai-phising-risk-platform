import React, { useState } from "react";
import { Send, RefreshCw, AlertCircle, FileText, Sparkles } from "lucide-react";
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
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            Analyze Suspicious Email
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Submit raw header metadata and message body for real-time model inference and investigation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => loadSample(PHISHING_SAMPLE)}
            disabled={isLoading}
            className="text-xs bg-red-950/60 hover:bg-red-900/60 text-red-300 border border-red-800/40 px-2.5 py-1.5 rounded-lg transition font-medium flex items-center gap-1.5 disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5 text-red-400" />
            Phishing Sample
          </button>
          <button
            type="button"
            onClick={() => loadSample(LEGITIMATE_SAMPLE)}
            disabled={isLoading}
            className="text-xs bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 border border-emerald-800/40 px-2.5 py-1.5 rounded-lg transition font-medium flex items-center gap-1.5 disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            Legitimate Sample
          </button>
          {(subject || text || hasResult) && (
            <button
              type="button"
              onClick={handleClear}
              disabled={isLoading}
              className="text-xs text-slate-400 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-slate-800 transition disabled:opacity-50"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-5 space-y-4">
        <div>
          <label htmlFor="email-subject" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Email Subject <span className="text-slate-500 font-normal lowercase">(optional)</span>
          </label>
          <input
            id="email-subject"
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={isLoading}
            placeholder="e.g. URGENT: Verify your payroll credentials"
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition disabled:opacity-60"
          />
        </div>

        <div>
          <label htmlFor="email-body" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Email Body Content <span className="text-cyan-400">*</span>
          </label>
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
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition font-mono disabled:opacity-60 leading-relaxed"
          />
          {validationError && (
            <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1.5" role="alert">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {validationError}
            </p>
          )}
        </div>

        <div className="pt-2 flex items-center justify-between">
          <p className="text-xs text-slate-500 italic">
            Privacy safeguard: Raw email text is never persisted or transmitted to external LLMs.
          </p>

          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center gap-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-sm px-6 py-2.5 rounded-xl shadow-lg shadow-cyan-900/30 transition transform active:scale-98 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Analyzing Signals...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Analyze Email
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

