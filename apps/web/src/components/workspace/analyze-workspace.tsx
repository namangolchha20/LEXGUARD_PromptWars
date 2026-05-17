"use client";

import type { DocumentSection, PipelineRunResponse } from "@lexguard/shared";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle } from "lucide-react";
import dynamic from "next/dynamic";
import { useCallback, useMemo } from "react";

import { ClausePanel } from "@/components/analysis/clause-panel";
import { InsightsPanel } from "@/components/analysis/insights-panel";
import { RiskHeatmap } from "@/components/analysis/risk-heatmap";
import { AppHeader } from "@/components/layout/app-header";
import { Dropzone } from "@/components/upload/dropzone";
import { useOrchestratorStream } from "@/hooks/use-orchestrator-stream";
import { useAnalysisStore } from "@/stores/analysis-store";

const PdfViewer = dynamic(
  () => import("@/components/pdf/pdf-viewer").then((mod) => mod.PdfViewer),
  {
    ssr: false,
    loading: () => (
      <motion.div className="glass flex flex-1 items-center justify-center rounded-xl">
        <motion.div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </motion.div>
    ),
  },
);

function findClausePage(
  sections: DocumentSection[],
  title: string,
  text: string,
): number | null {
  const snippet = text.slice(0, 120).trim();
  for (const section of sections) {
    if (
      section.page != null &&
      (section.title.toLowerCase() === title.toLowerCase() ||
        section.content.includes(snippet) ||
        section.content.toLowerCase().includes(title.toLowerCase()))
    ) {
      return section.page;
    }
    const nested = findClausePage(section.subsections, title, text);
    if (nested != null) return nested;
  }
  return null;
}

export function AnalyzeWorkspace() {
  const documentId = useAnalysisStore((s) => s.documentId);
  const fileUrl = useAnalysisStore((s) => s.fileUrl);
  const fileName = useAnalysisStore((s) => s.fileName);
  const analysis = useAnalysisStore((s) => s.analysis);
  const isAnalyzing = useAnalysisStore((s) => s.isAnalyzing);
  const error = useAnalysisStore((s) => s.error);
  const setDocument = useAnalysisStore((s) => s.setDocument);
  const setAnalyzing = useAnalysisStore((s) => s.setAnalyzing);
  const selectedClauseId = useAnalysisStore((s) => s.selectedClauseId);

  useOrchestratorStream(documentId, Boolean(documentId));

  const handleUploadSuccess = useCallback(
    (run: PipelineRunResponse, name: string, url: string) => {
      setDocument(run.document_id, name, url, run);
      setAnalyzing(true);
    },
    [setDocument, setAnalyzing],
  );

  const clauses = analysis?.clauses?.clauses ?? [];
  const findings = analysis?.risk?.findings ?? [];
  const categoryScores = analysis?.risk?.category_scores ?? [];
  const sections = analysis?.parsed_document?.sections ?? [];

  const jumpToPage = useMemo(() => {
    if (!selectedClauseId) return null;
    const clause = clauses.find((c) => c.clause_id === selectedClauseId);
    if (!clause) return null;
    return findClausePage(sections, clause.title, clause.text);
  }, [selectedClauseId, clauses, sections]);

  return (
    <div className="gradient-mesh flex h-screen flex-col overflow-hidden">
      <AppHeader />
      <AnimatePresence mode="wait">
        {!documentId ? (
          <motion.main
            key="upload"
            className="flex flex-1 flex-col items-center justify-center px-6 pb-12"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div className="mb-10 max-w-lg text-center" initial={{ y: 20 }} animate={{ y: 0 }}>
              <h2 className="text-3xl font-semibold tracking-tight">
                Contract intelligence,{" "}
                <span className="bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
                  explained
                </span>
              </h2>
              <p className="mt-3 text-sm text-muted-foreground">
                Upload a contract to extract clauses, score risks, simulate consequences, and get
                negotiation recommendations — streamed in real time.
              </p>
            </motion.div>
            <div className="w-full max-w-xl">
              <Dropzone onSuccess={handleUploadSuccess} />
              {error && (
                <motion.div
                  className="mt-4 flex items-center gap-2 rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-4 py-3 text-sm text-risk-critical"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {error}
                </motion.div>
              )}
            </div>
          </motion.main>
        ) : (
          <motion.main
            key="workspace"
            className="grid min-h-0 flex-1 grid-cols-1 gap-3 p-3 lg:grid-cols-12 lg:p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="flex min-h-[40vh] flex-col lg:col-span-5 lg:min-h-0">
              <PdfViewer
                fileUrl={fileUrl}
                fileName={fileName}
                jumpToPage={jumpToPage}
                className="min-h-0 flex-1"
              />
            </div>
            <motion.div className="glass flex min-h-[280px] flex-col overflow-hidden rounded-xl lg:col-span-3 lg:min-h-0">
              <ClausePanel clauses={clauses} findings={findings} />
              <div className="border-t border-border/60 p-4">
                <RiskHeatmap
                  scores={categoryScores}
                  overallScore={analysis?.risk?.overall_severity_score}
                />
              </div>
            </motion.div>
            <div className="glass min-h-[320px] overflow-hidden rounded-xl lg:col-span-4 lg:min-h-0">
              <InsightsPanel analysis={analysis} isAnalyzing={isAnalyzing} />
            </div>
          </motion.main>
        )}
      </AnimatePresence>
    </div>
  );
}
