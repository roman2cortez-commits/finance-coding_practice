# Run the full company analysis tool:
#   1. Ask for DCF assumptions
#   2. Download each company's latest 10-K numbers from the SEC (Stage 4)
#   3. Calculate metrics (Stages 1-2), DCF values (Stage 3) and credit ratings (Stage 6)
#   4. Print a summary and save everything to Excel (Stage 5)

import os

from metrics import all_metrics, fmt
from sec_data import ticker_to_cik, load_company
from stage3_dcf import ask_assumptions, dcf, describe
from stage6_credit import credit_rating

GROUPS = {
    "Big tech": ["MSFT", "GOOGL", "AMZN", "META", "NVDA"],
    "Asset managers": ["APO", "ARES", "BX", "KKR", "OWL"],
}

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output", "company_analysis.xlsx")


def main():
    assumptions = ask_assumptions()

    print("\nDownloading data from the SEC...")
    cik_lookup = ticker_to_cik()
    companies = []
    for group, tickers in GROUPS.items():
        for ticker in tickers:
            print(f"  {ticker}")
            company = load_company(ticker, cik_lookup)
            company["group"] = group
            companies.append(company)

    dcf_results = {}
    for c in companies:
        dcf_results[c["ticker"]] = dcf(c, assumptions)

    print("\nDCF: " + describe(assumptions))
    print(f"\n{'Ticker':<7}{'Group':<16}{'Rev growth':>11}{'EBITDA mgn':>11}"
          f"{'Debt/EBITDA':>12}{'Value/share':>13}  Credit")
    for c in companies:
        m = all_metrics(c)
        result = dcf_results[c["ticker"]]
        per_share = "n/a"
        if result and result["value_per_share"] is not None:
            per_share = f"${result['value_per_share']:,.2f}"
        rating, score = credit_rating(c)
        print(f"{c['ticker']:<7}{c['group']:<16}{fmt(m['Revenue growth'], 'pct'):>11}"
              f"{fmt(m['EBITDA margin'], 'pct'):>11}{fmt(m['Debt / EBITDA'], 'x'):>12}"
              f"{per_share:>13}  {rating}")

    save_excel(companies, dcf_results, assumptions)


def save_excel(companies, dcf_results, assumptions):
    try:
        from stage5_excel import save_report
    except ModuleNotFoundError:
        print("\nCouldn't save the Excel report: the openpyxl package isn't installed for")
        print("the Python you're using. Fix it by running:  python -m pip install openpyxl")
        return
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    try:
        save_report(companies, dcf_results, assumptions, OUTPUT_FILE)
    except PermissionError:
        print("\nCouldn't save the Excel report because it's open in Excel.")
        print("Close company_analysis.xlsx in Excel, then run the program again.")
        return
    print(f"\nSaved Excel report: {OUTPUT_FILE}")
    print("Note: asset managers' numbers include consolidated funds - see the Notes sheet.")


if __name__ == "__main__":
    main()
