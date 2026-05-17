"use client";

import { motion } from "framer-motion";
import { RotateCcw, Shield } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAnalysisStore } from "@/stores/analysis-store";

export function AppHeader() {
  const fileName = useAnalysisStore((s) => s.fileName);
  const reset = useAnalysisStore((s) => s.reset);

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/60 px-6">
      <motion.div
        className="flex items-center gap-3"
        initial={{ opacity: 0, x: -8 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <motion.div
          className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15"
          whileHover={{ scale: 1.05 }}
        >
          <Shield className="h-4 w-4 text-primary" />
        </motion.div>
        <motion.div>
          <h1 className="text-sm font-semibold tracking-tight">LEXGUARD</h1>
          {fileName && (
            <p className="max-w-[280px] truncate text-xs text-muted-foreground">{fileName}</p>
          )}
        </motion.div>
      </motion.div>
      {fileName && (
        <Button variant="ghost" size="sm" className="gap-2 text-muted-foreground" onClick={reset}>
          <RotateCcw className="h-3.5 w-3.5" />
          New document
        </Button>
      )}
    </header>
  );
}
