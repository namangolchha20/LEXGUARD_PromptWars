"use client";

import type { OrchestratorEvent, WsEnvelope } from "@lexguard/shared";
import { WsMessageType } from "@lexguard/shared";
import { useCallback, useEffect, useRef } from "react";

import { fetchAnalysis, orchestratorWsUrl } from "@/lib/api";
import { useAnalysisStore } from "@/stores/analysis-store";

export function useOrchestratorStream(documentId: string | null, enabled: boolean) {
  const addEvent = useAnalysisStore((s) => s.addEvent);
  const setAnalysis = useAnalysisStore((s) => s.setAnalysis);
  const setAnalyzing = useAnalysisStore((s) => s.setAnalyzing);
  const wsRef = useRef<WebSocket | null>(null);

  const refreshAnalysis = useCallback(async () => {
    if (!documentId) return;
    try {
      const state = await fetchAnalysis(documentId);
      if (!state) return;
      setAnalysis(state);
      if (state.status === "completed" || state.status === "partial" || state.status === "failed") {
        setAnalyzing(false);
      }
    } catch {
      /* polling fallback */
    }
  }, [documentId, setAnalysis, setAnalyzing]);

  useEffect(() => {
    if (!documentId || !enabled) return;

    const ws = new WebSocket(orchestratorWsUrl(documentId));
    wsRef.current = ws;

    ws.onmessage = (msg) => {
      try {
        const envelope = JSON.parse(msg.data as string) as WsEnvelope;
        if (envelope.type === WsMessageType.Orchestrator) {
          const event = envelope.payload as unknown as OrchestratorEvent;
          addEvent(event);
          if (
            event.type === "run_completed" ||
            event.type === "run_failed" ||
            event.type === "agent_completed"
          ) {
            void refreshAnalysis();
          }
        }
      } catch {
        /* ignore parse errors */
      }
    };

    ws.onopen = () => {
      setAnalyzing(true);
      void refreshAnalysis();
    };

    void refreshAnalysis();
    const poll = setInterval(() => void refreshAnalysis(), 2000);

    return () => {
      clearInterval(poll);
      ws.close();
      wsRef.current = null;
    };
  }, [documentId, enabled, addEvent, refreshAnalysis, setAnalyzing]);

  return { refreshAnalysis };
}
