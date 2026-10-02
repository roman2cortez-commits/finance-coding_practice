# Stage 3: Discounted cash flow (DCF) valuation.
#
#   1. Grow this year's free cash flow (FCF) for N years and discount each
#      year back to today at the discount rate.
#   2. Add a terminal value for everything after year N:
#        - Gordon Growth: FCF grows forever at a slow rate, or
#        - EBITDA exit multiple: the company is sold at a multiple of EBITDA.
#   3. Enterprise value - net debt = equity value; / shares = value per share.
#
# Mid-year convention: cash arrives through the year, not on Dec 31, so each
# year is discounted half a year less.

from metrics import free_cash_flow, net_debt, ebitda

GORDON = "Gordon Growth"
EXIT_MULTIPLE = "EBITDA exit multiple"


def ask(question, default):
    # Ask for a number; pressing Enter keeps the default
    while True:
        answer = input(f"  {question} [{default}]: ").strip().replace("%", "").replace("x", "")
        if answer == "":
            return default
        try:
            return float(answer)
        except ValueError:
            print("  Please type a number, like 8 or 8.5")


def ask_assumptions():
    print("DCF assumptions (press Enter to keep the default)")
    choice = ask("Terminal value: 1 = Gordon Growth, 2 = EBITDA exit multiple", 1)
    a = {
        "method": EXIT_MULTIPLE if choice == 2 else GORDON,
        "years": max(1, int(ask("Projection years", 5))),
        "growth": ask("Growth rate for cash flow and EBITDA, %", 8) / 100,
        "discount": ask("Discount rate, %", 9) / 100,
        "mid_year": ask("Mid-year convention: 1 = yes, 0 = no", 1) == 1,
        "terminal": None,
        "exit_multiple": None,
    }
    if a["method"] == GORDON:
        a["terminal"] = ask("Terminal growth rate, %", 3) / 100
        while a["terminal"] >= a["discount"]:
            print("  Terminal growth must be lower than the discount rate.")
            a["terminal"] = ask("Terminal growth rate, %", 3) / 100
    else:
        a["exit_multiple"] = ask("Exit EV / EBITDA multiple", 15)
        while a["exit_multiple"] <= 0:
            print("  The multiple must be above 0.")
            a["exit_multiple"] = ask("Exit EV / EBITDA multiple", 15)
    return a


def describe(a):
    text = f"{a['method']}, {a['years']} years, {a['growth']:.1%} growth, {a['discount']:.1%} discount rate, "
    if a["method"] == GORDON:
        text += f"{a['terminal']:.1%} terminal growth"
    else:
        text += f"{a['exit_multiple']:.1f}x exit multiple"
    if a["mid_year"]:
        text += ", mid-year convention"
    return text


def dcf(company, a):
    fcf = free_cash_flow(company)
    if fcf is None or fcf <= 0:
        return None  # a DCF needs positive cash flow to start from

    n, g, r = a["years"], a["growth"], a["discount"]
    shift = 0.5 if a["mid_year"] else 0

    pv_fcf = 0
    for year in range(1, n + 1):
        pv_fcf += fcf * (1 + g) ** year / (1 + r) ** (year - shift)

    final_fcf = fcf * (1 + g) ** n
    final_ebitda = None
    if ebitda(company) is not None and ebitda(company) > 0:
        final_ebitda = ebitda(company) * (1 + g) ** n

    if a["method"] == GORDON:
        tv = final_fcf * (1 + a["terminal"]) / (r - a["terminal"])
        tv_year = n - shift  # grows forever, so it also arrives through the year
    else:
        if final_ebitda is None:
            return None  # an EBITDA multiple needs positive EBITDA
        tv = final_ebitda * a["exit_multiple"]
        tv_year = n  # sold at the end of the final year

    pv_tv = tv / (1 + r) ** tv_year
    ev = pv_fcf + pv_tv
    equity = ev - (net_debt(company) or 0)

    # Cross-check: what each method implies about the other
    implied_multiple = None
    implied_growth = None
    if a["method"] == GORDON and final_ebitda is not None:
        implied_multiple = tv / final_ebitda
    if a["method"] == EXIT_MULTIPLE:
        implied_growth = (tv * r - final_fcf) / (tv + final_fcf)

    return {
        "method": a["method"],
        "starting_fcf": fcf,
        "pv_of_fcf": pv_fcf,
        "terminal_value": tv,
        "pv_of_terminal": pv_tv,
        "enterprise_value": ev,
        "equity_value": equity,
        "terminal_share": pv_tv / ev,
        "value_per_share": equity / company["shares"] if company.get("shares") else None,
        "implied_exit_multiple": implied_multiple,
        "implied_terminal_growth": implied_growth,
    }


def print_dcf(company, r):
    print(f"\n{company['name']} ({company['ticker']}) - DCF, $ millions")
    if r is None:
        print("  Not enough positive free cash flow (or EBITDA) for this DCF.")
        return
    print(f"  Method:                    {r['method']}")
    print(f"  Starting free cash flow:   ${r['starting_fcf']:,.0f}")
    print(f"  PV of projected cash flow: ${r['pv_of_fcf']:,.0f}")
    print(f"  PV of terminal value:      ${r['pv_of_terminal']:,.0f}  ({r['terminal_share']:.0%} of total)")
    print(f"  Enterprise value:          ${r['enterprise_value']:,.0f}")
    print(f"  Equity value:              ${r['equity_value']:,.0f}")
    if r["value_per_share"] is not None:
        print(f"  Value per share:           ${r['value_per_share']:,.2f}")
    if r["implied_exit_multiple"] is not None:
        print(f"  Implied exit multiple:     {r['implied_exit_multiple']:.1f}x EBITDA")
    if r["implied_terminal_growth"] is not None:
        print(f"  Implied terminal growth:   {r['implied_terminal_growth']:.1%}")


if __name__ == "__main__":
    # Example: Microsoft from Stage 2, plus diluted shares (millions)
    from stage2_peers import companies
    microsoft = dict(companies[0], shares=7453)
    assumptions = ask_assumptions()
    print("\nUsing: " + describe(assumptions))
    print_dcf(microsoft, dcf(microsoft, assumptions))
