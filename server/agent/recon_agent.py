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
from tools.lookups import (
    get_adjustment,
    get_bank_transaction,
    get_order,
    get_payment,
    get_reconciliation_case,
    get_settlement,
    list_adjustments,
    list_bank_transactions,
    list_orders,
    list_payments,
    list_reconciliation_cases,
    list_settlements,
)
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


@tool
def lookup_order(order_id: int) -> str:
    """Fetch a single order by its order_id from the orders table.

    Returns a JSON object with customer_id, merchant_id, gross_amount, and currency,
    or JSON null if no order with that id exists.

    Args:
        order_id: The order's primary key.
    """
    return json.dumps(get_order(order_id), default=str)


@tool
def list_all_orders(limit: int = 50) -> str:
    """List orders from the orders table.

    Args:
        limit: Maximum number of orders to return.
    """
    return json.dumps(list_orders(limit), default=str)


@tool
def lookup_bank_transaction(bank_transaction_id: int) -> str:
    """Fetch a single bank transaction by its bank_transaction_id.

    Returns a JSON object with transaction_date, amount, description, and reference,
    or JSON null if no bank transaction with that id exists.

    Args:
        bank_transaction_id: The bank transaction's primary key.
    """
    return json.dumps(get_bank_transaction(bank_transaction_id), default=str)


@tool
def list_all_bank_transactions(limit: int = 50) -> str:
    """List bank transactions from the bank_transactions table.

    Args:
        limit: Maximum number of bank transactions to return.
    """
    return json.dumps(list_bank_transactions(limit), default=str)


@tool
def lookup_payment(payment_id: int) -> str:
    """Fetch a single payment by its payment_id from the payments table.

    Returns a JSON object with order_id, amount, payment_date, provider_reference,
    and status, or JSON null if no payment with that id exists.

    Args:
        payment_id: The payment's primary key.
    """
    return json.dumps(get_payment(payment_id), default=str)


@tool
def list_all_payments(limit: int = 50) -> str:
    """List payments from the payments table.

    Args:
        limit: Maximum number of payments to return.
    """
    return json.dumps(list_payments(limit), default=str)


@tool
def lookup_settlement(settlement_id: int) -> str:
    """Fetch a single settlement by its settlement_id from the settlements table.

    Returns a JSON object with payment_id, gross_amount, fee_amount, tax_amount,
    adjustment_amount, net_amount, and settlement_date, or JSON null if no settlement
    with that id exists.

    Args:
        settlement_id: The settlement's primary key.
    """
    return json.dumps(get_settlement(settlement_id), default=str)


@tool
def list_all_settlements(limit: int = 50) -> str:
    """List settlements from the settlements table.

    Args:
        limit: Maximum number of settlements to return.
    """
    return json.dumps(list_settlements(limit), default=str)


@tool
def lookup_adjustment(adjustment_id: int) -> str:
    """Fetch a single adjustment by its adjustment_id from the adjustments table.

    Returns a JSON object with settlement_id, type, amount, and reason, or JSON null
    if no adjustment with that id exists.

    Args:
        adjustment_id: The adjustment's primary key.
    """
    return json.dumps(get_adjustment(adjustment_id), default=str)


@tool
def list_all_adjustments(limit: int = 50) -> str:
    """List adjustments from the adjustments table.

    Args:
        limit: Maximum number of adjustments to return.
    """
    return json.dumps(list_adjustments(limit), default=str)


@tool
def lookup_reconciliation_case(case_id: int) -> str:
    """Fetch a single reconciliation case by its case_id from the reconciliation_cases table.

    Returns a JSON object with payment_id, settlement_id, bank_transaction_id, status,
    confidence, expected_amount, actual_amount, difference_amount, and explanation, or
    JSON null if no case with that id exists.

    Args:
        case_id: The reconciliation case's primary key.
    """
    return json.dumps(get_reconciliation_case(case_id), default=str)


@tool
def list_all_reconciliation_cases(limit: int = 50) -> str:
    """List reconciliation cases from the reconciliation_cases table.

    Args:
        limit: Maximum number of reconciliation cases to return.
    """
    return json.dumps(list_reconciliation_cases(limit), default=str)


RECON_TOOLS = [
    lookup_order,
    list_all_orders,
    lookup_bank_transaction,
    list_all_bank_transactions,
    lookup_payment,
    list_all_payments,
    lookup_settlement,
    list_all_settlements,
    lookup_adjustment,
    list_all_adjustments,
    lookup_reconciliation_case,
    list_all_reconciliation_cases,
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
    from rich.console import Console
    from rich.markdown import Markdown

    query = sys.argv[1] if len(sys.argv) > 1 else "Reconcile settlement 1."
    Console().print(Markdown(run(query)))
