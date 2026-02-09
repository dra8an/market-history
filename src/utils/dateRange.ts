import type { DateRange } from '../types';

export function filterByDateRange(data: number[][], range: DateRange | null): number[][] {
  if (!range) return data;

  const fromTs = new Date(range.from + 'T00:00:00').getTime() / 1000;
  const toTs = new Date(range.to + 'T23:59:59').getTime() / 1000;

  return data.filter((row) => row[0] >= fromTs && row[0] <= toTs);
}

export function calculateGain(data: number[][]): { percent: string; positive: boolean } | null {
  if (data.length < 2) return null;

  const firstClose = data[0][4];
  const lastClose = data[data.length - 1][4];

  if (firstClose <= 0) return null;

  const pct = ((lastClose - firstClose) / firstClose) * 100;
  return {
    percent: (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%',
    positive: pct >= 0,
  };
}
