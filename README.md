# Finance & Coding Practice

Roman Cortez · Finance (BBA), Loyola Marymount University '27

Finance projects built with Python, plus general coding practice.

## Company Analysis Tool (`company_analysis/`)

Pulls each company's latest 10-K numbers from the SEC's free EDGAR API, then calculates profitability and credit metrics, runs a simple DCF, scores credit quality, and exports a formatted Excel report. It compares big tech (MSFT, GOOGL, AMZN, META, NVDA) with alternative asset managers (APO, ARES, BX, KKR, OWL).

| Stage | File | What it does |
|---|---|---|
| 1 | `stage1_metrics.py` | Metrics for one company from hand-entered numbers (Papa John's) |
| 2 | `stage2_peers.py` | Loops over a list of companies and prints a comparison table |
| 3 | `stage3_dcf.py` | DCF where you choose the terminal value method (Gordon Growth or EBITDA exit multiple), projection years, growth, discount rate and mid-year convention |
| 4 | `sec_data.py` | Downloads financial data from SEC EDGAR |
| 5 | `stage5_excel.py` | Saves metrics, DCF and credit results to Excel |
| 6 | `stage6_credit.py` | Credit scorecard from leverage and interest coverage |
| All | `run_analysis.py` | Runs everything end to end |

Shared formulas live in `metrics.py`. A sample report is in `company_analysis/output/`.

### Run it

```bash
python -m venv env
source env/Scripts/activate   # Windows Git Bash (macOS/Linux: source env/bin/activate)
pip install -r requirements.txt
cd company_analysis
python run_analysis.py
```

### Limitations

- Companies label numbers differently in SEC filings, so the tool tries several labels and records any estimates on the Excel `Notes` sheet.
- Asset managers consolidate funds and insurance businesses (e.g. Apollo/Athene, KKR/Global Atlantic), so their leverage and margins aren't comparable to operating companies.
- The DCF starts from the latest year's free cash flow, so heavy current investment (like AI data-center capex) lowers the result.

## Other folders

- `loop/` — loop practice
