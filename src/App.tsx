import { useState, useMemo, useCallback } from 'react';
import type { ManifestTicker, Timeframe, DateRange } from './types';
import { COMPARISON_COLORS } from './types';
import { useManifest } from './hooks/useManifest';
import { useMultiTickerData } from './hooks/useMultiTickerData';
import { filterByDateRange, calculateGain } from './utils/dateRange';
import { SearchBar } from './components/SearchBar';
import { StockChart } from './components/StockChart';
import { StockInfo } from './components/StockInfo';
import { ComparisonInfo } from './components/ComparisonInfo';
import { DateRangePicker } from './components/DateRangePicker';
import { TimeframeSelector } from './components/TimeframeSelector';

function App() {
  const { loading: manifestLoading, search } = useManifest();
  const [tickers, setTickers] = useState<ManifestTicker[]>([]);
  const [timeframe, setTimeframe] = useState<Timeframe>('daily');
  const [dateRange, setDateRange] = useState<DateRange | null>(null);

  const symbols = useMemo(() => tickers.map((t) => t.s), [tickers]);
  const { datasets, loading: dataLoading, errors } = useMultiTickerData(symbols);

  const mode = tickers.length > 1 ? 'comparison' : 'single';

  const handleSelect = useCallback((ticker: ManifestTicker) => {
    setTickers((prev) => {
      if (prev.length >= 4) return prev;
      if (prev.some((t) => t.s === ticker.s)) return prev;
      return [...prev, ticker];
    });
  }, []);

  const handleRemove = useCallback((symbol: string) => {
    setTickers((prev) => prev.filter((t) => t.s !== symbol));
  }, []);

  // Compute min/max date across all selected tickers (intersection)
  const { minDate, maxDate } = useMemo(() => {
    if (tickers.length === 0) return { minDate: '1970-01-01', maxDate: '2099-12-31' };
    let min = tickers[0].from;
    let max = tickers[0].to;
    for (let i = 1; i < tickers.length; i++) {
      if (tickers[i].from > min) min = tickers[i].from;
      if (tickers[i].to < max) max = tickers[i].to;
    }
    return { minDate: min, maxDate: max };
  }, [tickers]);

  // Single-mode data
  const primaryTicker = tickers[0] ?? null;
  const primaryData = datasets.get(primaryTicker?.s ?? '');

  const filteredData = useMemo(() => {
    if (!primaryData?.data) return null;
    return filterByDateRange(primaryData.data, dateRange);
  }, [primaryData, dateRange]);

  const lastClose = useMemo(() => {
    if (!filteredData?.length) return null;
    return filteredData[filteredData.length - 1][4];
  }, [filteredData]);

  const prevClose = useMemo(() => {
    if (!filteredData || filteredData.length < 2) return null;
    return filteredData[filteredData.length - 2][4];
  }, [filteredData]);

  const firstClose = useMemo(() => {
    if (!filteredData?.length) return null;
    return filteredData[0][4];
  }, [filteredData]);

  const singleRangeGain = useMemo(() => {
    if (!dateRange || !filteredData) return null;
    return calculateGain(filteredData);
  }, [dateRange, filteredData]);

  // Comparison-mode data
  const comparisonData = useMemo(() => {
    if (mode !== 'comparison') return undefined;
    return tickers
      .map((t, i) => {
        const td = datasets.get(t.s);
        if (!td) return null;
        const filtered = filterByDateRange(td.data, dateRange);
        return { symbol: t.s, data: filtered, color: COMPARISON_COLORS[i] };
      })
      .filter((d): d is NonNullable<typeof d> => d !== null);
  }, [mode, tickers, datasets, dateRange]);

  // Last closes and gains per ticker (for ComparisonInfo)
  const lastCloses = useMemo(() => {
    const map = new Map<string, number>();
    for (const t of tickers) {
      const td = datasets.get(t.s);
      if (td?.data.length) {
        const filtered = filterByDateRange(td.data, dateRange);
        if (filtered.length) map.set(t.s, filtered[filtered.length - 1][4]);
      }
    }
    return map;
  }, [tickers, datasets, dateRange]);

  const comparisonGains = useMemo(() => {
    const map = new Map<string, { percent: string; positive: boolean }>();
    for (const t of tickers) {
      const td = datasets.get(t.s);
      if (td?.data.length) {
        const filtered = filterByDateRange(td.data, dateRange);
        const gain = calculateGain(filtered);
        if (gain) map.set(t.s, gain);
      }
    }
    return map;
  }, [tickers, datasets, dateRange]);

  const hasAnyData = tickers.length > 0 && (mode === 'single' ? !!filteredData : (comparisonData?.length ?? 0) > 0);
  const firstError = errors.size > 0 ? [...errors.values()][0] : null;

  return (
    <div className="flex flex-col h-full">
      <header className="px-4 py-3 border-b border-gray-800 flex items-center gap-4">
        <h1 className="text-lg font-semibold text-white whitespace-nowrap">Market History</h1>
        <SearchBar
          onSelect={handleSelect}
          search={search}
          loading={manifestLoading}
          selectedSymbols={symbols}
          maxReached={tickers.length >= 4}
          onRemove={handleRemove}
        />
      </header>

      {tickers.length > 0 && (
        <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between gap-4 flex-wrap">
          {mode === 'single' && primaryTicker ? (
            <StockInfo
              ticker={primaryTicker}
              lastClose={lastClose}
              prevClose={prevClose}
              firstClose={firstClose}
              rangeGain={singleRangeGain}
            />
          ) : (
            <ComparisonInfo
              tickers={tickers}
              lastCloses={lastCloses}
              gains={comparisonGains}
              onRemove={handleRemove}
            />
          )}
          <div className="flex items-center gap-3">
            <TimeframeSelector value={timeframe} onChange={setTimeframe} />
          </div>
        </div>
      )}

      {tickers.length > 0 && (
        <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between gap-4 flex-wrap">
          <DateRangePicker
            value={dateRange}
            onChange={setDateRange}
            minDate={minDate}
            maxDate={maxDate}
          />
          {mode === 'single' && (
            <button
              onClick={() => handleRemove(primaryTicker!.s)}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              Clear
            </button>
          )}
        </div>
      )}

      <main className="flex-1 relative min-h-0">
        {tickers.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-600">
            <p>Search for a ticker to get started</p>
          </div>
        )}

        {dataLoading && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500">
            <p>Loading...</p>
          </div>
        )}

        {firstError && !dataLoading && (
          <div className="absolute inset-0 flex items-center justify-center text-red-400">
            <p>Error: {firstError}</p>
          </div>
        )}

        {hasAnyData && !dataLoading && (
          <StockChart
            mode={mode}
            data={mode === 'single' ? filteredData : null}
            timeframe={timeframe}
            comparisonData={comparisonData}
          />
        )}
      </main>
    </div>
  );
}

export default App;
