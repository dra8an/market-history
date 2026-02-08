from __future__ import annotations

"""
Step 4: Generate manifest.json from parsed ticker files.

Scans all ticker JSON files and builds a manifest with:
- symbol, name, exchange, date range, active/delisted status

Attempts to get company names from yfinance (with caching).
Falls back to symbol as name if yfinance is unavailable.
"""

import os
import json
from datetime import datetime, timedelta

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data", "tickers")
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "..", "public", "data", "manifest.json")
NAME_CACHE_PATH = os.path.join(os.path.dirname(__file__), "raw", "name_cache.json")

# Rough exchange detection from Stooq directory paths (stored during parse)
# If not available, default to "US"
EXCHANGE_HINTS_PATH = os.path.join(os.path.dirname(__file__), "raw", "exchange_hints.json")


def load_name_cache() -> dict:
    if os.path.exists(NAME_CACHE_PATH):
        with open(NAME_CACHE_PATH, "r") as f:
            return json.load(f)
    return {}


def save_name_cache(cache: dict):
    os.makedirs(os.path.dirname(NAME_CACHE_PATH), exist_ok=True)
    with open(NAME_CACHE_PATH, "w") as f:
        json.dump(cache, f, separators=(",", ":"))


def generate_manifest(parsed_tickers: list[dict] | None = None):
    # Build exchange hints from parsed tickers if available
    exchange_hints = {}
    if parsed_tickers:
        for t in parsed_tickers:
            exchange_hints[t["symbol"]] = t.get("exchange", "US")

    # Load name cache
    name_cache = load_name_cache()

    # Scan all ticker JSON files
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

            # Get exchange
            exchange = exchange_hints.get(symbol, "US")

            # Get name from cache or use symbol
            name = name_cache.get(symbol, symbol)

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

    # Sort by symbol
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

    # Attempt to fetch names via yfinance (optional, slow)
    unknown_names = [t for t in tickers if t["n"] == t["s"]]
    if unknown_names:
        print(f"[04] {len(unknown_names)} tickers missing names.")
        print("[04] Run with --fetch-names to fetch from yfinance (slow).")

    return manifest


def fetch_names():
    """Fetch company names from yfinance and update cache + manifest."""
    try:
        import yfinance as yf
    except ImportError:
        print("[04] yfinance not installed, skipping name fetch.")
        return

    name_cache = load_name_cache()

    if not os.path.exists(MANIFEST_PATH):
        print("[04] No manifest found. Run generate_manifest first.")
        return

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    updated = 0
    import time

    for i, t in enumerate(manifest["tickers"]):
        symbol = t["s"]
        if symbol in name_cache and name_cache[symbol] != symbol:
            t["n"] = name_cache[symbol]
            continue

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            name = info.get("shortName") or info.get("longName") or symbol
            name_cache[symbol] = name
            t["n"] = name
            updated += 1
            time.sleep(0.2)
        except Exception:
            name_cache[symbol] = symbol

        if (i + 1) % 100 == 0:
            print(f"[04] Name fetch progress: {i + 1}/{len(manifest['tickers'])} ({updated} fetched)")
            save_name_cache(name_cache)

    save_name_cache(name_cache)

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, separators=(",", ":"))

    print(f"[04] Updated {updated} ticker names.")


if __name__ == "__main__":
    import sys

    if "--fetch-names" in sys.argv:
        fetch_names()
    else:
        generate_manifest()
