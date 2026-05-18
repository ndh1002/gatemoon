"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ScanPayload } from "@/lib/types";

const WS = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export function useMarketWs(initial: ScanPayload | null) {
  const [data, setData] = useState<ScanPayload | null>(initial);
  const [status, setStatus] = useState<"connecting" | "open" | "closed" | "error">("connecting");
  const wsRef = useRef<WebSocket | null>(null);

  const applyPayload = useCallback((raw: string) => {
    try {
      const parsed = JSON.parse(raw) as ScanPayload;
      if (parsed?.type === "market_scan") {
        setData(parsed);
      }
    } catch {
      /* ping or malformed */
    }
  }, []);

  useEffect(() => {
    const url = `${WS.replace(/\/$/, "")}/ws/market`;
    /* const ws = new WebSocket(url); được thay bởi đoạn mã dưới */
    const protocol =
      window.location.protocol === "https:"
        ? "wss"
        : "ws";

    const ws = new WebSocket(
      `${protocol}://${window.location.host}/ws/market`
    );

    wsRef.current = ws;
    setStatus("connecting");
    ws.onopen = () => setStatus("open");
    ws.onclose = () => setStatus("closed");
    ws.onerror = () => setStatus("error");
    ws.onmessage = (ev) => applyPayload(String(ev.data));
    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [applyPayload]);

  return { data, status };
}
