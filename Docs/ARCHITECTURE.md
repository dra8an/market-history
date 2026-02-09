# Architecture

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.x | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | 6.x | Build tool and dev server |
| Tailwind CSS | 4.x | Utility-first styling (via `@tailwindcss/vite` plugin) |
| Lightweight Charts | 5.x | Candlestick and volume chart rendering |

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
┌─────────────────────────────────────────────────┐
│                  Static Web App                  │
│                                                  │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ SearchBar│→ │ StockInfo  │  │  Timeframe   │  │
│  └──────────┘  └───────────┘  │  Selector    │  │
│                               └──────────────┘  │
│  ┌──────────────────────────────────────────┐   │
│  │            StockChart                     │   │
│  │    (Lightweight Charts candlestick +      │   │
│  │     volume histogram)                     │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  Hooks: useManifest, useTickerData               │
│  Utils: aggregation, format                      │
└──────────────┬──────────────────┬────────────────┘
               │ fetch once       │ fetch on demand
               ▼                  ▼
        manifest.json      tickers/AAPL.json
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
```
App loads → fetch manifest.json → populate search index
User searches → filter manifest client-side → show results
User selects ticker → fetch tickers/{SYMBOL}.json → cache in memory
User changes timeframe → aggregate cached daily data → re-render chart
```

## Chart Implementation
- **Library**: TradingView Lightweight Charts v5
- **Candlestick series**: OHLC data on primary price scale
- **Volume series**: Histogram on secondary (overlay) price scale
- **Resize**: Handled via ResizeObserver for responsive layout
- **Data format**: `{ time: 'YYYY-MM-DD', open, high, low, close }` for candlesticks

## Styling Approach
- Tailwind CSS v4 with the Vite plugin (`@tailwindcss/vite`)
- Dark theme suitable for financial data viewing
- Responsive layout — chart fills available space below header/controls
