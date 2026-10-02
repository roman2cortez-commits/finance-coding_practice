# Stage 1: Calculate key financial metrics from hand-entered numbers.
#
# Numbers are Papa John's (PZZA) fiscal year 2025, in $ millions, from the
# company's Q4/FY2025 earnings release (Feb 26, 2026).

company = {
    "name": "Papa John's",
    "ticker": "PZZA",
    "revenue": 2053.8,
    "prior_year_revenue": 2059.4,
    "ebitda": 201.1,
    "net_income": 32.1,
    "interest_expense": 40.8,
    "operating_cash_flow": 126.0,
    "capex": 64.7,
    "total_debt": 715.4,
    "cash": 37.0,
}


def revenue_growth(c):
    return (c["revenue"] - c["prior_year_revenue"]) / c["prior_year_revenue"]


def ebitda_margin(c):
    return c["ebitda"] / c["revenue"]


def net_margin(c):
    return c["net_income"] / c["revenue"]


def free_cash_flow(c):
    return c["operating_cash_flow"] - c["capex"]


def leverage(c):
    # Total debt / EBITDA: how many years of EBITDA it would take to repay the debt
    return c["total_debt"] / c["ebitda"]


def net_leverage(c):
    return (c["total_debt"] - c["cash"]) / c["ebitda"]


def interest_coverage(c):
    # EBITDA / interest: how many times earnings cover the interest bill
    return c["ebitda"] / c["interest_expense"]


def print_report(c):
    print(f"{c['name']} ({c['ticker']}) - FY2025, $ millions")
    print("-" * 40)
    print("Growth & profitability")
    print(f"  Revenue growth:      {revenue_growth(c):.1%}")
    print(f"  EBITDA margin:       {ebitda_margin(c):.1%}")
    print(f"  Net margin:          {net_margin(c):.1%}")
    print(f"  Free cash flow:      ${free_cash_flow(c):,.1f}")
    print("Credit")
    print(f"  Debt / EBITDA:       {leverage(c):.2f}x")
    print(f"  Net debt / EBITDA:   {net_leverage(c):.2f}x")
    print(f"  Interest coverage:   {interest_coverage(c):.2f}x")


print_report(company)
