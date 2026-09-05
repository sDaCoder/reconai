"""Seed 100+ additional rows into every table of the Supabase database."""

from __future__ import annotations

import os
import random
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlmodel import Session, create_engine, select

from models import (
    Adjustment,
    BankTransaction,
    Order,
    Payment,
    ReconciliationCase,
    Settlement,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_STRING = os.getenv("DATABASE_STRING")
if not DATABASE_STRING:
    raise SystemExit("DATABASE_STRING is not set in .env")

RECORD_COUNT = 115
FAILED_COUNT = 5
CURRENCIES = ["INR", "INR", "INR", "USD", "EUR"]
ADJUSTMENT_TYPES = ["chargeback", "refund_adjustment", "fee_correction", "credit_note"]


def _cents(value) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _dt(days_ago: int, hour: int) -> datetime:
    return datetime.now(timezone.utc).replace(
        hour=hour, minute=0, second=0, microsecond=0
    ) - timedelta(days=days_ago)


def _resync_sequences(session: Session) -> None:
    tables_and_columns = [
        ("orders", "order_id"),
        ("payments", "payment_id"),
        ("settlements", "settlement_id"),
        ("adjustments", "adjustment_id"),
        ("bank_transactions", "bank_transaction_id"),
        ("reconciliation_cases", "case_id"),
    ]
    for table, column in tables_and_columns:
        session.exec(
            text(
                f"SELECT setval(pg_get_serial_sequence('{table}', '{column}'), "
                f"COALESCE((SELECT MAX({column}) FROM {table}), 1))"
            )
        )
    session.commit()


def seed_bulk(session: Session) -> None:
    existing = len(session.exec(select(Order)).all())
    if existing >= 100:
        print(f"Orders table already has {existing} rows; skipping bulk seed.")
        return

    _resync_sequences(session)

    failed_indexes = set(random.sample(range(RECORD_COUNT), FAILED_COUNT))

    orders = []
    for i in range(RECORD_COUNT):
        orders.append(
            Order(
                customer_id=2000 + i,
                merchant_id=600 + (i % 12),
                gross_amount=_cents(random.uniform(500, 15000)),
                currency=random.choice(CURRENCIES),
            )
        )
    session.add_all(orders)
    session.commit()
    for order in orders:
        session.refresh(order)

    payments = []
    for i, order in enumerate(orders):
        days_ago = RECORD_COUNT - i
        payments.append(
            Payment(
                order_id=order.order_id,
                amount=order.gross_amount,
                payment_date=_dt(days_ago, hour=10),
                provider_reference=f"bulk_ref_{order.order_id:04d}",
                status="failed" if i in failed_indexes else "captured",
            )
        )
    session.add_all(payments)
    session.commit()
    for payment in payments:
        session.refresh(payment)

    settlements = []
    adjustments = []
    bank_txns = []
    cases = []

    for i, (order, payment) in enumerate(zip(orders, payments)):
        days_ago = RECORD_COUNT - i

        if i in failed_indexes:
            cases.append(
                ReconciliationCase(
                    payment_id=payment.payment_id,
                    settlement_id=None,
                    bank_transaction_id=None,
                    status="unmatched",
                    confidence=round(random.uniform(0.1, 0.35), 2),
                    expected_amount=payment.amount,
                    actual_amount=Decimal("0.00"),
                    difference_amount=-payment.amount,
                    explanation="Payment failed; no settlement or bank credit found.",
                )
            )
            continue

        fee = _cents(order.gross_amount * Decimal(str(round(random.uniform(0.015, 0.035), 4))))
        tax = _cents(order.gross_amount * Decimal(str(round(random.uniform(0.0, 0.02), 4))))
        adjustment_amount = _cents(random.uniform(-200, 50))
        net_amount = _cents(order.gross_amount - fee - tax + adjustment_amount)

        settlement = Settlement(
            payment_id=payment.payment_id,
            gross_amount=order.gross_amount,
            fee_amount=fee,
            tax_amount=tax,
            adjustment_amount=adjustment_amount,
            net_amount=net_amount,
            settlement_date=_dt(days_ago - 1, hour=3),
        )
        session.add(settlement)
        session.commit()
        session.refresh(settlement)
        settlements.append(settlement)

        adjustment_type = random.choice(ADJUSTMENT_TYPES)
        adjustments.append(
            Adjustment(
                settlement_id=settlement.settlement_id,
                type=adjustment_type,
                amount=adjustment_amount,
                reason=f"{adjustment_type.replace('_', ' ').title()} applied during settlement.",
            )
        )

        has_mismatch = random.random() < 0.15
        bank_amount = (
            _cents(
                net_amount
                + Decimal(str(random.choice([-1, 1]) * random.uniform(10, 300)))
            )
            if has_mismatch
            else net_amount
        )
        bank_txn = BankTransaction(
            transaction_date=_dt(days_ago - 2, hour=19),
            amount=bank_amount,
            description=f"RPAY SETL MERCHANT {order.merchant_id}",
            reference=f"SET-{settlement.settlement_id}-B",
        )
        session.add(bank_txn)
        session.commit()
        session.refresh(bank_txn)
        bank_txns.append(bank_txn)

        if has_mismatch:
            status = "mismatch"
            confidence = round(random.uniform(0.55, 0.85), 2)
            explanation = "Bank credit does not match the expected settlement net amount."
        elif adjustment_amount != 0:
            status = "adjusted"
            confidence = round(random.uniform(0.85, 0.97), 2)
            explanation = "Settlement matched after accounting for the logged adjustment."
        else:
            status = "matched"
            confidence = round(random.uniform(0.9, 0.99), 2)
            explanation = "Settlement net amount matches the bank credit exactly."

        cases.append(
            ReconciliationCase(
                payment_id=payment.payment_id,
                settlement_id=settlement.settlement_id,
                bank_transaction_id=bank_txn.bank_transaction_id,
                status=status,
                confidence=confidence,
                expected_amount=net_amount,
                actual_amount=bank_amount,
                difference_amount=_cents(bank_amount - net_amount),
                explanation=explanation,
            )
        )

    session.add_all(adjustments)
    session.add_all(cases)
    session.commit()

    print(
        f"Bulk-seeded {len(orders)} orders, {len(payments)} payments, "
        f"{len(settlements)} settlements, {len(adjustments)} adjustments, "
        f"{len(bank_txns)} bank transactions, {len(cases)} reconciliation cases."
    )


def main() -> None:
    random.seed(7)
    engine = create_engine(DATABASE_STRING)
    try:
        with Session(engine) as session:
            seed_bulk(session)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
