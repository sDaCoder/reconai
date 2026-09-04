from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain.agents import create_agent
from langchain_core.tools import tool
from ai_models import get_groq_model

from tools.amounts import calculate_expected_settlement, compare_amounts
from tools.dates import calculate_date_difference
from tools.duplicates import detect_duplicates
from tools.matching import find_bank_candidates, find_exact_reference_match
from tools.validation import validate_currency


def _serialize_bank_transaction(txn) -> dict:
    return {
        "bank_transaction_id": txn.bank_transaction_id,
        "transaction_date": txn.transaction_date.isoformat(),
        "amount": float(txn.amount),
        "description": txn.description,
        "reference": txn.reference,
    }


@tool
def validate_settlement_currency(currency: str) -> str:
    """Validate that a settlement's currency is one Recon AI supports (INR, USD, EUR, GBP).

    Args:
        currency: The currency code from the settlement/order (e.g. "usd", "INR").
    """
    return json.dumps(validate_currency(currency))


@tool
def check_duplicate_bank_transactions() -> str:
    """Scan all bank transactions for duplicates (same reference, amount, currency, and date).

    Returns a JSON list of {original, duplicate} pairs for every duplicate found (empty
    list if none).
    """
    duplicates = detect_duplicates()
    return json.dumps(
        [
            {
                "original": _serialize_bank_transaction(pair["original"]),
                "duplicate": _serialize_bank_transaction(pair["duplicate"]),
            }
            for pair in duplicates
        ]
    )


@tool
def calculate_expected_settlement_amount(
    gross_amount: float,
    fee: float = 0,
    tax: float = 0,
    refund: float = 0,
    adjustment: float = 0,
) -> str:
    """Calculate the expected net settlement amount from a payment's gross amount and deductions.

    Args:
        gross_amount: The original payment/order gross amount.
        fee: Processor/gateway fee to subtract.
        tax: Tax to subtract.
        refund: Refund amount to subtract.
        adjustment: Adjustment amount to add back.
    """
    return json.dumps(calculate_expected_settlement(gross_amount, fee, tax, refund, adjustment))


@tool
def search_exact_bank_reference(reference: str, bank_transactions: list[dict]) -> str:
    """Search a list of candidate bank transactions for an exact reference match.

    Normalizes references (lowercase, alphanumeric only) before comparing, so formatting
    differences such as dashes, spaces, or casing are ignored. Returns a JSON list of
    matching transactions (empty list if none).

    Args:
        reference: The payment/order provider reference to match against.
        bank_transactions: Candidate bank transactions, each a dict with a "reference" key
            (e.g. the output of search_bank_candidates).
    """
    return json.dumps(find_exact_reference_match(reference, bank_transactions))


@tool
def search_bank_candidates(
    expected_amount: float,
    expected_date: str,
    currency: str,
    amount_tolerance: float = 5,
    day_window: int = 3,
) -> str:
    """Search bank transactions for candidates near an expected settlement amount and date.

    Returns a JSON list of candidate bank transactions (empty list if none).

    Args:
        expected_amount: The expected settlement amount to match against.
        expected_date: ISO-format date/datetime the settlement is expected around.
        currency: The order's currency; only bank transactions linked to orders in this
            currency are considered.
        amount_tolerance: Maximum allowed absolute amount difference.
        day_window: Maximum allowed number of days between expected and actual date.
    """
    candidates = find_bank_candidates(
        expected_amount, expected_date, currency, amount_tolerance, day_window
    )
    return json.dumps([_serialize_bank_transaction(txn) for txn in candidates])


@tool
def compare_settlement_amounts(expected: float, actual: float, tolerance: float = 0.01) -> str:
    """Compare an expected settlement amount against an actual bank transaction amount.

    Args:
        expected: The expected settlement amount.
        actual: The actual amount found on the bank transaction.
        tolerance: Maximum absolute difference still considered a match.
    """
    return json.dumps(compare_amounts(expected, actual, tolerance))


@tool
def compare_settlement_dates(date1: str, date2: str) -> str:
    """Calculate the number of days between a settlement date and a bank transaction date.

    Args:
        date1: First ISO-format date/datetime.
        date2: Second ISO-format date/datetime.
    """
    return json.dumps(calculate_date_difference(date1, date2))


RECON_TOOLS = [
    validate_settlement_currency,
    check_duplicate_bank_transactions,
    calculate_expected_settlement_amount,
    search_exact_bank_reference,
    search_bank_candidates,
    compare_settlement_amounts,
    compare_settlement_dates,
]

SYSTEM_PROMPT = (Path(__file__).resolve().parent / "prompt.txt").read_text()

recon_agent = create_agent(
    model=get_groq_model(),
    tools=RECON_TOOLS,
    system_prompt=SYSTEM_PROMPT,
)


def run(user_input: str) -> str:
    result = recon_agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config={"recursion_limit": 25},
    )
    return result["messages"][-1].content


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Reconcile settlement 1."
    print(run(query))
