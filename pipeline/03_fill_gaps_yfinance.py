from __future__ import annotations

"""
Step 3: Fill gaps in ticker data using yfinance.

For each parsed ticker, checks if yfinance has more recent data
and appends any missing days. Rate-limited to avoid API throttling.

This step is optional/skippable — Stooq data alone is sufficient for MVP.
"""

import os
import json
import time
from datetime import datetime, timedelta

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data", "tickers")
DELAY = 0.2  # seconds between yfinance requests


def fill_gaps(tickers: list[dict] | None = None):
    try:
        import yfinance as yf
    except ImportError:
        print("[03] yfinance not installed, skipping gap-fill.")
        return

    if tickers is None:
        # Load from existing files
        tickers = []
        if os.path.exists(OUTPUT_DIR):
            for f in os.listdir(OUTPUT_DIR):
                if f.endswith(".json"):
                    tickers.append({"symbol": f.replace(".json", "")})

    if not tickers:
        print("[03] No tickers to process.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    updated = 0
    errors = 0

    print(f"[03] Checking {len(tickers)} tickers for recent data gaps...")

    for i, t in enumerate(tickers):
        symbol = t["symbol"]
        filepath = os.path.join(OUTPUT_DIR, f"{symbol}.json")

        if not os.path.exists(filepath):
            continue

        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            if not data["data"]:
                continue

            last_ts = data["data"][-1][0]
            last_date = datetime.utcfromtimestamp(last_ts)

            # Skip if data is recent enough (within 3 days)
            if (datetime.now() - last_date).days <= 3:
                continue

            # Fetch from yfinance
            start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start, end=today)

            if hist.empty:
                continue

            new_rows = []
            for idx, row in hist.iterrows():
                ts = int(idx.timestamp())
                o = round(float(row["Open"]), 6)
                h = round(float(row["High"]), 6)
                l = round(float(row["Low"]), 6)
                c = round(float(row["Close"]), 6)
                v = int(row["Volume"])
                new_rows.append([ts, o, h, l, c, v])

            if new_rows:
                data["data"].extend(new_rows)
                data["data"].sort(key=lambda r: r[0])

                with open(filepath, "w") as f:
                    json.dump(data, f, separators=(",", ":"))

                updated += 1

            time.sleep(DELAY)

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  Error on {symbol}: {e}")

        if (i + 1) % 500 == 0:
            print(f"[03] Progress: {i + 1}/{len(tickers)} ({updated} updated, {errors} errors)")

    print(f"[03] Gap-fill complete: {updated} updated, {errors} errors")


if __name__ == "__main__":
    fill_gaps()
