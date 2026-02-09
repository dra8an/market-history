from __future__ import annotations

"""
Step 4: Generate manifest.json from parsed ticker files.

Scans all ticker JSON files and builds a manifest with:
- symbol, name, exchange, date range, active/delisted status

Uses the ticker list from step 01 for names and exchange info.
"""

import os
import csv
import json
from datetime import datetime, timedelta

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")
TICKERS_CSV = os.path.join(RAW_DIR, "tickers.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data", "tickers")
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "data", "manifest.json")


def load_ticker_info() -> dict[str, dict]:
    """Load ticker names and exchanges from the CSV produced in step 01."""
    info = {}
    if os.path.exists(TICKERS_CSV):
        with open(TICKERS_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                info[row["symbol"]] = {
                    "name": row["name"],
                    "exchange": row["exchange"],
                }
    return info


def generate_manifest(parsed_tickers: list[dict] | None = None):
    ticker_info = load_ticker_info()

    if not os.path.exists(OUTPUT_DIR):
        print("[04] ERROR: No ticker data directory found.")
        return

    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".json")]
    print(f"[04] Building manifest from {len(files)} ticker files...")

    tickers = []
    for filename in sorted(files):
        symbol = filename.replace(".json", "")
        filepath = os.path.join(OUTPUT_DIR, filename)

        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            if not data.get("data"):
                continue

            first_ts = data["data"][0][0]
            last_ts = data["data"][-1][0]
            first_date = datetime.utcfromtimestamp(first_ts).strftime("%Y-%m-%d")
            last_date = datetime.utcfromtimestamp(last_ts).strftime("%Y-%m-%d")

            # Determine if active: last data within ~30 days of now
            last_dt = datetime.utcfromtimestamp(last_ts)
            active = (datetime.now() - last_dt) < timedelta(days=30)

            # Get name and exchange from ticker list
            info = ticker_info.get(symbol, {})
            name = info.get("name", symbol)
            exchange = info.get("exchange", "US")

            tickers.append({
                "s": symbol,
                "n": name,
                "e": exchange,
                "from": first_date,
                "to": last_date,
                "a": active,
            })
        except Exception as e:
            print(f"  Error reading {filename}: {e}")

    tickers.sort(key=lambda t: t["s"])

    manifest = {
        "tickers": tickers,
        "updated": datetime.now().strftime("%Y-%m-%d"),
    }

    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, separators=(",", ":"))

    size_kb = os.path.getsize(MANIFEST_PATH) / 1024
    print(f"[04] Manifest generated: {len(tickers)} tickers, {size_kb:.0f} KB")

    return manifest


if __name__ == "__main__":
    generate_manifest()
