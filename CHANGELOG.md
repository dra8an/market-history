# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Project planning documents (PROJECT-PLAN, PROJECT-STATUS, NEXT-STEPS, MASTER, ARCHITECTURE)
- React + Vite + TypeScript scaffold with Tailwind CSS v4
- TypeScript interfaces (TickerData, Manifest, Timeframe)
- `useManifest` hook — loads manifest.json, provides client-side ticker search
- `useTickerData` hook — lazy-fetches per-ticker JSON with AbortController and LRU cache
- `aggregation.ts` — daily to weekly/monthly OHLCV aggregation
- `format.ts` — price, volume, date, and change formatting helpers
- `SearchBar` component — debounced autocomplete with keyboard navigation
- `StockChart` component — Lightweight Charts v5 candlestick + volume histogram
- `TimeframeSelector` component — daily/weekly/monthly toggle
- `StockInfo` component — symbol, name, exchange, date range, active/delisted badge, day change, all-time return
- `App.tsx` — full layout wiring all components together
- Python data pipeline: NASDAQ FTP ticker list download, yfinance batch OHLCV download, manifest generation
- Resumable pipeline with progress tracking (download_progress.json)
- **Multi-stock comparison** — compare up to 4 stocks on the same chart with percentage-normalized LineSeries
- `useMultiTickerData` hook — 4 fixed `useTickerData` calls for parallel multi-ticker data loading
- `DateRangePicker` component — preset buttons (1M/3M/6M/1Y/5Y/All) + custom date inputs
- `ComparisonInfo` component — color-coded ticker list with prices, % gains, and remove buttons
- `DateRange` interface and `COMPARISON_COLORS` constant in types
- `dateRange.ts` utility — `filterByDateRange()` and `calculateGain()` functions
- Dual-mode `StockChart` — single mode (candlestick + volume) and comparison mode (LineSeries with % normalization)
- Date range gain display in `StockInfo` ("Range: +X.XX%")

### Changed
- Replaced Stooq bulk download with NASDAQ FTP + yfinance (Stooq requires CAPTCHA)
- StockInfo now shows labeled "Day:" change and "All-time:" return instead of unlabeled single change
- Price display labeled as "(split-adj.)" since Yahoo Finance returns split-adjusted OHLC
- `App.tsx` refactored from single `selectedTicker` state to array-based `tickers` state (max 4)
- `SearchBar` accepts `selectedSymbols` and `maxReached` props — grays out already-selected tickers, disables input at 4
- `StockChart` refactored to support mode switching with series lifecycle management (add/remove on mode change)
