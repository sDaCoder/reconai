SUPPORTED_CURRENCIES = {
    "INR",
    "USD",
    "EUR",
    "GBP"
}


def validate_currency(currency):

    currency = currency.upper().strip()

    if currency not in SUPPORTED_CURRENCIES:
        return {
            "valid": False,
            "currency": currency
        }

    return {
        "valid": True,
        "currency": currency
    }
