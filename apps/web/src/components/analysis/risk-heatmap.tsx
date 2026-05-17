"use client";

import type { CategoryScore, RiskCategory } from "@lexguard/shared";
import { motion } from "framer-motion";

import { cn, severityBg, severityColor } from "@/lib/utils";

const CATEGORY_LABELS: Record<RiskCategory, string> = {
  employment_risk: "Employment",
  privacy_risk: "Privacy",
  financial_risk: "Financial",
  ip_risk: "IP",
  arbitration_risk: "Arbitration",
  compliance_risk: "Compliance",
};

interface RiskHeatmapProps {
  scores: CategoryScore[];
  overallScore?: number;
}

export function RiskHeatmap({ scores, overallScore }: RiskHeatmapProps) {
  const sorted = [...scores].sort((a, b) => b.score - a.score);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Risk heatmap
        </h3>
        {overallScore != null && (
          <span className={cn("text-sm font-semibold tabular-nums", severityColor(overallScore))}>
            {Math.round(overallScore)}
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {sorted.map((item, i) => (
          <motion.div
            key={item.category}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.05 }}
            className={cn("rounded-lg border p-3 transition-colors", severityBg(item.score))}
          >
            <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
              {CATEGORY_LABELS[item.category]}
            </p>
            <p className={cn("mt-1 text-lg font-bold tabular-nums", severityColor(item.score))}>
              {Math.round(item.score)}
            </p>
            <p className="text-[10px] text-muted-foreground">{item.finding_count} findings</p>
          </motion.div>
        ))}
      </div>
      {sorted.length === 0 && (
        <p className="py-4 text-center text-xs text-muted-foreground">Risk scores appear after analysis</p>
      )}
    </div>
  );
}
