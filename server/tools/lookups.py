from sqlmodel import Session, select

from db_connection import engine
from models import (
    Adjustment,
    BankTransaction,
    Order,
    Payment,
    ReconciliationCase,
    Settlement,
)


def _to_dict(row) -> dict | None:
    return row.model_dump() if row else None


def get_order(order_id: int) -> dict | None:
    with Session(engine) as session:
        return _to_dict(session.get(Order, order_id))


def list_orders(limit: int = 50) -> list[dict]:
    with Session(engine) as session:
        rows = session.exec(select(Order).limit(limit)).all()
        return [_to_dict(row) for row in rows]


def get_bank_transaction(bank_transaction_id: int) -> dict | None:
    with Session(engine) as session:
        return _to_dict(session.get(BankTransaction, bank_transaction_id))


def list_bank_transactions(limit: int = 50) -> list[dict]:
    with Session(engine) as session:
        rows = session.exec(select(BankTransaction).limit(limit)).all()
        return [_to_dict(row) for row in rows]


def get_payment(payment_id: int) -> dict | None:
    with Session(engine) as session:
        return _to_dict(session.get(Payment, payment_id))


def list_payments(limit: int = 50) -> list[dict]:
    with Session(engine) as session:
        rows = session.exec(select(Payment).limit(limit)).all()
        return [_to_dict(row) for row in rows]


def get_settlement(settlement_id: int) -> dict | None:
    with Session(engine) as session:
        return _to_dict(session.get(Settlement, settlement_id))


def list_settlements(limit: int = 50) -> list[dict]:
    with Session(engine) as session:
        rows = session.exec(select(Settlement).limit(limit)).all()
        return [_to_dict(row) for row in rows]


def get_adjustment(adjustment_id: int) -> dict | None:
    with Session(engine) as session:
        return _to_dict(session.get(Adjustment, adjustment_id))


def list_adjustments(limit: int = 50) -> list[dict]:
    with Session(engine) as session:
        rows = session.exec(select(Adjustment).limit(limit)).all()
        return [_to_dict(row) for row in rows]


def get_reconciliation_case(case_id: int) -> dict | None:
    with Session(engine) as session:
        return _to_dict(session.get(ReconciliationCase, case_id))


def list_reconciliation_cases(limit: int = 50) -> list[dict]:
    with Session(engine) as session:
        rows = session.exec(select(ReconciliationCase).limit(limit)).all()
        return [_to_dict(row) for row in rows]
