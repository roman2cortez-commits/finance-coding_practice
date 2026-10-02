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


def to_date(text):
    return date.fromisoformat(text)


def is_full_year(entry):
    if "start" not in entry:
        return False
    days = (to_date(entry["end"]) - to_date(entry["start"])).days
    return 350 <= days <= 380


def entries_for(facts, tag):
    # All reported values for one tag, in dollars (or shares)
    if tag not in facts:
        return []
    units = facts[tag]["units"]
    if "USD" in units:
        return units["USD"]
    if "shares" in units:
        return units["shares"]
    return []


def latest_fiscal_year_end(facts):
    # The most recent full-year period the company reported in a 10-K
    latest = None
    for entry in entries_for(facts, "NetIncomeLoss"):
        if entry.get("form") == "10-K" and is_full_year(entry):
            if latest is None or entry["end"] > latest:
                latest = entry["end"]
    return latest


def find_value(facts, item, period_end):
    # Find one item's value for the year ending on period_end
    found = []
    for tag in TAGS[item]:
        for entry in entries_for(facts, tag):
            if entry["end"] != period_end:
                continue
            if item in SNAPSHOT_ITEMS or is_full_year(entry):
                found.append((entry["val"], tag))
                break
        if found and item != "revenue":
            return found[0]
    if not found:
        return None, None
    # Some companies report only a piece of revenue under one tag, so for
    # revenue we take the largest of the matching tags (the total)
    return max(found)


def shares_from_cover_page(data):
    # Backup: shares outstanding from the cover page of the latest filing
    cover = data["facts"].get("dei", {})
    entries = entries_for(cover, "EntityCommonStockSharesOutstanding")
    if not entries:
        return None
    latest = max(entry["end"] for entry in entries)
    total = 0
    for entry in entries:
        if entry["end"] == latest:
            total += entry["val"]  # add up share classes (e.g. Class A + B)
    return total


def prior_year_end(facts, period_end):
    # The end date of the year before, found from the revenue history
    target = to_date(period_end)
    best = None
    for tag in TAGS["revenue"]:
        for entry in entries_for(facts, tag):
            if not is_full_year(entry):
                continue
            gap = (target - to_date(entry["end"])).days
            if 350 <= gap <= 380:
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
        value, tag = find_value(facts, item, period_end)
        if value is None:
            company[item] = None
        else:
            company[item] = value / 1_000_000  # convert to millions

    # Fill gaps with reasonable backups, and record what we assumed
    company["notes"] = []
    if company["operating_income"] is None and company["pretax_income"] is not None:
        company["operating_income"] = company["pretax_income"] + (company["interest_expense"] or 0)
        company["notes"].append("operating income estimated as pre-tax income + interest")
    if company["capex"] is None:
        company["capex"] = 0
        company["notes"].append("capex not reported; assumed 0")
    if company["shares"] is None:
        cover_shares = shares_from_cover_page(data)
        if cover_shares:
            company["shares"] = cover_shares / 1_000_000
            company["notes"].append("shares taken from filing cover page")

    for item in TAGS:
        if company[item] is None:
            company["missing"].append(item)

    previous = prior_year_end(facts, period_end)
    company["prior_year_revenue"] = None
    if previous:
        value, tag = find_value(facts, "revenue", previous)
        if value is not None:
            company["prior_year_revenue"] = value / 1_000_000
    return company


if __name__ == "__main__":
    # Quick test: load one company and print what was found
    lookup = ticker_to_cik()
    test = load_company("MSFT", lookup)
    for key, value in test.items():
        print(key, value)
