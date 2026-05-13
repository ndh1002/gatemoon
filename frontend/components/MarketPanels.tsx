"use client";

import clsx from "clsx";
import { motion } from "framer-motion";
import type { AlertRow, RiskAnalysisRow, ScanRow, SmartMoneyRow } from "@/lib/types";

function heatColor(score: number) {
  const t = Math.max(0, Math.min(1, score / 100));
  const hue = 210 - t * 150;
  return `hsl(${hue} 85% ${28 + t * 22}%)`;
}

export function Heatmap({ rows, limit = 48 }: { rows: ScanRow[]; limit?: number }) {
  const slice = rows.slice(0, limit);
  return (
    <div className="grid grid-cols-6 gap-2 sm:grid-cols-8 md:grid-cols-10">
      {slice.map((r, idx) => (
        <motion.div
          key={r.symbol}
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: idx * 0.008 }}
          className="group relative overflow-hidden rounded-md border border-tv-border/60 px-1 py-2 text-center font-mono text-[10px] text-white/90"
          style={{ background: heatColor(r.moonshot_score) }}
          title={`${r.symbol} · Moon ${r.moonshot_score.toFixed(1)} · Risk ${r.risk_score.toFixed(1)}`}
        >
          <div className="truncate">{r.symbol.replace("/USDT", "")}</div>
          <div className="text-[9px] text-black/70">{r.moonshot_score.toFixed(0)}</div>
        </motion.div>
      ))}
    </div>
  );
}

export function MoonTable({ rows }: { rows: ScanRow[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-[900px] w-full border-collapse text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-zinc-500">
            <th className="pb-3 pr-4">Pair</th>
            <th className="pb-3 pr-4">Last</th>
            <th className="pb-3 pr-4">24h</th>
            <th className="pb-3 pr-4">Moonshot</th>
            <th className="pb-3 pr-4">Confidence</th>
            <th className="pb-3 pr-4">Risk</th>
            <th className="pb-3 pr-4">Vol spike</th>
            <th className="pb-3 pr-4">Breakout</th>
            <th className="pb-3">Whale</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const d = r.details || {};
            const pct = Number(r.ticker?.percentage ?? 0);
            return (
              <motion.tr
                key={r.symbol}
                layout
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.012 }}
                className="border-t border-tv-border/60 hover:bg-white/[0.03]"
              >
                <td className="py-3 pr-4 font-mono text-xs text-tv-cyan">{r.symbol}</td>
                <td className="py-3 pr-4 font-mono text-xs">{fmt(r.ticker?.last)}</td>
                <td className={clsx("py-3 pr-4 font-mono text-xs", pct >= 0 ? "text-emerald-400" : "text-rose-400")}>
                  {pct.toFixed(2)}%
                </td>
                <td className="py-3 pr-4">
                  <ScorePill value={r.moonshot_score} kind="moon" />
                </td>
                <td className="py-3 pr-4">
                  <ScorePill value={r.confidence} kind="conf" />
                </td>
                <td className="py-3 pr-4">
                  <ScorePill value={r.risk_score} kind="risk" />
                </td>
                <td className="py-3 pr-4 text-xs text-zinc-300">{String(d.volume_spike ?? "—")}</td>
                <td className="py-3 pr-4 text-xs text-zinc-300">{String(d.momentum_breakout ?? "—")}</td>
                <td className="py-3 text-xs text-zinc-300">{String(d.whale_activity ?? "—")}</td>
              </motion.tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function VolumeLeaders({ items }: { items: { market?: string; quote_volume?: number; moonshot_score?: number }[] }) {
  return (
    <div className="space-y-2">
      {items.map((it, idx) => (
        <motion.div
          key={it.market ?? String(idx)}
          initial={{ opacity: 0, x: 8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.02 }}
          className="flex items-center justify-between rounded-lg border border-tv-border/60 bg-black/20 px-3 py-2"
        >
          <div className="font-mono text-xs text-tv-cyan">{it.market}</div>
          <div className="text-right">
            <div className="font-mono text-xs text-amber-200">{fmtUsd(it.quote_volume)}</div>
            <div className="text-[10px] text-zinc-500">Moon {Number(it.moonshot_score ?? 0).toFixed(1)}</div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

export function TopGainers({ rows }: { rows: ScanRow[] }) {
  return (
    <div className="space-y-2">
      {rows.map((r, idx) => {
        const pct = Number(r.ticker?.percentage ?? 0);
        return (
          <motion.div
            key={`${r.symbol}-${idx}`}
            initial={{ opacity: 0, x: 8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.02 }}
            className="flex items-center justify-between rounded-lg border border-tv-border/60 bg-black/20 px-3 py-2"
          >
            <div className="font-mono text-xs text-tv-cyan">{r.symbol}</div>
            <div className={clsx("font-mono text-xs", pct >= 0 ? "text-emerald-300" : "text-rose-300")}>
              {pct.toFixed(2)}%
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

export function SmartMoneyPanel({ items }: { items: SmartMoneyRow[] }) {
  return (
    <div className="space-y-2">
      {items.map((it, idx) => (
        <motion.div
          key={`${it.symbol}-${idx}`}
          initial={{ opacity: 0, x: 8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.02 }}
          className="flex items-center justify-between rounded-lg border border-tv-border/60 bg-black/20 px-3 py-2"
        >
          <div className="font-mono text-xs text-tv-cyan">{it.symbol}</div>
          <div className="text-right">
            <div className="font-mono text-xs text-amber-100">Smart {Number(it.smart_money ?? 0).toFixed(1)}</div>
            <div className="text-[10px] text-zinc-500">Whale {Number(it.whale_activity ?? 0).toFixed(1)}</div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

export function RiskPanel({ items }: { items: RiskAnalysisRow[] }) {
  return (
    <div className="space-y-2">
      {items.map((it, idx) => (
        <motion.div
          key={`${it.symbol}-${idx}`}
          initial={{ opacity: 0, x: 8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.02 }}
          className="flex items-center justify-between rounded-lg border border-tv-border/60 bg-black/20 px-3 py-2"
        >
          <div className="font-mono text-xs text-tv-cyan">{it.symbol}</div>
          <div className="text-right">
            <div className="font-mono text-xs text-rose-200">Risk {Number(it.risk_score ?? 0).toFixed(1)}</div>
            <div className="text-[10px] text-zinc-500">
              Spread {Number(it.spread_risk ?? 0).toFixed(0)} · Vol {Number(it.volatility_risk ?? 0).toFixed(0)}
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

export function AlertsPanel({ items }: { items: AlertRow[] }) {
  return (
    <div className="space-y-2">
      {items.map((it, idx) => (
        <motion.div
          key={`${it.id}-${idx}`}
          initial={{ opacity: 0, x: 8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.015 }}
          className="rounded-lg border border-tv-border/60 bg-black/20 px-3 py-2"
        >
          <div className="flex items-center justify-between">
            <div className="font-mono text-xs text-tv-cyan">{it.market}</div>
            <div className="text-[10px] text-zinc-500">{it.ts ?? "—"}</div>
          </div>
          <div className="mt-1 text-[10px] text-zinc-400">
            {it.channel} · {it.status}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function fmt(n?: number) {
  if (n === undefined || n === null || Number.isNaN(n)) return "—";
  if (n >= 1000) return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return n.toPrecision(6);
}

function fmtUsd(n?: number) {
  if (n === undefined || n === null || Number.isNaN(n)) return "—";
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

function ScorePill({ value, kind }: { value: number; kind: "moon" | "conf" | "risk" }) {
  const cls =
    kind === "moon"
      ? "from-amber-500/30 to-amber-400/10 text-amber-100"
      : kind === "conf"
        ? "from-cyan-500/25 to-cyan-400/10 text-cyan-100"
        : value > 55
          ? "from-rose-500/30 to-rose-400/10 text-rose-100"
          : "from-emerald-500/20 to-emerald-400/10 text-emerald-100";
  return (
    <span
      className={clsx(
        "inline-flex min-w-[52px] justify-center rounded-full bg-gradient-to-r px-2 py-1 font-mono text-[11px] ring-1 ring-white/10",
        cls,
      )}
    >
      {value.toFixed(1)}
    </span>
  );
}
