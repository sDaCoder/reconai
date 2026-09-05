import re
from datetime import datetime, timedelta

from sqlmodel import Session, select

from db_connection import engine
from models import BankTransaction, Order, Payment, ReconciliationCase
from tools.dates import calculate_date_difference


def normalize_reference(ref):

    ref = ref.lower()
    ref = re.sub(r'[^a-z0-9]', '', ref)

    return ref


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
