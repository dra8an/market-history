# Historical US Stock Data Viewer — Implementation Plan

## Context
Build a static (no backend) web app that displays historical OHLCV stock data for all US stocks + ETFs (~11,800 tickers), including delisted ones. Data is sourced from NASDAQ's public ticker lists + yfinance historical data. The React app lazy-loads per-ticker JSON files on demand.

## Project Structure
```
market-history-2/
├── pipeline/                    # Python data pipeline (runs locally)
│   ├── requirements.txt         # pandas, yfinance, requests
│   ├── 01_download_stooq.py     # Download ticker lists from NASDAQ FTP
│   ├── 02_parse_stooq.py        # Download OHLCV via yfinance → per-ticker JSON
│   ├── 03_fill_gaps_yfinance.py # (Legacy, unused)
│   ├── 04_generate_manifest.py  # Build manifest.json (ticker index)
│   └── run_pipeline.py          # Orchestrator: runs steps 01, 02, 04
├── public/
│   └── data/                    # Generated output (gitignored)
│       ├── manifest.json        # ~1.3MB ticker index for search
│       └── tickers/             # ~11,400 JSON files
│           ├── AAPL.json
│           ├── MSFT.json
│           └── ...
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── index.css                # Global styles (Tailwind)
│   ├── types/
│   │   └── index.ts             # Shared TypeScript interfaces and constants
│   ├── hooks/
│   │   ├── useManifest.ts       # Load manifest.json once, provide search
│   │   ├── useTickerData.ts     # Lazy-fetch per-ticker JSON with caching
│   │   └── useMultiTickerData.ts # 4 fixed useTickerData calls for comparison
│   ├── utils/
│   │   ├── aggregation.ts       # Daily → Weekly/Monthly OHLCV aggregation
│   │   ├── format.ts            # Number/date formatting helpers
│   │   └── dateRange.ts         # Date range filtering and gain calculation
│   └── components/
│       ├── SearchBar.tsx         # Autocomplete ticker search (multi-select, max 4)
│       ├── StockChart.tsx        # Dual-mode: candlestick+volume or LineSeries comparison
│       ├── TimeframeSelector.tsx # Daily/Weekly/Monthly toggle
│       ├── StockInfo.tsx         # Symbol, name, exchange, date range, changes, range gain
│       ├── ComparisonInfo.tsx    # Color-coded multi-ticker list with gains and remove
│       └── DateRangePicker.tsx   # Preset buttons + custom date inputs
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .gitignore                   # Includes public/data/
└── CHANGELOG.md
```

## Implementation Steps

### Step 1: Scaffold React + Vite Project
- `npm create vite@latest . -- --template react-ts`
- Install dependencies: `lightweight-charts`, `tailwindcss`, `@tailwindcss/vite`
- Configure Tailwind, basic layout in App.tsx

### Step 2: Define TypeScript Types (`src/types/index.ts`)
```ts
export interface TickerData {
  symbol: string;
  data: number[][]; // [timestamp, open, high, low, close, volume][]
}

export interface ManifestTicker {
  s: string;    // symbol
  n: string;    // name
  e: string;    // exchange (NASDAQ, NYSE, NYSEMKT, NYSEARCA)
  from: string; // first date YYYY-MM-DD
  to: string;   // last date YYYY-MM-DD
  a: boolean;   // active (true) or delisted (false)
}

export interface Manifest {
  tickers: ManifestTicker[];
  updated: string;
}

export type Timeframe = 'daily' | 'weekly' | 'monthly';

export interface DateRange {
  from: string; // YYYY-MM-DD
  to: string;   // YYYY-MM-DD
}

export const COMPARISON_COLORS = ['#2196f3', '#ff9800', '#4caf50', '#ab47bc'];
```

### Step 3: Build Core Hooks
**`useManifest.ts`** — Fetches `/data/manifest.json` once on app load. Provides a `search(query)` function that filters tickers by symbol/name prefix match. Memoized with useMemo.

**`useTickerData.ts`** — Given a ticker symbol, fetches `/data/tickers/{SYMBOL}.json`. Uses AbortController for cancellation on rapid switching. Simple in-memory Map cache (keeps last ~50 tickers to avoid re-fetching).

**`useMultiTickerData.ts`** — Calls `useTickerData` exactly 4 times (fixed slots) to support comparing up to 4 tickers while respecting React's rules of hooks. Returns `{ datasets: Map<string, TickerData>, loading, errors }`. Reuses the existing LRU cache.

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
- Multi-select: accepts `selectedSymbols` and `maxReached` props
- Grays out already-selected tickers in dropdown, disables input at 4

**`StockChart.tsx`**
- Wraps Lightweight Charts v5 with dual-mode rendering
- **Single mode**: candlestick series + volume histogram (original behavior)
- **Comparison mode**: LineSeries per ticker with percentage normalization (`((close - firstClose) / firstClose) * 100`)
- Mode switching: removes and recreates series when mode changes
- Line series tracked in `useRef<Map>`, diffed on update to add/remove only changed symbols
- Handles resize via ResizeObserver

**`TimeframeSelector.tsx`**
- Three buttons: Daily | Weekly | Monthly
- Active state styling

**`StockInfo.tsx`**
- Displays: symbol, company name, exchange
- Date range (e.g., "May 2002 — Feb 2026")
- Active/Delisted badge (green/red)
- Split-adjusted price with label
- Day change (last close vs previous close)
- All-time return (first close vs last close)
- Optional range gain ("Range: +X.XX%") when date range is active

**`ComparisonInfo.tsx`**
- Shown in comparison mode (2-4 tickers) instead of StockInfo
- For each ticker: color dot, symbol, last close price, % gain, remove (x) button
- Colors match the corresponding LineSeries on the chart

**`DateRangePicker.tsx`**
- Preset buttons: 1M, 3M, 6M, 1Y, 5Y, All
- Two native `<input type="date">` with min/max constraints from ticker date ranges
- "All" clears the date range (shows full history)
- Presets calculate from the max date of selected tickers

**`App.tsx`**
- Layout: SearchBar at top, StockInfo/ComparisonInfo + TimeframeSelector, DateRangePicker, StockChart fills remaining space
- State: `tickers: ManifestTicker[]` (max 4), `timeframe`, `dateRange: DateRange | null`
- Mode derived: `tickers.length > 1 ? 'comparison' : 'single'`
- Date range intersection computed across all selected tickers
- Single mode: filters data by date range, shows candlestick chart
- Comparison mode: filters all datasets, builds normalized comparison data

### Step 6: Python Data Pipeline

**`01_download_stooq.py`** (name kept for compatibility)
- Downloads ticker lists from NASDAQ's public FTP:
  - `nasdaqlisted.txt` — NASDAQ-listed symbols
  - `otherlisted.txt` — NYSE, NYSEMKT, NYSEARCA, BATS symbols
- Parses pipe-delimited format, filters test issues and special characters
- Outputs unified `pipeline/raw/tickers.csv` with symbol, name, exchange, type
- ~11,880 tickers total

**`02_parse_stooq.py`** (name kept for compatibility)
- Reads ticker list from step 01
- Downloads max historical OHLCV for each ticker via yfinance
- Uses batch download (`yf.download()`) in groups of 50 for efficiency
- Falls back to single-ticker download on batch errors
- Saves progress to `pipeline/raw/download_progress.json` (resumable)
- Outputs compact per-ticker JSON to `public/data/tickers/{SYMBOL}.json`
- ~1 hour for full run, ~11,400 successful downloads (~500 fail — warrants/rights)
- **Note**: Prices are split-adjusted (Yahoo Finance always returns split-adjusted OHLC)

**`04_generate_manifest.py`**
- Scans all generated ticker JSON files
- Reads names/exchanges from `pipeline/raw/tickers.csv`
- Determines active/delisted by checking if last data is within 30 days
- Outputs `public/data/manifest.json`

**`run_pipeline.py`**
- Runs steps 01, 02, 04 in order
- Flags: `--skip-download` to reuse existing ticker list
- Handles errors per-ticker gracefully (skip and continue)

### Step 7: Integration Testing
1. Run pipeline: `cd pipeline && python run_pipeline.py`
2. Verify output: check `public/data/manifest.json` exists and has entries
3. Run React dev server: `npm run dev`
4. Test: search for AAPL, verify chart loads, toggle timeframes

## Data Format Details

**Per-ticker JSON** (e.g., `AAPL.json`, ~150KB):
```json
{
  "symbol": "AAPL",
  "data": [
    [345427200, 0.51, 0.52, 0.49, 0.51, 117258400],
    [345513600, 0.51, 0.53, 0.50, 0.52, 43971200]
  ]
}
```
Each row: `[unix_timestamp_seconds, open, high, low, close, volume]`
Prices are split-adjusted (standard for financial charting).

**manifest.json** (~1.3MB):
```json
{
  "tickers": [
    {"s": "AAPL", "n": "Apple Inc. - Common Stock", "e": "NASDAQ", "from": "1980-12-12", "to": "2026-02-07", "a": true},
    {"s": "NFLX", "n": "Netflix, Inc. - Common Stock", "e": "NASDAQ", "from": "2002-05-23", "to": "2026-02-07", "a": true}
  ],
  "updated": "2026-02-09"
}
```

## Key Library Versions
- **lightweight-charts**: v5.x (`chart.addSeries(CandlestickSeries, opts)` API)
- **React**: 19.x
- **Vite**: 6.x
- **Tailwind CSS**: v4.x (using `@tailwindcss/vite` plugin)
- **Python**: 3.9+ with pandas, yfinance, requests

## Data Sources
- **Ticker lists**: NASDAQ FTP (`nasdaqtrader.com/dynamic/SymDir/`)
- **Historical OHLCV**: yfinance (Yahoo Finance, split-adjusted)

## Deployment (Future)
- React app on Render static site (build: `npm run build`, publish: `dist/`)
- Data files: TBD — options include Cloudflare R2, Render with build-time pipeline, or separate static host
- For now: local development only, `public/data/` is gitignored

## Verification
1. `cd pipeline && python run_pipeline.py` — produces `public/data/manifest.json` + `public/data/tickers/*.json`
2. `npm run dev` — opens React app at localhost
3. Search "AAPL" → candlestick chart loads (single mode, unchanged behavior)
4. Toggle Weekly/Monthly → chart re-renders with aggregated data
5. Check StockInfo shows day change and all-time return
6. Search "MSFT" while AAPL shown → switches to line comparison, both normalized to %
7. Add GOOGL, TSLA → 4 lines with distinct colors, gains shown per ticker
8. Try adding 5th → search disabled ("Max 4 tickers selected")
9. Remove a ticker via (x) → if back to 1, returns to candlestick mode
10. Select "1Y" preset → chart zooms to last year, gains recalculate
11. Set custom date range → chart and gains update
12. Combine: 3 stocks + custom date range → all 3 show % gains for that range
13. Toggle weekly/monthly → aggregation works in both modes
