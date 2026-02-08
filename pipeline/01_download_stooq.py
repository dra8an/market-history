"""
Step 1: Download and extract Stooq US daily data.

Downloads the bulk daily US stock data zip from Stooq.
Note: Stooq may require manual CAPTCHA - if download fails,
manually download from https://stooq.com/db/d/?b=d_us_txt
and place the zip in pipeline/raw/stooq/d_us_txt.zip
"""

import os
import zipfile
import requests

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw", "stooq")
ZIP_PATH = os.path.join(RAW_DIR, "d_us_txt.zip")
EXTRACT_DIR = os.path.join(RAW_DIR, "extracted")
URL = "https://stooq.com/db/d/?b=d_us_txt"


def download():
    os.makedirs(RAW_DIR, exist_ok=True)

    if os.path.exists(ZIP_PATH):
        print(f"[01] ZIP already exists at {ZIP_PATH}, skipping download.")
    else:
        print(f"[01] Downloading Stooq US daily data...")
        try:
            resp = requests.get(URL, stream=True, timeout=120, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            })
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            if "text/html" in content_type:
                print("[01] WARNING: Got HTML response instead of ZIP.")
                print("[01] Stooq likely requires CAPTCHA. Please download manually:")
                print(f"[01]   URL: {URL}")
                print(f"[01]   Save to: {ZIP_PATH}")
                return False

            with open(ZIP_PATH, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            size_mb = os.path.getsize(ZIP_PATH) / 1024 / 1024
            print(f"[01] Downloaded {size_mb:.1f} MB")

            # Validate it's actually a ZIP (should be >50MB)
            if size_mb < 1:
                os.remove(ZIP_PATH)
                print("[01] WARNING: Downloaded file is too small — likely not a valid ZIP.")
                print("[01] Stooq likely requires CAPTCHA. Please download manually:")
                print(f"[01]   URL: {URL}")
                print(f"[01]   Save to: {ZIP_PATH}")
                return False
        except Exception as e:
            print(f"[01] Download failed: {e}")
            print(f"[01] Please download manually from {URL}")
            print(f"[01] Save to: {ZIP_PATH}")
            return False

    # Extract
    if os.path.exists(EXTRACT_DIR) and os.listdir(EXTRACT_DIR):
        print(f"[01] Already extracted to {EXTRACT_DIR}, skipping.")
        return True

    print(f"[01] Extracting ZIP...")
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(EXTRACT_DIR)

    print(f"[01] Extraction complete.")
    return True


if __name__ == "__main__":
    download()
