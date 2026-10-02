# Stage 2: Compare several companies by looping over a list.
#
# Each company is a dictionary (like Stage 1), and the companies are kept in
# a list so one loop can calculate the same metrics for all of them.
#
# Numbers are $ millions from each company's latest 10-K (SEC EDGAR):
# Microsoft FY ended Jun 2026, Nvidia FY ended Jan 2026, others FY Dec 2025.

from metrics import all_metrics, fmt, METRIC_KINDS

companies = [
    {"name": "Microsoft", "ticker": "MSFT", "revenue": 331839, "prior_year_revenue": 281724,
     "operating_income": 155237, "da": 34300, "net_income": 133749, "interest_expense": 3051,
     "operating_cash_flow": 182935, "capex": 115948, "total_debt": 40294, "cash": 20935},
    {"name": "Alphabet", "ticker": "GOOGL", "revenue": 402836, "prior_year_revenue": 350018,
     "operating_income": 129039, "da": 21136, "net_income": 132170, "interest_expense": 736,
     "operating_cash_flow": 164713, "capex": 91447, "total_debt": 49085, "cash": 30708},
    {"name": "Amazon", "ticker": "AMZN", "revenue": 716924, "prior_year_revenue": 637959,
     "operating_income": 79975, "da": 65756, "net_income": 77670, "interest_expense": 2274,
     "operating_cash_flow": 139514, "capex": 131819, "total_debt": 68836, "cash": 86810},
    {"name": "Meta", "ticker": "META", "revenue": 200966, "prior_year_revenue": 164501,
     "operating_income": 83276, "da": 18616, "net_income": 60458, "interest_expense": 1165,
     "operating_cash_flow": 115800, "capex": 69691, "total_debt": 58744, "cash": 35873},
    {"name": "Nvidia", "ticker": "NVDA", "revenue": 215938, "prior_year_revenue": 130497,
     "operating_income": 130387, "da": 2843, "net_income": 120067, "interest_expense": 259,
     "operating_cash_flow": 102718, "capex": 6042, "total_debt": 8468, "cash": 10605},
]


def print_table(companies):
    names = list(METRIC_KINDS.keys())
    # Header row: metric name, then one column per company ticker
    header = f"{'Metric':<20}"
    for c in companies:
        header += f"{c['ticker']:>10}"
    print(header)
    print("-" * len(header))
    # One row per metric
    for name in names:
        row = f"{name:<20}"
        for c in companies:
            value = all_metrics(c)[name]
            row += f"{fmt(value, METRIC_KINDS[name]):>10}"
        print(row)


def best_company(companies, metric_name):
    # Loop through and keep track of the highest value seen so far
    best = None
    for c in companies:
        value = all_metrics(c)[metric_name]
        if value is None:
            continue
        if best is None or value > all_metrics(best)[metric_name]:
            best = c
    return best


if __name__ == "__main__":
    print_table(companies)
    print()
    for metric in ["Revenue growth", "EBITDA margin", "FCF margin"]:
        winner = best_company(companies, metric)
        print(f"Highest {metric}: {winner['name']}")
