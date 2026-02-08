# Next Steps

## Immediate
1. **Run the data pipeline** — `cd pipeline && python run_pipeline.py`
   - Download Stooq ZIP (may require manual CAPTCHA download)
   - Parse ~11,800 ticker CSVs into JSON
   - Optionally fill gaps with yfinance
   - Generate manifest.json
2. **Integration testing** — `npm run dev` and verify search, chart rendering, timeframe toggling

## After Data + Testing
3. Fetch company names via yfinance: `cd pipeline && python 04_generate_manifest.py --fetch-names`
4. Deploy to Render or other static host
