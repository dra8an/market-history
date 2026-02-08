from __future__ import annotations

"""
Step 2: Parse Stooq CSV files into per-ticker JSON files.

Walks the extracted Stooq directory tree and converts each ticker's
CSV data into a compact JSON array format.

Stooq directory structure:
  data/daily/us/nasdaq stocks/*.txt
  data/daily/us/nyse stocks/*.txt
  data/daily/us/nysemkt stocks/*.txt
  data/daily/us/nasdaq etfs/*.txt
  data/daily/us/nyse etfs/*.txt
  data/daily/us/nysemkt etfs/*.txt

Stooq CSV format:
  Date,Open,High,Low,Close,Volume
  (Date is YYYYMMDD integer)

Filename format: aapl.us.txt -> AAPL
"""

import os
import json
import csv
from datetime import datetime

EXTRACT_DIR = os.path.join(os.path.dirname(__file__), "raw", "stooq", "extracted")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data", "tickers")

# Map directory names to exchange codes
EXCHANGE_MAP = {
    "nasdaq stocks": "NASDAQ",
    "nasdaq etfs": "NASDAQ",
    "nyse stocks": "NYSE",
    "nyse etfs": "NYSE",
    "nysemkt stocks": "NYSEMKT",
    "nysemkt etfs": "NYSEMKT",
}

# Track parsed tickers for manifest generation
parsed_tickers = []


def parse_date(date_str: str) -> int:
    """Convert YYYYMMDD string to unix timestamp."""
    dt = datetime.strptime(date_str.strip(), "%Y%m%d")
    return int(dt.timestamp())


def parse_file(filepath: str, symbol: str, exchange: str) -> dict | None:
    """Parse a single Stooq CSV file into ticker data."""
    rows = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = parse_date(row["Date"])
                    o = round(float(row["Open"]), 6)
                    h = round(float(row["High"]), 6)
                    l = round(float(row["Low"]), 6)
                    c = round(float(row["Close"]), 6)
                    v = int(float(row["Volume"]))
                    rows.append([ts, o, h, l, c, v])
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
        return None

    if not rows:
        return None

    # Sort by timestamp
    rows.sort(key=lambda r: r[0])

    return {"symbol": symbol, "data": rows}


def parse_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Find the data directory
    data_dir = None
    for root, dirs, files in os.walk(EXTRACT_DIR):
        if "daily" in dirs:
            data_dir = os.path.join(root, "daily", "us")
            break

    if not data_dir or not os.path.exists(data_dir):
        print(f"[02] ERROR: Could not find Stooq data directory in {EXTRACT_DIR}")
        print(f"[02] Expected structure: .../data/daily/us/")
        return []

    print(f"[02] Found data directory: {data_dir}")

    total = 0
    errors = 0

    for dirname, exchange in EXCHANGE_MAP.items():
        dir_path = os.path.join(data_dir, dirname)
        if not os.path.exists(dir_path):
            print(f"[02] Skipping {dirname} (not found)")
            continue

        files = [f for f in os.listdir(dir_path) if f.endswith(".txt")]
        print(f"[02] Processing {dirname}: {len(files)} files")

        for filename in files:
            # Extract symbol: aapl.us.txt -> AAPL
            symbol = filename.split(".")[0].upper()
            filepath = os.path.join(dir_path, filename)

            ticker_data = parse_file(filepath, symbol, exchange)
            if ticker_data is None:
                errors += 1
                continue

            # Write JSON
            out_path = os.path.join(OUTPUT_DIR, f"{symbol}.json")
            with open(out_path, "w") as f:
                json.dump(ticker_data, f, separators=(",", ":"))

            # Track for manifest
            first_date = datetime.utcfromtimestamp(ticker_data["data"][0][0]).strftime("%Y-%m-%d")
            last_date = datetime.utcfromtimestamp(ticker_data["data"][-1][0]).strftime("%Y-%m-%d")
            parsed_tickers.append({
                "symbol": symbol,
                "exchange": exchange,
                "from": first_date,
                "to": last_date,
                "file": out_path,
            })

            total += 1

    print(f"[02] Parsed {total} tickers ({errors} errors)")
    return parsed_tickers


if __name__ == "__main__":
    parse_all()
