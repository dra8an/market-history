from __future__ import annotations

"""
Step 2: Download historical OHLCV data for each ticker via yfinance.

Reads the ticker list from step 01, downloads max history for each,
and saves as compact per-ticker JSON files.

Uses yfinance batch download for efficiency.
"""

import os
import csv
import json
import time
from datetime import datetime

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")
TICKERS_CSV = os.path.join(RAW_DIR, "tickers.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data", "tickers")
PROGRESS_FILE = os.path.join(RAW_DIR, "download_progress.json")

# How many tickers to download per yfinance batch call
BATCH_SIZE = 50
DELAY_BETWEEN_BATCHES = 1.0  # seconds


def load_tickers() -> list[dict]:
    tickers = []
    with open(TICKERS_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tickers.append(row)
    return tickers


def load_progress() -> set:
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_progress(done: set):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(list(done), f)


def download_ticker_data(symbol: str) -> dict | None:
    """Download max historical data for a single ticker."""
    import yfinance as yf

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="max")

        if hist.empty:
            return None

        rows = []
        for idx, row in hist.iterrows():
            ts = int(idx.timestamp())
            o = round(float(row["Open"]), 6)
            h = round(float(row["High"]), 6)
            l = round(float(row["Low"]), 6)
            c = round(float(row["Close"]), 6)
            v = int(row["Volume"])
            rows.append([ts, o, h, l, c, v])

        if not rows:
            return None

        rows.sort(key=lambda r: r[0])
        return {"symbol": symbol, "data": rows}

    except Exception:
        return None


def download_batch(symbols: list[str]) -> dict[str, dict]:
    """Download historical data for a batch of tickers using yfinance."""
    import yfinance as yf

    results = {}
    try:
        data = yf.download(
            symbols,
            period="max",
            group_by="ticker",
            auto_adjust=True,
            threads=True,
        )

        if data.empty:
            return results

        for symbol in symbols:
            try:
                if len(symbols) == 1:
                    ticker_data = data
                else:
                    ticker_data = data[symbol]

                ticker_data = ticker_data.dropna(subset=["Open", "Close"])
                if ticker_data.empty:
                    continue

                rows = []
                for idx, row in ticker_data.iterrows():
                    ts = int(idx.timestamp())
                    o = round(float(row["Open"]), 6)
                    h = round(float(row["High"]), 6)
                    l = round(float(row["Low"]), 6)
                    c = round(float(row["Close"]), 6)
                    v = int(row["Volume"]) if not str(row["Volume"]) == "nan" else 0
                    rows.append([ts, o, h, l, c, v])

                if rows:
                    rows.sort(key=lambda r: r[0])
                    results[symbol] = {"symbol": symbol, "data": rows}
            except Exception:
                continue

    except Exception as e:
        print(f"  Batch download error: {e}")
        # Fallback: try one by one
        for symbol in symbols:
            result = download_ticker_data(symbol)
            if result:
                results[symbol] = result
            time.sleep(0.2)

    return results


def download_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    tickers = load_tickers()
    done = load_progress()

    # Filter out already-done tickers
    remaining = [t for t in tickers if t["symbol"] not in done]
    print(f"[02] {len(tickers)} total tickers, {len(done)} already done, {len(remaining)} remaining")

    if not remaining:
        print("[02] All tickers already downloaded.")
        return load_tickers()

    total_new = 0
    errors = 0

    for i in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[i:i + BATCH_SIZE]
        symbols = [t["symbol"] for t in batch]

        print(f"[02] Batch {i // BATCH_SIZE + 1}/{(len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE}: {symbols[0]}...{symbols[-1]} ({len(symbols)} tickers)")

        results = download_batch(symbols)

        for symbol in symbols:
            if symbol in results:
                ticker_data = results[symbol]
                out_path = os.path.join(OUTPUT_DIR, f"{symbol}.json")
                with open(out_path, "w") as f:
                    json.dump(ticker_data, f, separators=(",", ":"))
                total_new += 1
            else:
                errors += 1

            done.add(symbol)

        # Save progress every batch
        save_progress(done)

        if i + BATCH_SIZE < len(remaining):
            time.sleep(DELAY_BETWEEN_BATCHES)

    print(f"[02] Downloaded {total_new} new tickers ({errors} failed/empty)")
    return tickers


if __name__ == "__main__":
    download_all()
