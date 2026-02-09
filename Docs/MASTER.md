# Master Document Index

## Project
**Historical US Stock Data Viewer** — A static web app displaying historical OHLCV stock data for all US stocks and ETFs (~11,400 tickers).

## Documentation Map

| Document | Location | Purpose |
|----------|----------|---------|
| Master Index | `Docs/MASTER.md` | This file — index of all docs and project locations |
| Project Plan | `Docs/PROJECT-PLAN.md` | Full implementation plan with steps, data formats, and structure |
| Project Status | `Docs/PROJECT-STATUS.md` | Tracks completion status of each implementation step |
| Next Steps | `Docs/NEXT-STEPS.md` | Ordered list of what to work on next |
| Architecture | `Docs/ARCHITECTURE.md` | Tech stack, design decisions, and technical details |
| Changelog | `CHANGELOG.md` | Version history and notable changes (project root) |

## Key Directories

| Path | Description |
|------|-------------|
| `src/` | React + TypeScript frontend source |
| `src/components/` | UI components (SearchBar, StockChart, TimeframeSelector, StockInfo) |
| `src/hooks/` | Custom React hooks (useManifest, useTickerData) |
| `src/utils/` | Utility functions (aggregation, formatting) |
| `src/types/` | Shared TypeScript interfaces |
| `pipeline/` | Python data pipeline scripts (runs locally) |
| `pipeline/raw/` | Downloaded ticker lists and progress tracking (gitignored) |
| `public/data/` | Generated JSON data files served by the app (gitignored) |
| `public/data/tickers/` | Per-ticker OHLCV JSON files (~11,400 files, 1.7GB) |
| `Docs/` | All project documentation |

## Generated Files (gitignored)

- `public/data/manifest.json` — Ticker index (1.3MB) used for search
- `public/data/tickers/*.json` — Per-ticker split-adjusted OHLCV data files
- `pipeline/raw/tickers.csv` — Unified ticker list from NASDAQ FTP
- `pipeline/raw/download_progress.json` — Resumable download progress tracker

## Data Sources

- **Ticker lists**: NASDAQ FTP (`nasdaqtrader.com/dynamic/SymDir/`) — NASDAQ, NYSE, NYSEMKT, NYSEARCA
- **Historical OHLCV**: yfinance (Yahoo Finance) — split-adjusted daily prices
