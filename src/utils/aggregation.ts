import type { Timeframe } from '../types';

// Each row: [timestamp, open, high, low, close, volume]
type OHLCVRow = number[];

function getWeekKey(date: Date): string {
  // ISO week: use Monday as start of week
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  // Set to nearest Thursday (current date + 4 - current day number, with Sunday as 7)
  const day = d.getDay() || 7;
  d.setDate(d.getDate() + 4 - day);
  const yearStart = new Date(d.getFullYear(), 0, 1);
  const weekNum = Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return `${d.getFullYear()}-W${String(weekNum).padStart(2, '0')}`;
}

function getMonthKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

function aggregateGroup(rows: OHLCVRow[]): OHLCVRow {
  const open = rows[0][1];
  let high = -Infinity;
  let low = Infinity;
  let volume = 0;

  for (const row of rows) {
    if (row[2] > high) high = row[2];
    if (row[3] < low) low = row[3];
    volume += row[5];
  }

  const close = rows[rows.length - 1][4];
  const timestamp = rows[0][0]; // Use first day's timestamp

  return [timestamp, open, high, low, close, volume];
}

export function aggregateData(daily: OHLCVRow[], timeframe: Timeframe): OHLCVRow[] {
  if (timeframe === 'daily') return daily;

  const keyFn = timeframe === 'weekly' ? getWeekKey : getMonthKey;
  const groups = new Map<string, OHLCVRow[]>();

  for (const row of daily) {
    const date = new Date(row[0] * 1000);
    const key = keyFn(date);
    let group = groups.get(key);
    if (!group) {
      group = [];
      groups.set(key, group);
    }
    group.push(row);
  }

  const result: OHLCVRow[] = [];
  for (const rows of groups.values()) {
    result.push(aggregateGroup(rows));
  }

  return result;
}
