import { useState, useEffect, useRef } from 'react';
import type { TickerData } from '../types';

const cache = new Map<string, TickerData>();
const MAX_CACHE_SIZE = 50;

function evictOldest() {
  if (cache.size >= MAX_CACHE_SIZE) {
    const firstKey = cache.keys().next().value;
    if (firstKey) cache.delete(firstKey);
  }
}

export function useTickerData(symbol: string | null) {
  const [data, setData] = useState<TickerData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!symbol) {
      setData(null);
      setError(null);
      return;
    }

    // Check cache first
    const cached = cache.get(symbol);
    if (cached) {
      setData(cached);
      setLoading(false);
      setError(null);
      return;
    }

    // Cancel any in-flight request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);

    fetch(`/data/tickers/${symbol}.json`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load ${symbol}: ${res.status}`);
        return res.json();
      })
      .then((tickerData: TickerData) => {
        evictOldest();
        cache.set(symbol, tickerData);
        setData(tickerData);
        setLoading(false);
      })
      .catch((err) => {
        if (err.name === 'AbortError') return;
        setError(err.message);
        setLoading(false);
      });

    return () => controller.abort();
  }, [symbol]);

  return { data, loading, error };
}
