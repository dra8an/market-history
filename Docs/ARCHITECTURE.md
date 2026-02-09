# Architecture

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.x | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | 7.x | Build tool and dev server |
| Tailwind CSS | 4.x | Utility-first styling (via `@tailwindcss/vite` plugin) |
| Lightweight Charts | 5.x | Candlestick, volume, and line chart rendering |

### Data Pipeline
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.9+ | Pipeline scripting language |
| pandas | latest | Data manipulation |
| yfinance | latest | Historical OHLCV data download |
| requests | latest | HTTP downloads |

### Data Sources
| Source | What it provides |
|--------|-----------------|
| NASDAQ FTP | Ticker lists for NASDAQ, NYSE, NYSEMKT, NYSEARCA (~11,880 symbols) |
| yfinance (Yahoo Finance) | Historical daily OHLCV data (split-adjusted) |

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    Static Web App                         │
│                                                           │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ SearchBar│→ │ StockInfo /   │  │ TimeframeSelector│   │
│  │ (max 4)  │  │ ComparisonInfo│  └──────────────────┘   │
│  └──────────┘  └──────────────┘                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │              DateRangePicker                       │    │
│  │    (1M/3M/6M/1Y/5Y/All presets + custom dates)   │    │
│  └──────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────┐    │
│  │              StockChart (dual mode)                │    │
│  │    Single: candlestick + volume histogram         │    │
│  │    Comparison: LineSeries with % normalization    │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  Hooks: useManifest, useTickerData, useMultiTickerData    │
│  Utils: aggregation, format, dateRange                    │
└──────────────┬──────────────────┬─────────────────────────┘
               │ fetch once       │ fetch on demand (up to 4)
               ▼                  ▼
        manifest.json      tickers/{SYMBOL}.json
        (ticker index)     (per-ticker OHLCV)
```

## Design Decisions

### No Backend
The app is fully static. All data is pre-generated JSON files served from `public/data/`. This means:
- Zero server costs for hosting
- Can be deployed to any static host (Render, Cloudflare Pages, GitHub Pages)
- No API rate limits or authentication needed at runtime

### Compact JSON Format
Per-ticker data uses nested arrays instead of objects to minimize file size:
```json
[unix_timestamp, open, high, low, close, volume]
```
This reduces file sizes by ~60% compared to named-key objects.

### Manifest for Search
A single `manifest.json` file (~1.3MB) is loaded once on app startup. This provides instant client-side search without needing a search API. Contains symbol, name, exchange, date range, and active/delisted status for every ticker.

### Lazy Loading
Ticker data is fetched only when a user selects a ticker. An in-memory LRU cache (last ~50 tickers) prevents re-fetching on navigation back to previously viewed tickers.

### Client-Side Aggregation
Daily → Weekly/Monthly aggregation is done in the browser. This avoids needing separate data files for each timeframe, keeping the data pipeline simple and storage requirements low.

### AbortController for Rapid Switching
When a user quickly switches between tickers, in-flight fetch requests are cancelled via AbortController to prevent stale data from appearing.

### Split-Adjusted Prices
All OHLCV data is split-adjusted, which is the standard for financial charting (used by TradingView, Yahoo Finance, etc.). This means:
- Historical prices are retroactively divided by cumulative split factors
- Charts show smooth price continuity across split dates
- A stock that was $100 and split 2:1 would show $50 for all pre-split dates
- The UI labels prices as "(split-adj.)" and shows both day change and all-time return

### Multi-Stock Comparison Mode
When 2-4 stocks are selected, the chart switches from candlestick to LineSeries with percentage normalization. This is the standard approach used by TradingView, Google Finance, etc.:
- Overlapping candlesticks are unreadable, so LineSeries is used instead
- Percentage normalization (`((close - firstClose) / firstClose) * 100`) allows comparing stocks at different price levels
- Each stock gets a distinct color from `COMPARISON_COLORS`
- The price scale formatter shows `%` instead of dollar values

### Fixed Hook Slots for Multi-Ticker
`useMultiTickerData` calls `useTickerData` exactly 4 times (fixed slots) regardless of how many tickers are selected. This respects React's rules of hooks (no conditional hook calls) while reusing the existing LRU cache. Unused slots receive `null` and return no data.

### Date Range Filtering
Date range filtering is client-side using the already-fetched ticker data. No additional network requests are needed. The `DateRangePicker` uses native `<input type="date">` elements — no external date picker dependency.

## Data Flow

### Pipeline (offline, run locally, ~1 hour)
```
NASDAQ FTP → Ticker lists (nasdaqlisted.txt, otherlisted.txt)
           → Unified tickers.csv (~11,880 symbols)
           → yfinance batch download (50 tickers/batch)
           → Per-ticker JSON files (~11,400 files, 1.7GB)
           → manifest.json (1.3MB)
```

### Runtime (in browser)

**Single-stock mode:**
```
App loads → fetch manifest.json → populate search index
User searches → filter manifest client-side → show results
User selects ticker → fetch tickers/{SYMBOL}.json → cache in memory
User changes timeframe → aggregate cached daily data → re-render chart
User selects date range → filter data client-side → re-render chart + recalculate gains
```

**Comparison mode (2-4 stocks):**
```
User selects 2nd ticker → fetch tickers/{SYMBOL}.json (if not cached)
  → switch to comparison mode (LineSeries)
  → normalize all datasets to % change from first close
  → show ComparisonInfo with per-ticker color, price, and % gain
User selects date range → filter all datasets → recalculate % gains per ticker
User removes ticker → if back to 1, switch to single mode (candlestick)
```

## Chart Implementation
- **Library**: TradingView Lightweight Charts v5
- **Single mode**: Candlestick series (OHLC) + Histogram series (volume) on separate price scales
- **Comparison mode**: LineSeries per ticker with `%` price formatter, no volume
- **Mode switching**: Series are removed and recreated when switching between single/comparison modes
- **Series lifecycle**: Line series tracked in `useRef<Map<string, ISeriesApi<'Line'>>>`, diffed on update to add/remove only changed symbols
- **Resize**: Handled via ResizeObserver for responsive layout
- **Data format**: `{ time: 'YYYY-MM-DD', open, high, low, close }` for candlesticks, `{ time: 'YYYY-MM-DD', value }` for lines

## Component Responsibilities

| Component | Purpose |
|-----------|---------|
| `SearchBar` | Autocomplete search with multi-select support (max 4, grays out already-selected) |
| `StockInfo` | Single-stock details: symbol, name, exchange, prices, day change, all-time return, range gain |
| `ComparisonInfo` | Multi-stock view: color dots, symbols, prices, % gains, remove (x) buttons |
| `StockChart` | Dual-mode chart: candlestick+volume (single) or normalized LineSeries (comparison) |
| `DateRangePicker` | Preset buttons (1M/3M/6M/1Y/5Y/All) + two native date inputs |
| `TimeframeSelector` | Daily/Weekly/Monthly toggle buttons |

## Styling Approach
- Tailwind CSS v4 with the Vite plugin (`@tailwindcss/vite`)
- Dark theme suitable for financial data viewing
- Responsive layout — chart fills available space below header/controls
- Comparison colors: `#2196f3` (blue), `#ff9800` (orange), `#4caf50` (green), `#ab47bc` (purple)
