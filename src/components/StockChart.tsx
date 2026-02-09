import { useEffect, useRef } from 'react';
import { createChart, CandlestickSeries, HistogramSeries, LineSeries } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, CandlestickData, HistogramData, LineData, Time } from 'lightweight-charts';
import type { Timeframe } from '../types';
import { aggregateData } from '../utils/aggregation';
import { timestampToDateStr } from '../utils/format';

interface ComparisonDataset {
  symbol: string;
  data: number[][];
  color: string;
}

interface StockChartProps {
  mode: 'single' | 'comparison';
  data: number[][] | null;
  timeframe: Timeframe;
  comparisonData?: ComparisonDataset[];
}

function normalizeToPercent(data: number[][]): LineData[] {
  if (data.length === 0) return [];
  const firstClose = data[0][4];
  if (firstClose <= 0) return [];
  return data.map((row) => ({
    time: timestampToDateStr(row[0]) as Time,
    value: ((row[4] - firstClose) / firstClose) * 100,
  }));
}

export function StockChart({ mode, data, timeframe, comparisonData }: StockChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const lineSeriesMapRef = useRef<Map<string, ISeriesApi<'Line'>>>(new Map());
  const currentModeRef = useRef<'single' | 'comparison' | null>(null);

  // Create chart once
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: '#0f1117' },
        textColor: '#6b7280',
      },
      grid: {
        vertLines: { color: '#1f2937' },
        horzLines: { color: '#1f2937' },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: '#1f2937',
      },
      timeScale: {
        borderColor: '#1f2937',
        timeVisible: false,
      },
    });

    chartRef.current = chart;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        chart.applyOptions({ width, height });
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
      lineSeriesMapRef.current.clear();
      currentModeRef.current = null;
    };
  }, []);

  // Clear all series when switching modes
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    if (currentModeRef.current !== mode) {
      // Remove existing series
      if (candleSeriesRef.current) {
        chart.removeSeries(candleSeriesRef.current);
        candleSeriesRef.current = null;
      }
      if (volumeSeriesRef.current) {
        chart.removeSeries(volumeSeriesRef.current);
        volumeSeriesRef.current = null;
      }
      for (const series of lineSeriesMapRef.current.values()) {
        chart.removeSeries(series);
      }
      lineSeriesMapRef.current.clear();

      // Create series for new mode
      if (mode === 'single') {
        chart.priceScale('right').applyOptions({
          mode: 0, // Normal mode
        });

        const candleSeries = chart.addSeries(CandlestickSeries, {
          upColor: '#22c55e',
          downColor: '#ef4444',
          borderUpColor: '#22c55e',
          borderDownColor: '#ef4444',
          wickUpColor: '#22c55e',
          wickDownColor: '#ef4444',
        });

        const volumeSeries = chart.addSeries(HistogramSeries, {
          priceFormat: { type: 'volume' },
          priceScaleId: 'volume',
        });

        chart.priceScale('volume').applyOptions({
          scaleMargins: { top: 0.8, bottom: 0 },
        });

        candleSeriesRef.current = candleSeries;
        volumeSeriesRef.current = volumeSeries;
      } else {
        chart.priceScale('right').applyOptions({
          mode: 0,
        });
      }

      currentModeRef.current = mode;
    }
  }, [mode]);

  // Update single-mode data
  useEffect(() => {
    if (mode !== 'single' || !candleSeriesRef.current || !volumeSeriesRef.current || !data) return;

    const aggregated = aggregateData(data, timeframe);

    const candleData: CandlestickData[] = aggregated.map((row) => ({
      time: timestampToDateStr(row[0]) as Time,
      open: row[1],
      high: row[2],
      low: row[3],
      close: row[4],
    }));

    const volumeData: HistogramData[] = aggregated.map((row) => ({
      time: timestampToDateStr(row[0]) as Time,
      value: row[5],
      color: row[4] >= row[1] ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)',
    }));

    candleSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);
    chartRef.current?.timeScale().fitContent();
  }, [mode, data, timeframe]);

  // Update comparison-mode data
  useEffect(() => {
    if (mode !== 'comparison' || !chartRef.current || !comparisonData) return;

    const chart = chartRef.current;
    const existingSymbols = new Set(lineSeriesMapRef.current.keys());
    const newSymbols = new Set(comparisonData.map((d) => d.symbol));

    // Remove series for symbols no longer present
    for (const symbol of existingSymbols) {
      if (!newSymbols.has(symbol)) {
        const series = lineSeriesMapRef.current.get(symbol)!;
        chart.removeSeries(series);
        lineSeriesMapRef.current.delete(symbol);
      }
    }

    // Add or update series for each symbol
    for (const dataset of comparisonData) {
      let series = lineSeriesMapRef.current.get(dataset.symbol);
      if (!series) {
        series = chart.addSeries(LineSeries, {
          color: dataset.color,
          lineWidth: 2,
          priceFormat: {
            type: 'custom',
            formatter: (price: number) => price.toFixed(2) + '%',
          },
        });
        lineSeriesMapRef.current.set(dataset.symbol, series);
      } else {
        series.applyOptions({ color: dataset.color });
      }

      const aggregated = aggregateData(dataset.data, timeframe);
      const lineData = normalizeToPercent(aggregated);
      series.setData(lineData);
    }

    chart.timeScale().fitContent();
  }, [mode, comparisonData, timeframe]);

  return <div ref={containerRef} className="w-full h-full" />;
}
