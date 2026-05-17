import type {
  AnalysisState,
  HealthResponse,
  PipelineRunResponse,
} from "@lexguard/shared";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
  return response.json() as Promise<HealthResponse>;
}

export async function uploadAndAnalyze(file: File): Promise<PipelineRunResponse> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_URL}/api/v1/documents/analyze`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? `Upload failed: ${response.status}`);
  }
  return response.json() as Promise<PipelineRunResponse>;
}

export async function fetchAnalysis(documentId: string): Promise<AnalysisState | null> {
  const response = await fetch(`${API_URL}/api/v1/documents/${documentId}/analysis`, {
    cache: "no-store",
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Failed to fetch analysis: ${response.status}`);
  return response.json() as Promise<AnalysisState>;
}

export function orchestratorWsUrl(documentId: string): string {
  const base = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
  return `${base}/ws/orchestrator/${documentId}`;
}
