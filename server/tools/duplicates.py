from sqlmodel import Session, select

from db_connection import engine
from models import BankTransaction, Order, Payment, ReconciliationCase


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
