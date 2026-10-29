import React from "react";
import { Cpu, Binary, PlusCircle, Scale, AlertTriangle } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";

interface ModelBreakdownProps {
  mlProbability: number;
  nlpProbability: number;
  ruleBonus: number;
}

export const ModelBreakdown: React.FC<ModelBreakdownProps> = ({
  mlProbability,
  nlpProbability,
  ruleBonus,
}) => {
  const divergence = Math.abs(mlProbability - nlpProbability);
  const isDivergent = divergence > 0.30;

  const chartData = [
    {
      name: "Random Forest",
      probability: Number((mlProbability * 100).toFixed(1)),
      color: "#0284c7", // sky-600
    },
    {
      name: "DistilBERT",
      probability: Number((nlpProbability * 100).toFixed(1)),
      color: "#7c3aed", // violet-600
    },
  ];

  return (
    <div className="bg-[#111726] border border-slate-800 rounded-xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-800 gap-2">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>Ensemble Model Breakdown</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Phase 5 hybrid weighting: Classical handcrafted features (40%) + transformer token semantics (60%).
          </p>
        </div>

        {isDivergent && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-950/60 border border-amber-800/80 text-amber-300 text-xs font-mono">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>High Disagreement Detected</span>
          </div>
        )}
      </div>

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
        {/* Card 1: Random Forest */}
        <div className="bg-[#0b0f19] border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-cyan-400 flex items-center gap-1.5 font-medium">
              <Binary className="w-3.5 h-3.5" />
              <span>Classical ML</span>
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Weight 0.40</span>
          </div>
          <div className="my-3">
            <span className="text-2xl font-bold text-white font-mono">
              {(mlProbability * 100).toFixed(1)}%
            </span>
            <span className="text-xs text-slate-500 font-mono ml-2">
              (p = {mlProbability.toFixed(4)})
            </span>
          </div>
          <div className="text-xs text-slate-400 border-t border-slate-900 pt-2.5">
            Random Forest classifier trained on 19 URL and text lexical features.
          </div>
        </div>

        {/* Card 2: DistilBERT NLP */}
        <div className="bg-[#0b0f19] border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-violet-400 flex items-center gap-1.5 font-medium">
              <Cpu className="w-3.5 h-3.5" />
              <span>Transformer NLP</span>
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Weight 0.60</span>
          </div>
          <div className="my-3">
            <span className="text-2xl font-bold text-white font-mono">
              {(nlpProbability * 100).toFixed(1)}%
            </span>
            <span className="text-xs text-slate-500 font-mono ml-2">
              (p = {nlpProbability.toFixed(4)})
            </span>
          </div>
          <div className="text-xs text-slate-400 border-t border-slate-900 pt-2.5">
            Fine-tuned DistilBERT analyzing contextual semantics and intent patterns.
          </div>
        </div>

        {/* Card 3: Rule Bonus & Divergence */}
        <div className="bg-[#0b0f19] border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-emerald-400 flex items-center gap-1.5 font-medium">
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Rule Bonus</span>
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Heuristics</span>
          </div>
          <div className="my-3">
            <span className="text-2xl font-bold text-white font-mono">
              +{ruleBonus.toFixed(1)}
            </span>
            <span className="text-xs text-slate-500 font-mono ml-2">
              pts bonus
            </span>
          </div>
          <div className="text-xs text-slate-400 flex items-center justify-between border-t border-slate-900 pt-2.5">
            <span>Model Divergence:</span>
            <span className={`font-mono font-semibold ${isDivergent ? "text-amber-400" : "text-slate-300"}`}>
              Δ {(divergence * 100).toFixed(1)}% {isDivergent && "(High)"}
            </span>
          </div>
        </div>
      </div>

      {/* Visual Comparative Chart */}
      <div className="mt-5 pt-4 border-t border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
            <Scale className="w-3.5 h-3.5 text-slate-400" />
            <span>Model Probability Distribution (0–100%)</span>
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            P(phishing) comparison
          </span>
        </div>
        <div className="h-28 w-full bg-[#0b0f19] rounded-lg p-2 border border-slate-800/80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
            >
              <XAxis type="number" domain={[0, 100]} stroke="#475569" tick={{ fontSize: 10, fill: "#64748b" }} />
              <YAxis dataKey="name" type="category" stroke="#94a3b8" tick={{ fontSize: 11, fill: "#cbd5e1" }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#0b0f19", borderColor: "#334155", borderRadius: "8px", fontSize: "12px" }}
                formatter={(val: number) => [`${val}%`, "P(Phishing)"]}
              />
              <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
