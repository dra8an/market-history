import { useState, useMemo } from 'react';
import type { ManifestTicker, Timeframe } from './types';
import { useManifest } from './hooks/useManifest';
import { useTickerData } from './hooks/useTickerData';
import { SearchBar } from './components/SearchBar';
import { StockChart } from './components/StockChart';
import { StockInfo } from './components/StockInfo';
import { TimeframeSelector } from './components/TimeframeSelector';

function App() {
  const { loading: manifestLoading, search } = useManifest();
  const [selectedTicker, setSelectedTicker] = useState<ManifestTicker | null>(null);
  const [timeframe, setTimeframe] = useState<Timeframe>('daily');
  const { data: tickerData, loading: dataLoading, error: dataError } = useTickerData(
    selectedTicker?.s ?? null
  );

  const lastClose = useMemo(() => {
    if (!tickerData?.data.length) return null;
    return tickerData.data[tickerData.data.length - 1][4];
  }, [tickerData]);

  const prevClose = useMemo(() => {
    if (!tickerData?.data || tickerData.data.length < 2) return null;
    return tickerData.data[tickerData.data.length - 2][4];
  }, [tickerData]);

  return (
    <div className="flex flex-col h-full">
      <header className="px-4 py-3 border-b border-gray-800 flex items-center gap-4">
        <h1 className="text-lg font-semibold text-white whitespace-nowrap">Market History</h1>
        <SearchBar onSelect={setSelectedTicker} search={search} loading={manifestLoading} />
      </header>

      {selectedTicker && (
        <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between gap-4 flex-wrap">
          <StockInfo ticker={selectedTicker} lastClose={lastClose} prevClose={prevClose} />
          <TimeframeSelector value={timeframe} onChange={setTimeframe} />
        </div>
      )}

      <main className="flex-1 relative min-h-0">
        {!selectedTicker && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-600">
            <p>Search for a ticker to get started</p>
          </div>
        )}

        {dataLoading && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500">
            <p>Loading {selectedTicker?.s}...</p>
          </div>
        )}

        {dataError && (
          <div className="absolute inset-0 flex items-center justify-center text-red-400">
            <p>Error: {dataError}</p>
          </div>
        )}

        {selectedTicker && tickerData && !dataLoading && (
          <StockChart data={tickerData.data} timeframe={timeframe} />
        )}
      </main>
    </div>
  );
}

export default App;
