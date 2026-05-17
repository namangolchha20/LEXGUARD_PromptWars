import { WsEnvelope, WsMessageType } from "@lexguard/shared";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export function createWebSocket(onMessage: (envelope: WsEnvelope) => void): WebSocket {
  const ws = new WebSocket(`${WS_URL}/ws`);

  ws.onmessage = (event) => {
    const envelope = JSON.parse(event.data as string) as WsEnvelope;
    onMessage(envelope);
  };

  return ws;
}

export function sendPing(ws: WebSocket): void {
  const ping: WsEnvelope = { type: WsMessageType.Ping, payload: {} };
  ws.send(JSON.stringify(ping));
}
