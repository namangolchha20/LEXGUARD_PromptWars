"use client";

import { useEffect, useState } from "react";
import type { HealthResponse } from "@lexguard/shared";
import { WsEnvelope, WsMessageType } from "@lexguard/shared";
import { fetchHealth } from "@/lib/api";
import { createWebSocket, sendPing } from "@/lib/websocket";

export function StatusPanel() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<string>("disconnected");

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err: Error) => setHealthError(err.message));
  }, []);

  useEffect(() => {
    const ws = createWebSocket((envelope: WsEnvelope) => {
      if (envelope.type === WsMessageType.Connected) {
        setWsStatus("connected");
        sendPing(ws);
      }
      if (envelope.type === WsMessageType.Pong) {
        setWsStatus("pong received");
      }
    });

    ws.onerror = () => setWsStatus("error");
    ws.onclose = () => setWsStatus("disconnected");

    return () => ws.close();
  }, []);

  return (
    <section
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        padding: "1.5rem 2rem",
        minWidth: "320px",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
    >
      <StatusRow
        label="API"
        value={health ? `${health.status} (${health.version})` : healthError ?? "loading…"}
        ok={health?.status === "ok"}
      />
      <StatusRow label="WebSocket" value={wsStatus} ok={wsStatus.includes("pong")} />
    </section>
  );
}

function StatusRow({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div
      style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}
    >
      <span style={{ color: "var(--muted)", fontSize: "0.875rem" }}>{label}</span>
      <span
        style={{
          fontSize: "0.875rem",
          fontWeight: 500,
          color: ok ? "#22c55e" : ok === false ? "#ef4444" : "var(--foreground)",
        }}
      >
        {value}
      </span>
    </div>
  );
}
