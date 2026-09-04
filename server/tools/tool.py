import os
import re
from datetime import datetime, timedelta

from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select

from models import BankTransaction, Order, Payment, ReconciliationCase

load_dotenv()

DATABASE_STRING = os.getenv("DATABASE_STRING")
engine = create_engine(DATABASE_STRING)


def normalize_reference(ref):

    ref = ref.lower()
    ref = re.sub(r'[^a-z0-9]', '', ref)

    return ref


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


def calculate_date_difference(date1, date2):

    if isinstance(date1, str):
        date1 = datetime.fromisoformat(date1)

    if isinstance(date2, str):
        date2 = datetime.fromisoformat(date2)

    difference = abs(date2 - date1)

    return difference.days


def find_bank_candidates(
    expected_amount,
    expected_date,
    currency,
    amount_tolerance=5,
    day_window=3
):
    if isinstance(expected_date, str):
        expected_date = datetime.fromisoformat(expected_date)

    date_lower = expected_date - timedelta(days=day_window)
    date_upper = expected_date + timedelta(days=day_window)

    candidates = []

    with Session(engine) as session:
        statement = (
            select(BankTransaction)
            .join(
                ReconciliationCase,
                ReconciliationCase.bank_transaction_id == BankTransaction.bank_transaction_id,
            )
            .join(Payment, Payment.payment_id == ReconciliationCase.payment_id)
            .join(Order, Order.order_id == Payment.order_id)
            .where(
                Order.currency == currency,
                BankTransaction.transaction_date >= date_lower,
                BankTransaction.transaction_date <= date_upper,
            )
        )
        bank_transactions = session.exec(statement).all()

    for txn in bank_transactions:

        amount_difference = abs(
            float(txn.amount) - expected_amount
        )

        date_difference = calculate_date_difference(
            expected_date,
            txn.transaction_date
        )

        if (
            amount_difference <= amount_tolerance
            and date_difference <= day_window
        ):
            candidates.append(txn)

    return candidates


def detect_duplicates():

    with Session(engine) as session:
        statement = (
            select(BankTransaction, Order.currency)
            .join(
                ReconciliationCase,
                ReconciliationCase.bank_transaction_id == BankTransaction.bank_transaction_id,
                isouter=True,
            )
            .join(Payment, Payment.payment_id == ReconciliationCase.payment_id, isouter=True)
            .join(Order, Order.order_id == Payment.order_id, isouter=True)
        )
        rows = session.exec(statement).all()

    seen = {}
    duplicates = []

    for txn, currency in rows:

        key = (
            txn.reference,
            txn.amount,
            currency,
            txn.transaction_date
        )

        if key in seen:
            duplicates.append({
                "original": seen[key],
                "duplicate": txn
            })
        else:
            seen[key] = txn

    return duplicates


def find_exact_reference_match(
    reference: str,
    bank_transactions: list
):

    matches = []

    normalized_reference = normalize_reference(reference)

    for transaction in bank_transactions:

        bank_reference = normalize_reference(
            transaction.get("reference", "")
        )

        if normalized_reference == bank_reference:
            matches.append(transaction)

    return matches

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