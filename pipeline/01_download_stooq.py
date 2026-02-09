"""
Step 1: Download ticker lists from NASDAQ and fetch historical data via yfinance.

Sources:
- NASDAQ-listed symbols: ftp.nasdaqtrader.com/symboldirectory/nasdaqlisted.txt
- Other exchange-listed: ftp.nasdaqtrader.com/symboldirectory/otherlisted.txt
- Historical OHLCV data: yfinance

The script:
1. Downloads ticker lists from NASDAQ's public FTP
2. Parses into a unified ticker list with exchange info
3. Saves to pipeline/raw/tickers.csv
"""

import os
import csv
import urllib.request

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")
TICKERS_CSV = os.path.join(RAW_DIR, "tickers.csv")

NASDAQ_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"


def download_ticker_list():
    os.makedirs(RAW_DIR, exist_ok=True)

    if os.path.exists(TICKERS_CSV):
        # Count lines
        with open(TICKERS_CSV) as f:
            count = sum(1 for _ in f) - 1  # minus header
        if count > 1000:
            print(f"[01] Ticker list already exists ({count} tickers), skipping download.")
            return True

    tickers = []

    # Download NASDAQ-listed
    print("[01] Downloading NASDAQ-listed symbols...")
    try:
        req = urllib.request.Request(NASDAQ_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            lines = resp.read().decode("utf-8").strip().split("\n")

        # Format: Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
        # Skip header and footer (last line is timestamp)
        for line in lines[1:]:
            if line.startswith("File Creation Time"):
                break
            fields = line.split("|")
            if len(fields) >= 7 and fields[3] == "N":  # Not a test issue
                symbol = fields[0].strip()
                name = fields[1].strip()
                is_etf = fields[6].strip() == "Y"
                tickers.append({
                    "symbol": symbol,
                    "name": name,
                    "exchange": "NASDAQ",
                    "type": "ETF" if is_etf else "Stock",
                })
        print(f"[01] Found {len(tickers)} NASDAQ symbols")
    except Exception as e:
        print(f"[01] Error downloading NASDAQ list: {e}")

    # Download other-listed (NYSE, NYSEMKT/AMEX, etc.)
    print("[01] Downloading other exchange-listed symbols...")
    other_count = 0
    try:
        req = urllib.request.Request(OTHER_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            lines = resp.read().decode("utf-8").strip().split("\n")

        # Format: ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
        for line in lines[1:]:
            if line.startswith("File Creation Time"):
                break
            fields = line.split("|")
            if len(fields) >= 7 and fields[6].strip() == "N":  # Not a test issue
                symbol = fields[0].strip()
                name = fields[1].strip()
                exchange_code = fields[2].strip()
                is_etf = fields[4].strip() == "Y"

                # Map exchange codes
                exchange_map = {
                    "N": "NYSE",
                    "A": "NYSEMKT",
                    "P": "NYSEARCA",
                    "Z": "BATS",
                    "V": "IEXG",
                }
                exchange = exchange_map.get(exchange_code, exchange_code)

                tickers.append({
                    "symbol": symbol,
                    "name": name,
                    "exchange": exchange,
                    "type": "ETF" if is_etf else "Stock",
                })
                other_count += 1
        print(f"[01] Found {other_count} other-exchange symbols")
    except Exception as e:
        print(f"[01] Error downloading other listings: {e}")

    if not tickers:
        print("[01] ERROR: No tickers downloaded.")
        return False

    # Filter out symbols with special characters (warrants, units, etc.)
    clean_tickers = [t for t in tickers if t["symbol"].isalpha() or t["symbol"].replace(".", "").isalpha()]
    removed = len(tickers) - len(clean_tickers)
    if removed:
        print(f"[01] Filtered out {removed} tickers with special characters")

    # Write CSV
    with open(TICKERS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["symbol", "name", "exchange", "type"])
        writer.writeheader()
        writer.writerows(clean_tickers)

    print(f"[01] Saved {len(clean_tickers)} tickers to {TICKERS_CSV}")
    return True


if __name__ == "__main__":
    download_ticker_list()
