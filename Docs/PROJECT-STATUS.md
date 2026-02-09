# Project Status

## Overview
Historical US Stock Data Viewer — static web app for OHLCV stock data.

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

## Pipeline Results
- **11,387 tickers** downloaded successfully
- **~500 tickers** failed (warrants/rights with invalid yfinance symbols)
- **manifest.json**: 1.3 MB, 11,387 entries
- **Total data**: ~1.7 GB in `public/data/tickers/`
- **Pipeline runtime**: ~60 minutes

## Known Issues
- Prices are split-adjusted (Yahoo Finance always returns split-adjusted OHLC) — UI labels this clearly
- Pipeline script filenames still reference "stooq" for compatibility (original plan used Stooq, switched to NASDAQ FTP + yfinance due to Stooq CAPTCHA)
