# Stage 3: A simple discounted cash flow (DCF) valuation.
#
# Idea: a company is worth the cash it will produce in the future, adjusted
# for the fact that a dollar later is worth less than a dollar today.
#
#   1. Start from this year's free cash flow (FCF).
#   2. Grow it for a number of years at a growth rate you choose.
#   3. Estimate a terminal value for everything after that, using either:
#        - Gordon Growth: cash flow grows forever at a slow rate, or
#        - EBITDA exit multiple: the company is sold at a multiple of EBITDA.
#   4. Discount everything back to today at a discount rate (required return).
#      With the mid-year convention, each year's cash is assumed to arrive
#      halfway through the year, so it is discounted half a year less.
#   5. Enterprise value - net debt = equity value; divide by shares = value per share.

from metrics import free_cash_flow, net_debt, ebitda

GORDON = "Gordon Growth"
EXIT_MULTIPLE = "EBITDA exit multiple"


def ask_number(question, default, unit=""):
    # Ask for a number; pressing Enter uses the default
    while True:
        answer = input(f"{question} [default {default}{unit}]: ").strip()
        if answer == "":
            return default
        try:
            return float(answer.replace("%", "").replace("x", ""))
        except ValueError:
            print("  Please type a number, like 8 or 8.5")


def ask_percent(question, default):
    return ask_number(question, default, "%") / 100


def ask_yes_no(question, default="y"):
    while True:
        answer = input(f"{question} (y/n) [default {default}]: ").strip().lower()
        if answer == "":
            answer = default
        if answer in ["y", "yes"]:
            return True
        if answer in ["n", "no"]:
            return False
        print("  Please type y or n")


def ask_method():
    print("  Terminal value method:")
    print("    1 = Gordon Growth (cash flow grows forever at a set rate)")
    print("    2 = EBITDA exit multiple (company sold at a multiple of EBITDA)")
    while True:
        answer = input("  Choose 1 or 2 [default 1]: ").strip()
        if answer in ["", "1"]:
            return GORDON
        if answer == "2":
            return EXIT_MULTIPLE
        print("  Please type 1 or 2")


def ask_assumptions():
    print("DCF assumptions (press Enter to use the default)")
    method = ask_method()
    years = int(ask_number("  Projection years", 5))
    while years < 1:
        print("  Use at least 1 year.")
        years = int(ask_number("  Projection years", 5))
    growth = ask_percent("  Growth rate for cash flow and EBITDA, %", 8)
    discount = ask_percent("  Discount rate (required return), %", 9)
    mid_year = ask_yes_no("  Use the mid-year convention?")

    assumptions = {"method": method, "years": years, "growth": growth,
                   "discount": discount, "mid_year": mid_year,
                   "terminal": None, "exit_multiple": None}

    if method == GORDON:
        terminal = ask_percent("  Terminal growth rate, %", 3)
        while terminal >= discount:
            print("  The terminal growth rate must be lower than the discount rate.")
            terminal = ask_percent("  Terminal growth rate, %", 3)
        assumptions["terminal"] = terminal
    else:
        multiple = ask_number("  Exit EV / EBITDA multiple", 15, "x")
        while multiple <= 0:
            print("  The multiple must be above 0.")
            multiple = ask_number("  Exit EV / EBITDA multiple", 15, "x")
        assumptions["exit_multiple"] = multiple
    return assumptions


def describe(assumptions):
    # One line summarizing the assumptions, for printing
    text = (f"{assumptions['method']}, {assumptions['years']} years, "
            f"{assumptions['growth']:.1%} growth, {assumptions['discount']:.1%} discount rate, ")
    if assumptions["method"] == GORDON:
        text += f"{assumptions['terminal']:.1%} terminal growth"
    else:
        text += f"{assumptions['exit_multiple']:.1f}x exit multiple"
    if assumptions["mid_year"]:
        text += ", mid-year convention"
    return text


def dcf(company, assumptions):
    fcf = free_cash_flow(company)
    if fcf is None or fcf <= 0:
        return None  # a DCF needs positive cash flow to start from

    method = assumptions["method"]
    years = assumptions["years"]
    growth = assumptions["growth"]
    discount = assumptions["discount"]

    # Years 1..N: grow the cash flow, then discount it back to today
    present_value_of_fcf = 0
    for year in range(1, years + 1):
        future_fcf = fcf * (1 + growth) ** year
        if assumptions["mid_year"]:
            timing = year - 0.5
        else:
            timing = year
        present_value_of_fcf += future_fcf / (1 + discount) ** timing

    final_year_fcf = fcf * (1 + growth) ** years
    current_ebitda = ebitda(company)
    final_year_ebitda = None
    if current_ebitda is not None and current_ebitda > 0:
        final_year_ebitda = current_ebitda * (1 + growth) ** years

    if method == GORDON:
        terminal = assumptions["terminal"]
        terminal_value = final_year_fcf * (1 + terminal) / (discount - terminal)
        # A forever-growing stream also arrives through the year, so with the
        # mid-year convention it is discounted half a year less as well
        if assumptions["mid_year"]:
            terminal_timing = years - 0.5
        else:
            terminal_timing = years
    else:
        if final_year_ebitda is None:
            return None  # can't use an EBITDA multiple without positive EBITDA
        terminal_value = final_year_ebitda * assumptions["exit_multiple"]
        # The sale happens at the end of the final year
        terminal_timing = years

    present_value_of_terminal = terminal_value / (1 + discount) ** terminal_timing
    enterprise_value = present_value_of_fcf + present_value_of_terminal
    equity_value = enterprise_value - (net_debt(company) or 0)

    result = {
        "method": method,
        "starting_fcf": fcf,
        "pv_of_fcf": present_value_of_fcf,
        "terminal_value": terminal_value,
        "pv_of_terminal": present_value_of_terminal,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "terminal_share": present_value_of_terminal / enterprise_value,
        "value_per_share": None,
        "implied_exit_multiple": None,
        "implied_terminal_growth": None,
    }

    # Cross-check: what does each method imply about the other?
    if method == GORDON and final_year_ebitda is not None:
        result["implied_exit_multiple"] = terminal_value / final_year_ebitda
    if method == EXIT_MULTIPLE:
        result["implied_terminal_growth"] = ((terminal_value * discount - final_year_fcf)
                                             / (terminal_value + final_year_fcf))

    if company.get("shares"):
        result["value_per_share"] = equity_value / company["shares"]
    return result


def print_dcf(company, result):
    print(f"\n{company['name']} ({company['ticker']}) - DCF, $ millions")
    if result is None:
        print("  Not enough positive free cash flow (or EBITDA) for this DCF.")
        return
    print(f"  Terminal value method:     {result['method']}")
    print(f"  Starting free cash flow:   ${result['starting_fcf']:,.0f}")
    print(f"  PV of projected cash flow: ${result['pv_of_fcf']:,.0f}")
    print(f"  PV of terminal value:      ${result['pv_of_terminal']:,.0f}"
          f"  ({result['terminal_share']:.0%} of total)")
    print(f"  Enterprise value:          ${result['enterprise_value']:,.0f}")
    print(f"  Equity value:              ${result['equity_value']:,.0f}")
    if result["value_per_share"] is not None:
        print(f"  Value per share:           ${result['value_per_share']:,.2f}")
    if result["implied_exit_multiple"] is not None:
        print(f"  Implied exit multiple:     {result['implied_exit_multiple']:.1f}x EBITDA")
    if result["implied_terminal_growth"] is not None:
        print(f"  Implied terminal growth:   {result['implied_terminal_growth']:.1%}")


if __name__ == "__main__":
    # Example: Microsoft, using the Stage 2 numbers plus diluted shares (millions)
    from stage2_peers import companies
    microsoft = dict(companies[0])
    microsoft["shares"] = 7453
    assumptions = ask_assumptions()
    print("\nUsing: " + describe(assumptions))
    print_dcf(microsoft, dcf(microsoft, assumptions))
