# Stage 5: Save the results to a formatted Excel file (pip install openpyxl).

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from metrics import all_metrics, METRIC_KINDS
from stage6_credit import credit_rating

# Excel number formats
FORMATS = {"pct": "0.0%", "x": '0.00"x"', "usd": "$#,##0", "usd2": "$#,##0.00", None: "General"}


def add_sheet(wb, title, headers, rows, kinds, width=16):
    # Write a header row, then one row per item, formatting each column
    sheet = wb.create_sheet(title)
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(name="Arial", bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F3864")
    for values in rows:
        sheet.append(values)
        for cell, kind in zip(sheet[sheet.max_row], kinds):
            cell.font = Font(name="Arial")
            cell.number_format = FORMATS[kind]
    for column in sheet.columns:
        sheet.column_dimensions[column[0].column_letter].width = width
    sheet.column_dimensions["A"].width = 34
    return sheet


def save_report(companies, dcf_results, a, filename):
    wb = Workbook()
    wb.remove(wb.active)
    names = list(METRIC_KINDS)

    rows = []
    for c in companies:
        m = all_metrics(c)
        rows.append([c["name"], c["ticker"], c.get("group", ""), c.get("fiscal_year_end", "")]
                    + [m[n] for n in names])
    add_sheet(wb, "Metrics", ["Company", "Ticker", "Group", "Fiscal year end"] + names,
              rows, [None] * 4 + [METRIC_KINDS[n] for n in names])

    rows = []
    for c in companies:
        r = dcf_results[c["ticker"]]
        if r is None:
            rows.append([c["name"], c["ticker"], "Not enough positive FCF or EBITDA"])
        else:
            rows.append([c["name"], c["ticker"], r["starting_fcf"], r["enterprise_value"],
                         r["equity_value"], r["terminal_share"], r["value_per_share"],
                         r["implied_exit_multiple"], r["implied_terminal_growth"]])
    sheet = add_sheet(wb, "DCF",
                      ["Company", "Ticker", "Starting FCF ($mm)", "Enterprise value ($mm)",
                       "Equity value ($mm)", "Terminal value % of EV", "Value per share",
                       "Implied exit multiple", "Implied terminal growth"],
                      rows, [None, None, "usd", "usd", "usd", "pct", "usd2", "x", "pct"], width=18)

    # Assumptions block below the table: (label, value, number format)
    assumptions = [("Terminal value method", a["method"], None),
                   ("Projection years", a["years"], None),
                   ("Growth rate (cash flow and EBITDA)", a["growth"], "pct"),
                   ("Discount rate", a["discount"], "pct"),
                   ("Mid-year convention", "Yes" if a["mid_year"] else "No", None),
                   ("Terminal growth rate", a["terminal"], "pct"),
                   ("Exit EV / EBITDA multiple", a["exit_multiple"], "x")]
    sheet.append([])
    sheet.append(["Assumptions"])
    sheet.cell(row=sheet.max_row, column=1).font = Font(name="Arial", bold=True)
    for label, value, kind in assumptions:
        if value is not None:
            sheet.append([label, None, value])
            sheet.cell(row=sheet.max_row, column=3).number_format = FORMATS[kind]

    rows = []
    for c in companies:
        m = all_metrics(c)
        rating, score = credit_rating(c)
        rows.append([c["name"], c["ticker"], m["Debt / EBITDA"], m["Interest coverage"], score, rating])
    add_sheet(wb, "Credit", ["Company", "Ticker", "Debt / EBITDA", "Interest coverage",
                             "Score (out of 8)", "Rating"], rows, [None, None, "x", "x", None, None])

    rows = []
    for c in companies:
        for note in c.get("notes", []) + [f"missing: {m}" for m in c.get("missing", [])]:
            rows.append([c["ticker"], note])
    rows.append(["Source", "SEC EDGAR XBRL company facts (latest 10-K). $ in millions."])
    rows.append(["Caution", "Asset managers consolidate funds/insurance units, so their leverage "
                            "and margins are not comparable to operating companies."])
    sheet = add_sheet(wb, "Notes", ["Ticker", "Note"], rows, [None, None])
    sheet.column_dimensions["A"].width = 10
    sheet.column_dimensions["B"].width = 90

    wb.save(filename)
