# Project Status

## Overview
Historical US Stock Data Viewer — static web app for OHLCV stock data with multi-stock comparison and date range filtering.

## Implementation Progress

| Step | Description | Status |
|------|-------------|--------|
| 1 | Scaffold React + Vite project | Done |
| 2 | Define TypeScript types | Done |
| 3 | Build core hooks (useManifest, useTickerData) | Done |
| 4 | Build aggregation + format utilities | Done |
| 5 | Build React components (SearchBar, StockChart, TimeframeSelector, StockInfo, App) | Done |
| 6 | Python data pipeline (NASDAQ FTP ticker list, yfinance OHLCV, manifest) | Done |
| 7 | Integration testing | Done — app loads, search works, charts render, timeframes toggle |
| 8 | Multi-stock comparison (up to 4 tickers, LineSeries with % normalization) | Done |
| 9 | Date range picker (presets + custom date inputs, gain calculation) | Done |
| 10 | Dual-mode StockChart (candlestick for single, LineSeries for comparison) | Done |

## Pipeline Results
- **11,387 tickers** downloaded successfully
- **~500 tickers** failed (warrants/rights with invalid yfinance symbols)
- **manifest.json**: 1.3 MB, 11,387 entries
- **Total data**: ~1.7 GB in `public/data/tickers/`
- **Pipeline runtime**: ~60 minutes

## Frontend Components
| Component | File | Description |
|-----------|------|-------------|
| SearchBar | `src/components/SearchBar.tsx` | Autocomplete search, multi-select (max 4), grays out selected |
| StockChart | `src/components/StockChart.tsx` | Dual-mode: candlestick+volume (single) or LineSeries with % (comparison) |
| StockInfo | `src/components/StockInfo.tsx` | Single-stock details with optional range gain |
| ComparisonInfo | `src/components/ComparisonInfo.tsx` | Color-coded ticker list with prices, % gains, remove buttons |
| DateRangePicker | `src/components/DateRangePicker.tsx` | Preset buttons (1M/3M/6M/1Y/5Y/All) + custom date inputs |
| TimeframeSelector | `src/components/TimeframeSelector.tsx` | Daily/Weekly/Monthly toggle |

## Known Issues
- Prices are split-adjusted (Yahoo Finance always returns split-adjusted OHLC) — UI labels this clearly
- Pipeline script filenames still reference "stooq" for compatibility (original plan used Stooq, switched to NASDAQ FTP + yfinance due to Stooq CAPTCHA)
