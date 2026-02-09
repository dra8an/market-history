from __future__ import annotations

"""
Step 5: Download historical data for curated delisted tickers.

Reads delisted_tickers.csv and downloads OHLCV data via yfinance.
Appends successful tickers to tickers.csv so manifest generation picks them up.
Skips tickers that already have data files.

Usage:
  python 05_download_delisted.py
"""

import os
import csv
import json
import time

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")
TICKERS_CSV = os.path.join(RAW_DIR, "tickers.csv")
DELISTED_CSV = os.path.join(os.path.dirname(__file__), "delisted_tickers.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data", "tickers")

DELAY_BETWEEN_TICKERS = 0.5  # seconds


def load_delisted() -> list[dict]:
    tickers = []
    with open(DELISTED_CSV, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tickers.append(row)
    return tickers


def load_existing_tickers_csv() -> dict[str, dict]:
    """Load existing tickers.csv into a dict keyed by symbol."""
    existing = {}
    if os.path.exists(TICKERS_CSV):
        with open(TICKERS_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row["symbol"]] = row
    return existing


def download_ticker(symbol: str) -> dict | None:
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
            v = int(row["Volume"]) if str(row["Volume"]) != "nan" else 0
            rows.append([ts, o, h, l, c, v])

        if not rows:
            return None

        rows.sort(key=lambda r: r[0])
        return {"symbol": symbol, "data": rows}

    except Exception as e:
        print(f"  Error downloading {symbol}: {e}")
        return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    delisted = load_delisted()
    existing_csv = load_existing_tickers_csv()

    # Skip tickers that already have data files
    to_download = []
    already_have = 0
    for t in delisted:
        data_file = os.path.join(OUTPUT_DIR, f"{t['symbol']}.json")
        if os.path.exists(data_file):
            already_have += 1
        else:
            to_download.append(t)

    print(f"[05] {len(delisted)} delisted tickers in list")
    print(f"[05] {already_have} already have data files, {len(to_download)} to download")

    if not to_download:
        print("[05] Nothing to download.")
        return

    success = 0
    failed = 0
    new_csv_rows = []

    for i, t in enumerate(to_download):
        symbol = t["symbol"]
        print(f"[05] ({i + 1}/{len(to_download)}) Downloading {symbol}...", end=" ", flush=True)

        result = download_ticker(symbol)
        if result and len(result["data"]) > 5:  # At least a few data points
            out_path = os.path.join(OUTPUT_DIR, f"{symbol}.json")
            with open(out_path, "w") as f:
                json.dump(result, f, separators=(",", ":"))
            days = len(result["data"])
            print(f"OK ({days} days)")
            success += 1

            # Track for CSV append
            if symbol not in existing_csv:
                new_csv_rows.append(t)
        else:
            print("FAILED (no data)")
            failed += 1

        time.sleep(DELAY_BETWEEN_TICKERS)

    # Append new tickers to tickers.csv
    if new_csv_rows and os.path.exists(TICKERS_CSV):
        with open(TICKERS_CSV, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["symbol", "name", "exchange", "type"])
            writer.writerows(new_csv_rows)
        print(f"[05] Appended {len(new_csv_rows)} new entries to tickers.csv")

    print(f"\n[05] Done: {success} downloaded, {failed} failed")
    print("[05] Run 04_generate_manifest.py to rebuild the manifest.")


if __name__ == "__main__":
    main()
