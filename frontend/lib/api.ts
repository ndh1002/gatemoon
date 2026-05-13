import type { AlertRow, RiskAnalysisRow, ScanPayload, SmartMoneyRow, VolumeLeader } from "./types";

export function getApiBase(): string {
  if (typeof window === "undefined") {
    return (
      process.env.API_INTERNAL_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000"
    );
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export async function fetchLatest(): Promise<ScanPayload> {
  const res = await fetch(`${getApiBase()}/api/latest`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load latest scan");
  return res.json();
}

export async function fetchTopVolume() {
  const res = await fetch(`${getApiBase()}/api/top-volume`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load volume leaders");
  return res.json();
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchMoonshots(limit = 20): Promise<ScanPayload["rows"]> {
  return getJson<ScanPayload["rows"]>(`${getApiBase()}/api/moonshots?limit=${limit}`);
}

export async function fetchTopGainers(limit = 20): Promise<ScanPayload["rows"]> {
  return getJson<ScanPayload["rows"]>(`${getApiBase()}/api/top-gainers?limit=${limit}`);
}

export async function fetchHeatmap(limit = 80): Promise<Array<Record<string, unknown>>> {
  return getJson<Array<Record<string, unknown>>>(`${getApiBase()}/api/heatmap?limit=${limit}`);
}

export async function fetchSmartMoney(limit = 20): Promise<SmartMoneyRow[]> {
  return getJson<SmartMoneyRow[]>(`${getApiBase()}/api/smart-money?limit=${limit}`);
}

export async function fetchRiskAnalysis(limit = 20): Promise<RiskAnalysisRow[]> {
  return getJson<RiskAnalysisRow[]>(`${getApiBase()}/api/risk-analysis?limit=${limit}`);
}

export async function fetchAlerts(limit = 20): Promise<AlertRow[]> {
  return getJson<AlertRow[]>(`${getApiBase()}/api/alerts?limit=${limit}`);
}

export async function fetchTopVolumeLeaders(limit = 20): Promise<VolumeLeader[]> {
  return getJson<VolumeLeader[]>(`${getApiBase()}/api/top-volume?limit=${limit}`);
}
