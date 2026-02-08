# Historical US Stock Data Viewer — Implementation Plan

## Context
Build a static (no backend) web app that displays historical OHLCV stock data for all US stocks + ETFs (~11,800 tickers), including delisted ones. Data is sourced from Stooq bulk downloads + yfinance gap-filling. The React app lazy-loads per-ticker JSON files on demand.

## Project Structure
```
market-history-2/
├── pipeline/                    # Python data pipeline (runs locally)
│   ├── requirements.txt         # pandas, yfinance, requests
│   ├── 01_download_stooq.py     # Download & extract Stooq US daily zip
│   ├── 02_parse_stooq.py        # Parse CSVs → per-ticker JSON files
│   ├── 03_fill_gaps_yfinance.py # Supplement missing data via yfinance
│   ├── 04_generate_manifest.py  # Build manifest.json (ticker index)
│   └── run_pipeline.py          # Orchestrator: runs steps 01-04
├── public/
│   └── data/                    # Generated output (gitignored)
│       ├── manifest.json        # ~500KB ticker index for search
│       └── tickers/             # ~11,800 JSON files
│           ├── AAPL.json
│           ├── MSFT.json
│           └── ...
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── index.css                # Global styles (Tailwind)
│   ├── types/
│   │   └── index.ts             # Shared TypeScript interfaces
│   ├── hooks/
│   │   ├── useManifest.ts       # Load manifest.json once, provide search
│   │   └── useTickerData.ts     # Lazy-fetch per-ticker JSON with caching
│   ├── utils/
│   │   ├── aggregation.ts       # Daily → Weekly/Monthly OHLCV aggregation
│   │   └── format.ts            # Number/date formatting helpers
│   └── components/
│       ├── SearchBar.tsx         # Autocomplete ticker search
│       ├── StockChart.tsx        # Lightweight Charts candlestick + volume
│       ├── TimeframeSelector.tsx # Daily/Weekly/Monthly toggle
│       └── StockInfo.tsx         # Symbol, name, exchange, date range badge
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── .gitignore                   # Includes public/data/
└── README.md
```

## Implementation Steps

### Step 1: Scaffold React + Vite Project
- `npm create vite@latest . -- --template react-ts`
- Install dependencies: `lightweight-charts`, `tailwindcss`, `@tailwindcss/vite`
- Configure Tailwind, basic layout in App.tsx

### Step 2: Define TypeScript Types (`src/types/index.ts`)
```ts
// Per-ticker JSON format: compact arrays for small file size
export interface TickerData {
  symbol: string;
  data: number[][]; // [timestamp, open, high, low, close, volume][]
}

// Manifest entry (short keys for compact JSON)
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
```

### Step 3: Build Core Hooks
**`useManifest.ts`** — Fetches `/data/manifest.json` once on app load. Provides a `search(query)` function that filters tickers by symbol/name prefix match. Memoized with useMemo.

**`useTickerData.ts`** — Given a ticker symbol, fetches `/data/tickers/{SYMBOL}.json`. Uses AbortController for cancellation on rapid switching. Simple in-memory Map cache (keeps last ~50 tickers to avoid re-fetching).

### Step 4: Build Aggregation Utility (`src/utils/aggregation.ts`)
- Takes daily OHLCV array, returns weekly or monthly aggregated array
- Weekly: group by ISO week (Mon-Fri), aggregate OHLCV (open=first, high=max, low=min, close=last, volume=sum)
- Monthly: group by year-month, same aggregation logic

### Step 5: Build React Components

**`SearchBar.tsx`**
- Text input with dropdown of matching tickers (from useManifest search)
- Shows symbol, name, exchange, active/delisted badge
- Debounced input (150ms)
- Keyboard navigation (arrow keys + enter)

**`StockChart.tsx`**
- Wraps Lightweight Charts v5
- Creates chart with `createChart()`, adds candlestick series via `chart.addSeries(CandlestickSeries)`
- Separate volume histogram series on secondary price scale
- Handles resize via ResizeObserver
- Updates data when ticker or timeframe changes
- Formats candlestick data as `{ time: 'YYYY-MM-DD', open, high, low, close }`

**`TimeframeSelector.tsx`**
- Three buttons: Daily | Weekly | Monthly
- Active state styling
- Calls parent callback on change

**`StockInfo.tsx`**
- Displays: symbol, company name, exchange
- Date range (e.g., "Dec 1980 — Feb 2026")
- Active/Delisted badge (green/red)
- Current price + change from last close

**`App.tsx`**
- Layout: SearchBar at top, StockInfo + TimeframeSelector below, StockChart fills remaining space
- State: selectedTicker, timeframe
- Default: show AAPL or empty state with instructions

### Step 6: Python Data Pipeline

**`01_download_stooq.py`**
- Downloads US daily data zip from `https://stooq.com/db/d/?b=d_us_txt`
- Note: Stooq may require manual CAPTCHA — script will check if file exists and skip if already downloaded
- Extracts to `pipeline/raw/stooq/`

**`02_parse_stooq.py`**
- Walks the Stooq directory tree: `data/daily/us/nasdaq stocks/`, `data/daily/us/nyse stocks/`, etc.
- Stooq CSV format: `Date,Open,High,Low,Close,Volume` (Date is YYYYMMDD integer)
- Parses each `.txt` file, converts to compact JSON array format
- Outputs to `public/data/tickers/{SYMBOL}.json`
- Ticker symbol extracted from filename (e.g., `aapl.us.txt` → `AAPL`)
- Determines exchange from directory path

**`03_fill_gaps_yfinance.py`**
- Reads manifest of parsed Stooq tickers
- For each ticker, checks if yfinance has more recent data
- Appends any missing recent days
- Rate-limited: ~0.2s delay between requests
- Optional/skippable — Stooq data alone is sufficient for MVP

**`04_generate_manifest.py`**
- Scans all generated ticker JSON files
- For each: extracts symbol, date range, determines active/delisted
- Attempts to get company name from yfinance (cached) or uses symbol as fallback
- Outputs `public/data/manifest.json`

**`run_pipeline.py`**
- Runs steps in order, with progress logging
- Handles errors per-ticker gracefully (skip and continue)

### Step 7: Integration Testing
1. Run pipeline: `cd pipeline && python run_pipeline.py`
2. Verify output: check `public/data/manifest.json` exists and has entries, spot-check a few ticker JSONs
3. Run React dev server: `npm run dev`
4. Test: search for AAPL, verify chart loads, toggle timeframes, search for a delisted ticker

## Data Format Details

**Per-ticker JSON** (e.g., `AAPL.json`, ~150KB):
```json
{
  "symbol": "AAPL",
  "data": [
    [345427200, 0.51, 0.52, 0.49, 0.51, 117258400],
    [345513600, 0.51, 0.53, 0.50, 0.52, 43971200],
    ...
  ]
}
```
Each row: `[unix_timestamp_seconds, open, high, low, close, volume]`

**manifest.json** (~500KB):
```json
{
  "tickers": [
    {"s": "AAPL", "n": "Apple Inc", "e": "NASDAQ", "from": "1984-09-07", "to": "2026-02-07", "a": true},
    {"s": "ENRNQ", "n": "Enron Corp", "e": "NYSE", "from": "1983-01-03", "to": "2007-03-26", "a": false}
  ],
  "updated": "2026-02-07"
}
```

## Key Library Versions
- **lightweight-charts**: v5.x (`chart.addSeries(CandlestickSeries, opts)` API)
- **React**: 19.x
- **Vite**: 6.x
- **Tailwind CSS**: v4.x (using `@tailwindcss/vite` plugin)
- **Python**: 3.10+ with pandas, yfinance, requests

## Deployment (Future)
- React app on Render static site (build: `npm run build`, publish: `dist/`)
- Data files: TBD — options include Cloudflare R2, Render with build-time pipeline, or separate static host
- For now: local development only, `public/data/` is gitignored

## Verification
1. `cd pipeline && python run_pipeline.py` — should produce `public/data/manifest.json` + `public/data/tickers/*.json`
2. `npm run dev` — opens React app at localhost
3. Search "AAPL" → chart loads with candlestick + volume data
4. Toggle Weekly/Monthly → chart re-renders with aggregated data
5. Search a delisted ticker → shows with "Delisted" badge
6. Check mobile responsiveness (browser dev tools)
