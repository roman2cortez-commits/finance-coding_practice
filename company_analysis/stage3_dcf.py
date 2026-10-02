# Stage 3: A simple discounted cash flow (DCF) valuation.
#
# Idea: a company is worth the cash it will produce in the future, adjusted
# for the fact that a dollar later is worth less than a dollar today.
#
#   1. Start from this year's free cash flow (FCF).
#   2. Grow it for 5 years at a growth rate you choose.
#   3. After year 5, assume it grows forever at a slow "terminal" rate.
#   4. Discount everything back to today at a discount rate (required return).
#   5. Enterprise value - net debt = equity value; divide by shares = value per share.

from metrics import free_cash_flow, net_debt


def ask_percent(question, default):
    # Ask for a percentage; pressing Enter uses the default
    while True:
        answer = input(f"{question} [default {default}%]: ").strip()
        if answer == "":
            return default / 100
        try:
            return float(answer.replace("%", "")) / 100
        except ValueError:
            print("Please type a number, like 8 or 8.5")


def ask_assumptions():
    print("DCF assumptions (type a number like 8 for 8%, or press Enter for the default)")
    growth = ask_percent("  Free cash flow growth, years 1-5", 8)
    discount = ask_percent("  Discount rate (required return)", 9)
    terminal = ask_percent("  Terminal growth rate, after year 5", 3)
    while terminal >= discount:
        print("  The terminal growth rate must be lower than the discount rate.")
        terminal = ask_percent("  Terminal growth rate, after year 5", 3)
    return {"growth": growth, "discount": discount, "terminal": terminal}


def dcf(company, assumptions, years=5):
    fcf = free_cash_flow(company)
    if fcf is None or fcf <= 0:
        return None  # a DCF needs positive cash flow to start from

    growth = assumptions["growth"]
    discount = assumptions["discount"]
    terminal = assumptions["terminal"]

    present_value_of_fcf = 0
    for year in range(1, years + 1):
        future_fcf = fcf * (1 + growth) ** year
        present_value_of_fcf += future_fcf / (1 + discount) ** year

    final_year_fcf = fcf * (1 + growth) ** years
    terminal_value = final_year_fcf * (1 + terminal) / (discount - terminal)
    present_value_of_terminal = terminal_value / (1 + discount) ** years

    enterprise_value = present_value_of_fcf + present_value_of_terminal
    equity_value = enterprise_value - (net_debt(company) or 0)

    result = {
        "starting_fcf": fcf,
        "pv_of_fcf": present_value_of_fcf,
        "pv_of_terminal": present_value_of_terminal,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "terminal_share": present_value_of_terminal / enterprise_value,
        "value_per_share": None,
    }
    if company.get("shares"):
        result["value_per_share"] = equity_value / company["shares"]
    return result


def print_dcf(company, result):
    print(f"\n{company['name']} ({company['ticker']}) - DCF, $ millions")
    if result is None:
        print("  Not enough positive free cash flow for a DCF.")
        return
    print(f"  Starting free cash flow:   ${result['starting_fcf']:,.0f}")
    print(f"  PV of 5-year cash flows:   ${result['pv_of_fcf']:,.0f}")
    print(f"  PV of terminal value:      ${result['pv_of_terminal']:,.0f}"
          f"  ({result['terminal_share']:.0%} of total)")
    print(f"  Enterprise value:          ${result['enterprise_value']:,.0f}")
    print(f"  Equity value:              ${result['equity_value']:,.0f}")
    if result["value_per_share"] is not None:
        print(f"  Value per share:           ${result['value_per_share']:,.2f}")


if __name__ == "__main__":
    # Example: Microsoft, using the Stage 2 numbers plus diluted shares (millions)
    from stage2_peers import companies
    microsoft = dict(companies[0])
    microsoft["shares"] = 7453
    assumptions = ask_assumptions()
    print_dcf(microsoft, dcf(microsoft, assumptions))
