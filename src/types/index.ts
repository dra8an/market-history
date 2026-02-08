export interface TickerData {
  symbol: string;
  data: number[][]; // [timestamp, open, high, low, close, volume][]
}

export interface ManifestTicker {
  s: string;    // symbol
  n: string;    // name
  e: string;    // exchange (NASDAQ, NYSE, NYSEMKT)
  from: string; // first date YYYY-MM-DD
  to: string;   // last date YYYY-MM-DD
  a: boolean;   // active (true) or delisted (false)
}

export interface Manifest {
  tickers: ManifestTicker[];
  updated: string;
}

export type Timeframe = 'daily' | 'weekly' | 'monthly';
