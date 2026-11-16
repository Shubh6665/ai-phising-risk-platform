import React from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";
import { AlertTriangle } from "lucide-react";

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
    { name: "Random Forest", value: +(mlProbability * 100).toFixed(1) },
    { name: "DistilBERT",    value: +(nlpProbability * 100).toFixed(1) },
  ];

  return (
    <div className="card animate-fade-up delay-50">
      <div className="card-header">
        <div>
          <p className="text-sm font-semibold text-zinc-100">Model Breakdown</p>
          <p className="text-xs text-zinc-500 mt-0.5">Random Forest · DistilBERT · Rule signals</p>
        </div>
        {isDivergent && (
          <span className="inline-flex items-center gap-1.5 text-xs text-amber-400 font-medium">
            <AlertTriangle className="w-3.5 h-3.5" />
            Δ {(divergence * 100).toFixed(0)}% divergence
          </span>
        )}
      </div>

      <div className="p-5 space-y-5">
        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "Random Forest", value: `${(mlProbability * 100).toFixed(1)}%`, sub: "Weight 0.40" },
            { label: "DistilBERT",    value: `${(nlpProbability * 100).toFixed(1)}%`, sub: "Weight 0.60" },
            { label: "Rule Bonus",    value: `+${ruleBonus.toFixed(1)}`, sub: "Deterministic" },
          ].map((s) => (
            <div key={s.label} className="p-3 rounded-lg bg-surface-raised border border-white/[0.05]">
              <p className="label mb-1.5">{s.label}</p>
              <p className="text-lg font-bold text-zinc-100 font-mono tracking-tight">{s.value}</p>
              <p className="text-[10px] text-zinc-600 mt-0.5">{s.sub}</p>
            </div>
          ))}
        </div>

        {/* Chart */}
        <div className="h-28">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 8 }} barCategoryGap={10}>
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fontSize: 10, fill: "#52525b" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `${v}%`}
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 11, fill: "#a1a1aa" }}
                axisLine={false}
                tickLine={false}
                width={95}
              />
              <Tooltip
                contentStyle={{
                  background: "#111113",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: 8,
                  fontSize: 12,
                  color: "#e4e4e7",
                }}
                itemStyle={{ color: "#a1a1aa" }}
                formatter={(v: number) => [`${v}%`, "P(phishing)"]}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={18}>
                {chartData.map((_, i) => (
                  <Cell key={i} fill={i === 0 ? "#52525b" : "#a1a1aa"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
