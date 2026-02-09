import { useMemo } from 'react';
import { useTickerData } from './useTickerData';
import type { TickerData } from '../types';

export function useMultiTickerData(symbols: string[]) {
  // 4 fixed hook calls to respect rules of hooks
  const r0 = useTickerData(symbols[0] ?? null);
  const r1 = useTickerData(symbols[1] ?? null);
  const r2 = useTickerData(symbols[2] ?? null);
  const r3 = useTickerData(symbols[3] ?? null);

  const results = [r0, r1, r2, r3];

  const datasets = useMemo(() => {
    const map = new Map<string, TickerData>();
    for (let i = 0; i < symbols.length && i < 4; i++) {
      const d = results[i].data;
      if (d) map.set(symbols[i], d);
    }
    return map;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbols[0], symbols[1], symbols[2], symbols[3], r0.data, r1.data, r2.data, r3.data]);

  const loading = symbols.some((_, i) => i < 4 && results[i].loading);

  const errors = useMemo(() => {
    const map = new Map<string, string>();
    for (let i = 0; i < symbols.length && i < 4; i++) {
      const e = results[i].error;
      if (e) map.set(symbols[i], e);
    }
    return map;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbols[0], symbols[1], symbols[2], symbols[3], r0.error, r1.error, r2.error, r3.error]);

  return { datasets, loading, errors };
}
