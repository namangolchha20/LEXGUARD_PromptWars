"use client";

import type { AgentName, OrchestratorEvent } from "@lexguard/shared";
import { motion } from "framer-motion";
import { Activity } from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

const AGENT_LABELS: Partial<Record<AgentName, string>> = {
  ingestion: "Ingestion",
  extraction: "Extraction",
  risk: "Risk",
  benchmark: "Benchmark",
  simulation: "Simulation",
  negotiation: "Negotiation",
};

interface AgentTimelineProps {
  events: OrchestratorEvent[];
}

function eventColor(type: OrchestratorEvent["type"]): string {
  if (type === "agent_failed" || type === "run_failed") return "bg-risk-critical";
  if (type === "run_completed" || type === "agent_completed") return "bg-risk-low";
  if (type === "agent_started" || type === "agent_progress") return "bg-primary";
  return "bg-muted-foreground";
}

export function AgentTimeline({ events }: AgentTimelineProps) {
  const recent = [...events].reverse().slice(0, 40);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-border/60 px-4 py-3">
        <Activity className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-medium">Agent activity</h3>
      </div>
      <ScrollArea className="flex-1">
        <motion.div className="space-y-0 p-3">
          {recent.length === 0 && (
            <p className="py-6 text-center text-xs text-muted-foreground">
              Live events stream here during analysis
            </p>
          )}
          {recent.map((event, i) => (
            <motion.div
              key={`${event.timestamp}-${i}`}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              className="relative flex gap-3 pb-4 last:pb-0"
            >
              <div className="flex flex-col items-center">
                <div className={cn("h-2 w-2 shrink-0 rounded-full", eventColor(event.type))} />
                {i < recent.length - 1 && <div className="mt-1 w-px flex-1 bg-border" />}
              </div>
              <div className="min-w-0 flex-1 pt-0.5">
                <div className="flex items-center gap-2">
                  {event.agent && (
                    <span className="text-[10px] font-medium uppercase text-primary">
                      {AGENT_LABELS[event.agent] ?? event.agent}
                    </span>
                  )}
                  <span className="text-[10px] text-muted-foreground">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="mt-0.5 text-xs leading-relaxed text-foreground/90">{event.message}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </ScrollArea>
    </div>
  );
}
