import type { AnalysisState, OrchestratorEvent, PipelineRunResponse } from "@lexguard/shared";
import { create } from "zustand";

function initialAnalysisFromRun(run: PipelineRunResponse): AnalysisState {
  return {
    document_id: run.document_id,
    run_id: run.run_id,
    status: run.status,
    agents: {},
    overall_progress: 0,
    errors: {},
  };
}

interface AnalysisStore {
  documentId: string | null;
  fileName: string | null;
  fileUrl: string | null;
  analysis: AnalysisState | null;
  events: OrchestratorEvent[];
  selectedClauseId: string | null;
  isAnalyzing: boolean;
  error: string | null;

  setDocument: (id: string, fileName: string, fileUrl: string, run?: PipelineRunResponse) => void;
  setAnalysis: (analysis: AnalysisState) => void;
  addEvent: (event: OrchestratorEvent) => void;
  setSelectedClause: (id: string | null) => void;
  setAnalyzing: (v: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useAnalysisStore = create<AnalysisStore>((set) => ({
  documentId: null,
  fileName: null,
  fileUrl: null,
  analysis: null,
  events: [],
  selectedClauseId: null,
  isAnalyzing: false,
  error: null,

  setDocument: (id, fileName, fileUrl, run) =>
    set({
      documentId: id,
      fileName,
      fileUrl,
      analysis: run ? initialAnalysisFromRun(run) : null,
      events: [],
      error: null,
    }),
  setAnalysis: (analysis) => set({ analysis }),
  addEvent: (event) => set((s) => ({ events: [...s.events, event] })),
  setSelectedClause: (id) => set({ selectedClauseId: id }),
  setAnalyzing: (isAnalyzing) => set({ isAnalyzing }),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      documentId: null,
      fileName: null,
      fileUrl: null,
      analysis: null,
      events: [],
      selectedClauseId: null,
      isAnalyzing: false,
      error: null,
    }),
}));
