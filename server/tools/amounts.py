def calculate_expected_settlement(
    gross_amount: float,
    fee: float = 0,
    tax: float = 0,
    refund: float = 0,
    adjustment: float = 0
) -> float:
    expected = (
        gross_amount
        - fee
        - tax
        - refund
        + adjustment
    )

    return round(expected, 2)


def compare_amounts(
    expected: float,
    actual: float,
    tolerance: float = 0.01
) -> dict:

    difference = actual - expected

    return {
        "expected": expected,
        "actual": actual,
        "difference": round(difference, 2),
        "absolute_difference": round(abs(difference), 2),
        "matched": abs(difference) <= tolerance
    }
