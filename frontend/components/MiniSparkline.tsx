"use client";

import { useEffect, useRef } from "react";
import { ColorType, createChart, type IChartApi, type ISeriesApi, type UTCTimestamp } from "lightweight-charts";

type Props = {
  last?: number;
  changePct?: number;
  height?: number;
};

function buildSeries(last: number, changePct: number, points = 40): { time: UTCTimestamp; value: number }[] {
  const now = Math.floor(Date.now() / 1000);
  const startPrice = last / (1 + (changePct || 0) / 100);
  const out: { time: UTCTimestamp; value: number }[] = [];
  for (let i = 0; i < points; i++) {
    const t = (now - (points - i)) as UTCTimestamp;
    const p = i / (points - 1);
    const noise = (Math.sin(i * 1.7) * 0.001 + Math.cos(i * 0.9) * 0.0007) * (last || 1);
    const v = startPrice + ((last || 1) - startPrice) * p + noise;
    out.push({ time: t, value: v });
  }
  out[out.length - 1] = { time: now as UTCTimestamp, value: last || 1 };
  return out;
}

export function MiniSparkline({ last = 0, changePct = 0, height = 64 }: Props) {
  const ref = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = createChart(ref.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
      },
      grid: { vertLines: { visible: false }, horzLines: { visible: false } },
      rightPriceScale: { visible: false },
      timeScale: { visible: false },
      crosshair: { mode: 0 },
    });
    const series = chart.addLineSeries({
      color: changePct >= 0 ? "#34d399" : "#f43f5e",
      lineWidth: 2,
    });
    chartRef.current = chart;
    seriesRef.current = series;
    series.setData(buildSeries(last || 1, changePct));
    chart.timeScale().fitContent();

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: ref.current?.clientWidth ?? 300 });
    });
    ro.observe(ref.current);
    chart.applyOptions({ width: ref.current.clientWidth });

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [last, changePct, height]);

  useEffect(() => {
    const s = seriesRef.current;
    if (!s) return;
    s.setData(buildSeries(last || 1, changePct));
    chartRef.current?.timeScale().fitContent();
  }, [last, changePct]);

  return <div ref={ref} className="w-full" style={{ height }} />;
}
