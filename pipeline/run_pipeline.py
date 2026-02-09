"""
Pipeline orchestrator: runs steps 01, 02, 04 in order.

Usage:
  python run_pipeline.py                # Run all steps
  python run_pipeline.py --skip-download  # Skip ticker list download (use existing)

Step 01: Download ticker lists from NASDAQ FTP
Step 02: Download historical OHLCV via yfinance (batched, resumable)
Step 04: Generate manifest.json
"""

import sys
import os
import time
import importlib.util


def load_module(step_num, filename):
    """Load a pipeline step module by filename."""
    pipeline_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(pipeline_dir, filename)
    module_name = f"pipeline_step_{step_num}"
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main():
    args = sys.argv[1:]
    skip_download = "--skip-download" in args

    start = time.time()
    print("=" * 60)
    print("Market History Data Pipeline")
    print("=" * 60)

    # Load modules
    step01 = load_module("01", "01_download_stooq.py")
    step02 = load_module("02", "02_parse_stooq.py")
    step04 = load_module("04", "04_generate_manifest.py")

    # Step 1: Download ticker list
    if skip_download:
        print("\n[01] Skipping ticker list download (--skip-download)")
    else:
        print("\n--- Step 1: Download Ticker Lists ---")
        success = step01.download_ticker_list()
        if not success:
            print("\n[!] Ticker list download failed.")
            sys.exit(1)

    # Step 2: Download historical data via yfinance
    print("\n--- Step 2: Download Historical Data (yfinance) ---")
    step02.download_all()

    # Step 4: Generate manifest
    print("\n--- Step 4: Generate Manifest ---")
    step04.generate_manifest()

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"Pipeline complete in {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
