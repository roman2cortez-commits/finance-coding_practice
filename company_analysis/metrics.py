# Financial metric functions shared by every stage.
#
# Each function takes a company dictionary (numbers in $ millions) and returns
# one number. If a number it needs is missing (None) or would mean dividing
# by zero, it returns None instead of crashing.


def safe_divide(top, bottom):
    if top is None or bottom is None or bottom == 0:
        return None
    return top / bottom


def subtract(a, b):
    if a is None or b is None:
        return None
    return a - b


def safe_add(a, b):
    if a is None or b is None:
        return None
    return a + b


def ebitda(c):
    # EBITDA = operating income + depreciation & amortization
    if c.get("ebitda") is not None:
        return c["ebitda"]
    return safe_add(c.get("operating_income"), c.get("da"))


def revenue_growth(c):
    change = subtract(c.get("revenue"), c.get("prior_year_revenue"))
    return safe_divide(change, c.get("prior_year_revenue"))


def ebitda_margin(c):
    return safe_divide(ebitda(c), c.get("revenue"))


def net_margin(c):
    return safe_divide(c.get("net_income"), c.get("revenue"))


def free_cash_flow(c):
    return subtract(c.get("operating_cash_flow"), c.get("capex"))


def fcf_margin(c):
    return safe_divide(free_cash_flow(c), c.get("revenue"))


def net_debt(c):
    return subtract(c.get("total_debt"), c.get("cash"))


def leverage(c):
    # Total debt / EBITDA: how many years of EBITDA it would take to repay the debt
    return safe_divide(c.get("total_debt"), ebitda(c))


def net_leverage(c):
    return safe_divide(net_debt(c), ebitda(c))


def interest_coverage(c):
    # EBITDA / interest: how many times earnings cover the interest bill
    return safe_divide(ebitda(c), c.get("interest_expense"))


def all_metrics(c):
    return {
        "Revenue growth": revenue_growth(c),
        "EBITDA margin": ebitda_margin(c),
        "Net margin": net_margin(c),
        "FCF margin": fcf_margin(c),
        "Free cash flow": free_cash_flow(c),
        "Debt / EBITDA": leverage(c),
        "Net debt / EBITDA": net_leverage(c),
        "Interest coverage": interest_coverage(c),
    }


def fmt(value, kind):
    # Turn a number into display text: "pct" = 12.3%, "x" = 2.50x, "usd" = $1,234
    if value is None:
        return "n/a"
    if kind == "pct":
        return f"{value:.1%}"
    if kind == "x":
        return f"{value:.2f}x"
    return f"${value:,.0f}"


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
