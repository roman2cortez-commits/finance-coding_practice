# Financial metric functions shared by every stage.
#
# Each function takes a company dictionary (numbers in $ millions) and returns
# one number, or None if a number it needs is missing.


def divide(top, bottom):
    if top is None or bottom is None or bottom == 0:
        return None
    return top / bottom


def minus(a, b):
    if a is None or b is None:
        return None
    return a - b


def ebitda(c):
    if c.get("ebitda") is not None:  # Stage 1 enters EBITDA directly
        return c["ebitda"]
    if c.get("operating_income") is None or c.get("da") is None:
        return None
    return c["operating_income"] + c["da"]  # EBITDA = operating income + D&A


def free_cash_flow(c):
    return minus(c.get("operating_cash_flow"), c.get("capex"))


def net_debt(c):
    return minus(c.get("total_debt"), c.get("cash"))


def leverage(c):
    return divide(c.get("total_debt"), ebitda(c))  # years of EBITDA to repay debt


def interest_coverage(c):
    return divide(ebitda(c), c.get("interest_expense"))  # times interest is covered


def all_metrics(c):
    growth = minus(c.get("revenue"), c.get("prior_year_revenue"))
    return {
        "Revenue growth": divide(growth, c.get("prior_year_revenue")),
        "EBITDA margin": divide(ebitda(c), c.get("revenue")),
        "Net margin": divide(c.get("net_income"), c.get("revenue")),
        "FCF margin": divide(free_cash_flow(c), c.get("revenue")),
        "Free cash flow": free_cash_flow(c),
        "Debt / EBITDA": leverage(c),
        "Net debt / EBITDA": divide(net_debt(c), ebitda(c)),
        "Interest coverage": interest_coverage(c),
    }


# How to display each metric: "pct" = 12.3%, "x" = 2.50x, "usd" = $1,234
METRIC_KINDS = {
    "Revenue growth": "pct",
    "EBITDA margin": "pct",
    "Net margin": "pct",
    "FCF margin": "pct",
    "Free cash flow": "usd",
    "Debt / EBITDA": "x",
    "Net debt / EBITDA": "x",
    "Interest coverage": "x",
}


def fmt(value, kind):
    if value is None:
        return "n/a"
    if kind == "pct":
        return f"{value:.1%}"
    if kind == "x":
        return f"{value:.2f}x"
    return f"${value:,.0f}"
