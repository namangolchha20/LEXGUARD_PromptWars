"use client";

import type { AgentName, AgentRunState, AnalysisState } from "@lexguard/shared";
import { motion } from "framer-motion";
import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";

import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

const AGENT_LABELS: Record<AgentName, string> = {
  ingestion: "Document ingestion",
  extraction: "Clause extraction",
  risk: "Risk analysis",
  simulation: "Consequence simulation",
  benchmark: "Benchmark comparison",
  negotiation: "Negotiation strategy",
};

const ORDER: AgentName[] = [
  "ingestion",
  "extraction",
  "risk",
  "benchmark",
  "simulation",
  "negotiation",
];

interface StreamingProgressProps {
  analysis: AnalysisState | null;
  isAnalyzing: boolean;
}

function AgentIcon({ status }: { status: AgentRunState["status"] }) {
  if (status === "completed") return <CheckCircle2 className="h-4 w-4 text-risk-low" />;
  if (status === "failed") return <XCircle className="h-4 w-4 text-risk-critical" />;
  if (status === "running" || status === "retrying")
    return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
  return <Circle className="h-4 w-4 text-muted-foreground/40" />;
}

export function StreamingProgress({ analysis, isAnalyzing }: StreamingProgressProps) {
  const progress = analysis?.overall_progress ?? 0;
  const agents = analysis?.agents ?? {};

  return (
    <div className="space-y-4">
      <div>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">Pipeline progress</span>
          <span className="text-xs tabular-nums text-foreground">{Math.round(progress)}%</span>
        </div>
        <Progress value={progress} className="h-1.5" />
      </div>
      <div className="space-y-2">
        {ORDER.map((name, i) => {
          const agent = agents[name];
          if (!agent && !isAnalyzing) return null;
          const status = agent?.status ?? "pending";
          return (
            <motion.div
              key={name}
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04 }}
              className={cn(
                "flex items-center gap-3 rounded-lg px-2 py-1.5 text-sm",
                status === "running" && "bg-primary/5",
              )}
            >
              <AgentIcon status={status} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium">{AGENT_LABELS[name]}</p>
                {agent?.message && (
                  <p className="truncate text-[10px] text-muted-foreground">{agent.message}</p>
                )}
              </div>
              {agent && status === "running" && (
                <span className="text-[10px] tabular-nums text-muted-foreground">
                  {Math.round(agent.progress)}%
                </span>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
