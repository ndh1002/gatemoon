"use client";

import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { useMarketWs } from "@/hooks/useMarketWs";
import type { AlertRow, RiskAnalysisRow, ScanPayload, ScanRow, SmartMoneyRow, VolumeLeader } from "@/lib/types";
import { getApiBase } from "@/lib/api";
import { AlertsPanel, Heatmap, MoonTable, RiskPanel, SmartMoneyPanel, TopGainers, VolumeLeaders } from "@/components/MarketPanels";
import { MiniSparkline } from "@/components/MiniSparkline";

export function Dashboard({ initial }: { initial: ScanPayload | null }) {
  const { data, status } = useMarketWs(initial);
  const rows = (data?.rows ?? []) as ScanRow[];
  const [vol, setVol] = useState<VolumeLeader[]>([]);
  const [gainers, setGainers] = useState<ScanRow[]>([]);
  const [smartMoney, setSmartMoney] = useState<SmartMoneyRow[]>([]);
  const [riskRows, setRiskRows] = useState<RiskAnalysisRow[]>([]);
  const [alerts, setAlerts] = useState<AlertRow[]>([]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [volRes, gainersRes, smartRes, riskRes, alertRes] = await Promise.all([
          fetch(`${getApiBase()}/api/top-volume?limit=10`, { cache: "no-store" }),
          fetch(`${getApiBase()}/api/top-gainers?limit=10`, { cache: "no-store" }),
          fetch(`${getApiBase()}/api/smart-money?limit=10`, { cache: "no-store" }),
          fetch(`${getApiBase()}/api/risk-analysis?limit=10`, { cache: "no-store" }),
          fetch(`${getApiBase()}/api/alerts?limit=10`, { cache: "no-store" }),
        ]);
        if (cancelled) return;
        if (volRes.ok) setVol(await volRes.json());
        if (gainersRes.ok) setGainers(await gainersRes.json());
        if (smartRes.ok) setSmartMoney(await smartRes.json());
        if (riskRes.ok) setRiskRows(await riskRes.json());
        if (alertRes.ok) setAlerts(await alertRes.json());
      } catch {
        /* ignore */
      }
    };
    void load();
    const id = setInterval(async () => {
      await load();
    }, 20_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const hero = useMemo(() => rows[0], [rows]);

  return (
    <div className="mx-auto max-w-[1400px] px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <header className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-amber-400 to-orange-600 shadow-glow" />
            <div>
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Gate MoonHunter AI</h1>
              <p className="text-sm text-zinc-400">
                Realtime Gate.io scanner · volume · whales · volatility · social velocity · moonshot scoring
              </p>
            </div>
          </motion.div>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-400">
          <span
            className={`rounded-full px-3 py-1 font-mono ring-1 ${
              status === "open"
                ? "bg-emerald-500/10 text-emerald-300 ring-emerald-500/30"
                : "bg-amber-500/10 text-amber-200 ring-amber-500/30"
            }`}
          >
            WS: {status}
          </span>
          <span className="rounded-full bg-white/5 px-3 py-1 font-mono ring-1 ring-white/10">
            Last scan: {data?.generated_at ?? "—"}
          </span>
          <span className="rounded-full bg-white/5 px-3 py-1 font-mono ring-1 ring-white/10">Pairs: {rows.length}</span>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-3">
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass relative overflow-hidden rounded-2xl p-5 lg:col-span-2"
        >
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Top moonshot</h2>
              <p className="text-xs text-zinc-500">Highest composite AI score on this scan</p>
            </div>
            {hero ? (
              <div className="text-right">
                <div className="font-mono text-lg text-tv-cyan">{hero.symbol}</div>
                <div className="text-xs text-zinc-500">
                  Moon {hero.moonshot_score.toFixed(1)} · Conf {hero.confidence.toFixed(1)} · Risk{" "}
                  {hero.risk_score.toFixed(1)}
                </div>
              </div>
            ) : null}
          </div>
          {hero ? (
            <div className="grid gap-4 md:grid-cols-[1.2fr_1fr]">
              <MiniSparkline last={hero.ticker?.last} changePct={Number(hero.ticker?.percentage ?? 0)} height={120} />
              <div className="grid grid-cols-2 gap-3 text-xs">
                <Metric label="Vol spike" value={String(hero.details?.volume_spike ?? "—")} />
                <Metric label="Breakout" value={String(hero.details?.momentum_breakout ?? "—")} />
                <Metric label="Smart $" value={String(hero.details?.smart_money ?? "—")} />
                <Metric label="Whales" value={String(hero.details?.whale_activity ?? "—")} />
                <Metric label="Social" value={String(hero.details?.social_velocity ?? "—")} />
                <Metric label="Trend" value={String(hero.details?.trend_strength ?? "—")} />
              </div>
            </div>
          ) : (
            <p className="text-sm text-zinc-500">Waiting for first live scan from Gate.io…</p>
          )}
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass rounded-2xl p-5"
        >
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-400">Volume inflow</h2>
          <VolumeLeaders items={vol.slice(0, 10)} />
        </motion.section>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.06 }}
          className="glass rounded-2xl p-5"
        >
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-400">Top gainers</h2>
          <TopGainers rows={gainers} />
        </motion.section>
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.07 }}
          className="glass rounded-2xl p-5"
        >
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-400">Smart money</h2>
          <SmartMoneyPanel items={smartMoney} />
        </motion.section>
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08 }}
          className="glass rounded-2xl p-5"
        >
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-400">Risk analysis</h2>
          <RiskPanel items={riskRows} />
        </motion.section>
      </div>

      <motion.section
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08 }}
        className="glass mt-6 rounded-2xl p-5"
      >
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Moonshot heatmap</h2>
            <p className="text-xs text-zinc-500">Color = moonshot score intensity</p>
          </div>
        </div>
        <Heatmap rows={rows} />
      </motion.section>

      <motion.section
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="glass mt-6 rounded-2xl p-5"
      >
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Live leaderboard</h2>
            <p className="text-xs text-zinc-500">Sorted by moonshot · updates over WebSocket</p>
          </div>
        </div>
        <MoonTable rows={rows} />
      </motion.section>

      <motion.section
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.12 }}
        className="glass mt-6 rounded-2xl p-5"
      >
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Alerts</h2>
            <p className="text-xs text-zinc-500">Latest Telegram alert history</p>
          </div>
        </div>
        <AlertsPanel items={alerts} />
      </motion.section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-tv-border/50 bg-black/25 p-3">
      <div className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</div>
      <div className="mt-1 font-mono text-sm text-zinc-100">{value}</div>
    </div>
  );
}
