"use client";

import type { AnalysisState } from "@lexguard/shared";
import { motion } from "framer-motion";
import { Brain, Sparkles, TrendingUp } from "lucide-react";

import { AgentTimeline } from "@/components/analysis/agent-timeline";
import { NegotiationCards } from "@/components/analysis/negotiation-cards";
import { StreamingProgress } from "@/components/analysis/streaming-progress";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn, severityColor } from "@/lib/utils";
import { useAnalysisStore } from "@/stores/analysis-store";

interface InsightsPanelProps {
  analysis: AnalysisState | null;
  isAnalyzing: boolean;
}

export function InsightsPanel({ analysis, isAnalyzing }: InsightsPanelProps) {
  const events = useAnalysisStore((s) => s.events);
  const risk = analysis?.risk;
  const consequences = analysis?.consequences;
  const benchmarks = analysis?.benchmarks;
  const negotiation = analysis?.negotiation;

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border/60 px-4 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-medium">AI insights</h2>
        </div>
      </div>
      <Tabs defaultValue="overview" className="flex flex-1 flex-col overflow-hidden">
        <TabsList className="mx-4 mt-3 grid w-auto grid-cols-4">
          <TabsTrigger value="overview" className="text-xs">
            Overview
          </TabsTrigger>
          <TabsTrigger value="risks" className="text-xs">
            Risks
          </TabsTrigger>
          <TabsTrigger value="negotiate" className="text-xs">
            Negotiate
          </TabsTrigger>
          <TabsTrigger value="activity" className="text-xs">
            Activity
          </TabsTrigger>
        </TabsList>
        <ScrollArea className="flex-1">
          <TabsContent value="overview" className="px-4 pb-4">
            <StreamingProgress analysis={analysis} isAnalyzing={isAnalyzing} />
            {risk?.summary && (
              <motion.div
                className="mt-4 rounded-lg border border-border/60 bg-secondary/20 p-3"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className="mb-2 flex items-center gap-2 text-xs font-medium text-primary">
                  <Brain className="h-3.5 w-3.5" />
                  Executive summary
                </div>
                <p className="text-xs leading-relaxed text-muted-foreground">{risk.summary}</p>
                {risk.overall_severity_score != null && (
                  <p className={cn("mt-2 text-sm font-semibold", severityColor(risk.overall_severity_score))}>
                    Overall risk score: {Math.round(risk.overall_severity_score)}
                  </p>
                )}
              </motion.div>
            )}
            {consequences?.summary && (
              <motion.div className="mt-3 rounded-lg border border-border/60 p-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <p className="text-xs font-medium">Consequence outlook</p>
                <p className="mt-1 text-xs text-muted-foreground">{consequences.summary}</p>
              </motion.div>
            )}
            {benchmarks?.benchmark_summary && (
              <motion.div className="mt-3 rounded-lg border border-border/60 p-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <div className="flex items-center gap-2 text-xs font-medium">
                  <TrendingUp className="h-3.5 w-3.5 text-primary" />
                  Benchmark
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{benchmarks.benchmark_summary}</p>
              </motion.div>
            )}
          </TabsContent>
          <TabsContent value="risks" className="px-4 pb-4">
            <div className="space-y-2">
              {risk?.findings.slice(0, 12).map((f, i) => (
                <motion.div
                  key={f.finding_id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="rounded-lg border border-border/60 p-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-medium">{f.clause_title}</p>
                    <span className={cn("text-xs font-bold tabular-nums", severityColor(f.severity_score))}>
                      {Math.round(f.severity_score)}
                    </span>
                  </div>
                  <Badge variant="risk" className="mt-2 text-[10px]">
                    {f.flag.replace(/_/g, " ")}
                  </Badge>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                    {f.plain_language_explanation}
                  </p>
                </motion.div>
              ))}
              {!risk?.findings.length && (
                <p className="py-6 text-center text-xs text-muted-foreground">Risk findings will appear here</p>
              )}
            </div>
          </TabsContent>
          <TabsContent value="negotiate" className="px-4 pb-4">
            <NegotiationCards
              recommendations={negotiation?.recommendations ?? []}
              summary={negotiation?.summary}
              leverage={negotiation?.overall_leverage}
            />
          </TabsContent>
          <TabsContent value="activity" className="h-[320px] px-0 pb-0">
            <AgentTimeline events={events} />
          </TabsContent>
        </ScrollArea>
      </Tabs>
    </div>
  );
}
