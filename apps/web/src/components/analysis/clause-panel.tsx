"use client";

import type { ExtractedClause, RiskFinding } from "@lexguard/shared";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, ChevronRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn, severityColor } from "@/lib/utils";
import { useAnalysisStore } from "@/stores/analysis-store";

interface ClausePanelProps {
  clauses: ExtractedClause[];
  findings: RiskFinding[];
}

export function ClausePanel({ clauses, findings }: ClausePanelProps) {
  const selectedId = useAnalysisStore((s) => s.selectedClauseId);
  const setSelected = useAnalysisStore((s) => s.setSelectedClause);

  const findingByClause = new Map(findings.map((f) => [f.clause_id, f]));
  const maxSeverity = (clauseId: string) => {
    const related = findings.filter((f) => f.clause_id === clauseId);
    return related.length ? Math.max(...related.map((f) => f.severity_score)) : 0;
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border/60 px-4 py-3">
        <h2 className="text-sm font-medium">Clauses</h2>
        <p className="text-xs text-muted-foreground">{clauses.length} extracted · click to inspect</p>
      </div>
      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          <AnimatePresence mode="popLayout">
            {clauses.map((clause, i) => {
              const severity = maxSeverity(clause.clause_id);
              const topFinding = findingByClause.get(clause.clause_id);
              const isSelected = selectedId === clause.clause_id;

              return (
                <motion.button
                  key={clause.clause_id}
                  type="button"
                  layout
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                  onClick={() => setSelected(isSelected ? null : clause.clause_id)}
                  className={cn(
                    "w-full rounded-lg border p-3 text-left transition-colors",
                    isSelected
                      ? "border-primary/50 bg-primary/10"
                      : "border-transparent hover:border-border hover:bg-secondary/50",
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="shrink-0 text-[10px]">
                          {clause.clause_type.replace(/_/g, " ")}
                        </Badge>
                        {severity > 0 && (
                          <span className={cn("text-xs font-semibold tabular-nums", severityColor(severity))}>
                            {Math.round(severity)}
                          </span>
                        )}
                      </div>
                      <p className="mt-1 truncate text-sm font-medium">{clause.title}</p>
                    </div>
                    <ChevronRight
                      className={cn(
                        "h-4 w-4 shrink-0 text-muted-foreground transition-transform",
                        isSelected && "rotate-90 text-primary",
                      )}
                    />
                  </div>
                  <AnimatePresence>
                    {isSelected && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <p className="mt-2 text-xs leading-relaxed text-muted-foreground line-clamp-4">
                          {clause.text}
                        </p>
                        {topFinding && (
                          <div className="mt-2 flex items-start gap-2 rounded-md bg-risk-high/10 p-2">
                            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-risk-high" />
                            <p className="text-xs text-foreground/90">{topFinding.plain_language_explanation}</p>
                          </div>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.button>
              );
            })}
          </AnimatePresence>
          {clauses.length === 0 && (
            <p className="py-8 text-center text-xs text-muted-foreground">Clauses appear after extraction</p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
