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
- `StockInfo` component — symbol, name, exchange, date range, active/delisted badge
- `App.tsx` — full layout wiring all components together
- Python data pipeline (01-04 + orchestrator) for Stooq download, parsing, yfinance gap-fill, manifest generation
