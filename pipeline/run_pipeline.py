"""
Pipeline orchestrator: runs steps 01-04 in order.

Usage:
  python run_pipeline.py              # Run all steps
  python run_pipeline.py --skip-download  # Skip download (use existing ZIP)
  python run_pipeline.py --skip-yfinance  # Skip yfinance gap-fill
"""

import sys
import time


def main():
    args = sys.argv[1:]
    skip_download = "--skip-download" in args
    skip_yfinance = "--skip-yfinance" in args

    start = time.time()
    print("=" * 60)
    print("Market History Data Pipeline")
    print("=" * 60)

    # Step 1: Download
    if skip_download:
        print("\n[01] Skipping download (--skip-download)")
    else:
        print("\n--- Step 1: Download Stooq Data ---")
        from pipeline_step_01 import download
        success = download()
        if not success:
            print("\n[!] Download failed. Place the ZIP manually and re-run with --skip-download")
            print("[!] Or re-run to retry the download.")
            sys.exit(1)

    # Step 2: Parse
    print("\n--- Step 2: Parse Stooq CSV Files ---")
    from pipeline_step_02 import parse_all
    parsed_tickers = parse_all()
    if not parsed_tickers:
        print("[!] No tickers parsed. Check that the Stooq data was extracted correctly.")
        sys.exit(1)

    # Step 3: Fill gaps (optional)
    if skip_yfinance:
        print("\n[03] Skipping yfinance gap-fill (--skip-yfinance)")
    else:
        print("\n--- Step 3: Fill Gaps via yfinance ---")
        from pipeline_step_03 import fill_gaps
        fill_gaps(parsed_tickers)

    # Step 4: Generate manifest
    print("\n--- Step 4: Generate Manifest ---")
    from pipeline_step_04 import generate_manifest
    generate_manifest(parsed_tickers)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"Pipeline complete in {elapsed:.1f}s")
    print("=" * 60)


# Allow importing step modules by their filenames
# (they use numeric prefixes which aren't valid Python identifiers)
if __name__ == "__main__":
    import importlib.util
    import os

    pipeline_dir = os.path.dirname(os.path.abspath(__file__))

    # Load step modules with clean names
    for step_num, module_name in [
        ("01", "pipeline_step_01"),
        ("02", "pipeline_step_02"),
        ("03", "pipeline_step_03"),
        ("04", "pipeline_step_04"),
    ]:
        filepath = os.path.join(pipeline_dir, f"{step_num}_{'download_stooq' if step_num == '01' else 'parse_stooq' if step_num == '02' else 'fill_gaps_yfinance' if step_num == '03' else 'generate_manifest'}.py")
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

    main()
