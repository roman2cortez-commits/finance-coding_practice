# Stage 6: A simple credit scorecard.
#
# Lenders look at two key questions:
#   - Leverage (Debt / EBITDA): how much debt compared to earnings? Lower is safer.
#   - Interest coverage (EBITDA / interest): how easily are interest payments covered? Higher is safer.
#
# Each gets 1-4 points, and the total decides the rating. The cutoffs are
# rough rules of thumb, not an official rating method.

from metrics import leverage, interest_coverage


def leverage_points(value):
    if value is None:
        return None
    if value <= 1.5:
        return 4
    elif value <= 3.0:
        return 3
    elif value <= 5.0:
        return 2
    else:
        return 1


def coverage_points(value):
    if value is None:
        return None
    if value >= 8:
        return 4
    elif value >= 4:
        return 3
    elif value >= 2:
        return 2
    else:
        return 1


def credit_rating(company):
    lev = leverage_points(leverage(company))
    cov = coverage_points(interest_coverage(company))
    if lev is None or cov is None:
        return "Not enough data", None
    score = lev + cov
    if score >= 7:
        rating = "Strong"
    elif score >= 5:
        rating = "Moderate"
    elif score >= 3:
        rating = "Weak"
    else:
        rating = "Distressed"
    return rating, score


if __name__ == "__main__":
    from stage2_peers import companies
    for c in companies:
        rating, score = credit_rating(c)
        print(f"{c['ticker']:<6} {rating:<16} score {score}/8")
