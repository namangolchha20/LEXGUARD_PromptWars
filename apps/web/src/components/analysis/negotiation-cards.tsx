"use client";

import type { NegotiationRecommendation } from "@lexguard/shared";
import { motion } from "framer-motion";
import { ArrowRight, MessageSquare } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { priorityColor } from "@/lib/utils";

interface NegotiationCardsProps {
  recommendations: NegotiationRecommendation[];
  summary?: string;
  leverage?: string;
}

export function NegotiationCards({ recommendations, summary, leverage }: NegotiationCardsProps) {
  const sorted = [...recommendations].sort((a, b) => {
    const order = { critical: 0, high: 1, medium: 2, low: 3 };
    return order[a.priority] - order[b.priority];
  });

  return (
    <motion.div className="space-y-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      {(summary || leverage) && (
        <div className="rounded-lg border border-border/60 bg-secondary/30 p-3">
          <div className="flex items-center gap-2 text-xs font-medium text-primary">
            <MessageSquare className="h-3.5 w-3.5" />
            Negotiation brief
          </div>
          {summary && <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{summary}</p>}
          {leverage && (
            <p className="mt-2 text-xs">
              <span className="text-muted-foreground">Leverage: </span>
              <span className="font-medium">{leverage}</span>
            </p>
          )}
        </div>
      )}
      {sorted.map((rec, i) => (
        <motion.div
          key={`${rec.topic}-${i}`}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.06 }}
        >
          <Card className="border-border/60 bg-card/60">
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-sm leading-snug">{rec.topic}</CardTitle>
                <Badge className={priorityColor(rec.priority)}>{rec.priority}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <div className="grid gap-2 text-xs">
                <div className="rounded-md bg-risk-high/5 p-2">
                  <span className="text-[10px] uppercase text-muted-foreground">Current</span>
                  <p className="mt-0.5">{rec.current_term}</p>
                </div>
                <div className="flex justify-center">
                  <ArrowRight className="h-4 w-4 text-primary" />
                </div>
                <div className="rounded-md bg-risk-low/5 p-2">
                  <span className="text-[10px] uppercase text-muted-foreground">Suggested</span>
                  <p className="mt-0.5">{rec.suggested_term}</p>
                </div>
              </div>
              <p className="text-xs leading-relaxed text-muted-foreground">{rec.rationale}</p>
            </CardContent>
          </Card>
        </motion.div>
      ))}
      {sorted.length === 0 && (
        <p className="py-4 text-center text-xs text-muted-foreground">
          Negotiation suggestions appear after the pipeline completes
        </p>
      )}
    </motion.div>
  );
}
