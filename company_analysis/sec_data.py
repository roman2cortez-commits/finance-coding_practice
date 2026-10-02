# Stage 4: Pull real financial data from the SEC's free EDGAR API.
#
# Every public company files its financial statements with the SEC in a
# machine-readable format (XBRL). This file downloads those numbers and turns
# them into the same kind of company dictionary used in Stages 1-3.
#
# The SEC asks every program to identify itself with a name and email.

import json
import time
import urllib.request
from datetime import date

CONTACT = "Roman Cortez rcortez8@lion.lmu.edu"

# Companies don't all use the same label for the same number, so for each
# item we list several possible labels ("tags") and use the first one found.
TAGS = {
    "revenue": ["Revenues",
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "operating_income": ["OperatingIncomeLoss"],
    "pretax_income": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                      "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"],
    "da": ["DepreciationDepletionAndAmortization",
           "DepreciationAmortizationAndOther",
           "DepreciationAndAmortization",
           "DepreciationAmortizationAndAccretionNet",
           "Depreciation"],
    "net_income": ["NetIncomeLoss"],
    "interest_expense": ["InterestExpense",
                         "InterestExpenseNonoperating",
                         "InterestExpenseDebt"],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment",
              "PaymentsToAcquireProductiveAssets",
              "PaymentsToAcquirePropertyPlantAndEquipmentAndIntangibleAssets"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue",
             "Cash",
             "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "total_debt": ["LongTermDebt",
                   "DebtLongtermAndShorttermCombinedAmount",
                   "LongTermDebtNoncurrent",
                   "SeniorNotes",
                   "DebtInstrumentCarryingAmount",
                   "NotesPayable"],
    "shares": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
}

# Balance sheet items are a snapshot on one day; the rest cover a full year.
SNAPSHOT_ITEMS = ["cash", "total_debt"]


def download_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": CONTACT})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    time.sleep(0.2)  # be polite: the SEC allows at most 10 requests per second
    return data


def ticker_to_cik():
    # The SEC identifies companies by a number called a CIK, not the ticker
    data = download_json("https://www.sec.gov/files/company_tickers.json")
    lookup = {}
    for row in data.values():
        lookup[row["ticker"]] = row["cik_str"]
    return lookup


def days_between(start, end):
    return (date.fromisoformat(end) - date.fromisoformat(start)).days


def is_full_year(entry):
    return "start" in entry and 350 <= days_between(entry["start"], entry["end"]) <= 380


def entries_for(facts, tag):
    # All reported values for one tag, in dollars (or shares)
    units = facts.get(tag, {}).get("units", {})
    return units.get("USD") or units.get("shares") or []


def latest_fiscal_year_end(facts):
    # The most recent full-year period the company reported in a 10-K
    ends = [e["end"] for e in entries_for(facts, "NetIncomeLoss")
            if e.get("form") == "10-K" and is_full_year(e)]
    return max(ends) if ends else None


def find_value(facts, item, period_end):
    # Value of one item for the year ending on period_end, in $ millions
    found = []
    for tag in TAGS[item]:
        for entry in entries_for(facts, tag):
            if entry["end"] == period_end and (item in SNAPSHOT_ITEMS or is_full_year(entry)):
                found.append(entry["val"])
                break
        if found and item != "revenue":
            break
    if not found:
        return None
    # Some companies report only a piece of revenue under one tag, so for
    # revenue we take the largest matching tag (the total)
    return max(found) / 1_000_000


def shares_from_cover_page(data):
    # Backup: shares outstanding from the cover page, adding up share classes
    entries = entries_for(data["facts"].get("dei", {}), "EntityCommonStockSharesOutstanding")
    if not entries:
        return None
    latest = max(e["end"] for e in entries)
    return sum(e["val"] for e in entries if e["end"] == latest) / 1_000_000


def prior_year_end(facts, period_end):
    # The end date of the year before, found from the revenue history
    for tag in TAGS["revenue"]:
        best = None
        for entry in entries_for(facts, tag):
            if is_full_year(entry) and 350 <= days_between(entry["end"], period_end) <= 380:
                best = entry["end"]
        if best:
            return best
    return None


def load_company(ticker, cik_lookup):
    cik = cik_lookup[ticker]
    data = download_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
    facts = data["facts"]["us-gaap"]
    period_end = latest_fiscal_year_end(facts)

    company = {"name": data["entityName"], "ticker": ticker,
               "fiscal_year_end": period_end, "missing": []}
    for item in TAGS:
        company[item] = find_value(facts, item, period_end)

    # Fill gaps with reasonable backups, and record what we assumed
    company["notes"] = []
    if company["operating_income"] is None and company["pretax_income"] is not None:
        company["operating_income"] = company["pretax_income"] + (company["interest_expense"] or 0)
        company["notes"].append("operating income estimated as pre-tax income + interest")
    if company["capex"] is None:
        company["capex"] = 0
        company["notes"].append("capex not reported; assumed 0")
    if company["shares"] is None:
        company["shares"] = shares_from_cover_page(data) or None
        if company["shares"]:
            company["notes"].append("shares taken from filing cover page")

    company["missing"] = [item for item in TAGS if company[item] is None]

    previous = prior_year_end(facts, period_end)
    company["prior_year_revenue"] = find_value(facts, "revenue", previous) if previous else None
    return company


if __name__ == "__main__":
    # Quick test: load one company and print what was found
    lookup = ticker_to_cik()
    test = load_company("MSFT", lookup)
    for key, value in test.items():
        print(key, value)
