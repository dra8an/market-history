import { useState, useEffect, useMemo, useCallback } from 'react';
import type { Manifest, ManifestTicker } from '../types';

export function useManifest() {
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/data/manifest.json')
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load manifest: ${res.status}`);
        return res.json();
      })
      .then((data: Manifest) => {
        setManifest(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const tickerMap = useMemo(() => {
    if (!manifest) return new Map<string, ManifestTicker>();
    const map = new Map<string, ManifestTicker>();
    for (const t of manifest.tickers) {
      map.set(t.s, t);
    }
    return map;
  }, [manifest]);

  const search = useCallback(
    (query: string): ManifestTicker[] => {
      if (!manifest || !query) return [];
      const q = query.toUpperCase();
      const results: ManifestTicker[] = [];

      // Symbol prefix matches first
      for (const t of manifest.tickers) {
        if (t.s.startsWith(q)) {
          results.push(t);
          if (results.length >= 50) return results;
        }
      }

      // Then name prefix matches
      const qLower = query.toLowerCase();
      for (const t of manifest.tickers) {
        if (t.n.toLowerCase().startsWith(qLower) && !t.s.startsWith(q)) {
          results.push(t);
          if (results.length >= 50) return results;
        }
      }

      return results;
    },
    [manifest]
  );

  const getTicker = useCallback(
    (symbol: string): ManifestTicker | undefined => {
      return tickerMap.get(symbol);
    },
    [tickerMap]
  );

  return { manifest, loading, error, search, getTicker };
}
