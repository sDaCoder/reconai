"""Seed the Supabase database with dummy reconciliation data via SQLModel."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
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


def _dt(days_ago: int, hour: int = 12) -> datetime:
    return datetime.now(timezone.utc).replace(
        hour=hour, minute=0, second=0, microsecond=0
    ) - timedelta(days=days_ago)


def seed(session: Session) -> None:
    existing = session.exec(select(Order)).first()
    if existing is not None:
        print("Database already has orders; skipping seed.")
        return

    # --- Orders ---
    orders = [
        Order(
            customer_id=1001,
            merchant_id=501,
            gross_amount=Decimal("1500.00"),
            currency="INR",
        ),
        Order(
            customer_id=1002,
            merchant_id=501,
            gross_amount=Decimal("2750.50"),
            currency="INR",
        ),
        Order(
            customer_id=1003,
            merchant_id=502,
            gross_amount=Decimal("999.00"),
            currency="INR",
        ),
        Order(
            customer_id=1004,
            merchant_id=502,
            gross_amount=Decimal("4200.00"),
            currency="INR",
        ),
        Order(
            customer_id=1005,
            merchant_id=503,
            gross_amount=Decimal("350.75"),
            currency="INR",
        ),
    ]
    session.add_all(orders)
    session.commit()
    for order in orders:
        session.refresh(order)

    # --- Payments (one per order; last one failed) ---
    payments = [
        Payment(
            order_id=orders[0].order_id,
            amount=Decimal("1500.00"),
            payment_date=_dt(5, 10),
            provider_reference="pay_ref_001",
            status="captured",
        ),
        Payment(
            order_id=orders[1].order_id,
            amount=Decimal("2750.50"),
            payment_date=_dt(4, 11),
            provider_reference="pay_ref_002",
            status="captured",
        ),
        Payment(
            order_id=orders[2].order_id,
            amount=Decimal("999.00"),
            payment_date=_dt(3, 14),
            provider_reference="pay_ref_003",
            status="captured",
        ),
        Payment(
            order_id=orders[3].order_id,
            amount=Decimal("4200.00"),
            payment_date=_dt(2, 9),
            provider_reference="pay_ref_004",
            status="captured",
        ),
        Payment(
            order_id=orders[4].order_id,
            amount=Decimal("350.75"),
            payment_date=_dt(1, 16),
            provider_reference="pay_ref_005",
            status="failed",
        ),
    ]
    session.add_all(payments)
    session.commit()
    for payment in payments:
        session.refresh(payment)

    # --- Settlements (for captured payments) ---
    # Settlement 0: clean match
    # Settlement 1: fee/tax deduction
    # Settlement 2: chargeback adjustment
    # Settlement 3: underpaid vs bank
    settlements = [
        Settlement(
            payment_id=payments[0].payment_id,
            gross_amount=Decimal("1500.00"),
            fee_amount=Decimal("30.00"),
            tax_amount=Decimal("5.40"),
            adjustment_amount=Decimal("0.00"),
            net_amount=Decimal("1464.60"),
            settlement_date=_dt(4, 18),
        ),
        Settlement(
            payment_id=payments[1].payment_id,
            gross_amount=Decimal("2750.50"),
            fee_amount=Decimal("55.01"),
            tax_amount=Decimal("9.90"),
            adjustment_amount=Decimal("0.00"),
            net_amount=Decimal("2685.59"),
            settlement_date=_dt(3, 18),
        ),
        Settlement(
            payment_id=payments[2].payment_id,
            gross_amount=Decimal("999.00"),
            fee_amount=Decimal("19.98"),
            tax_amount=Decimal("3.60"),
            adjustment_amount=Decimal("-50.00"),
            net_amount=Decimal("925.42"),
            settlement_date=_dt(2, 18),
        ),
        Settlement(
            payment_id=payments[3].payment_id,
            gross_amount=Decimal("4200.00"),
            fee_amount=Decimal("84.00"),
            tax_amount=Decimal("15.12"),
            adjustment_amount=Decimal("0.00"),
            net_amount=Decimal("4100.88"),
            settlement_date=_dt(1, 18),
        ),
    ]
    session.add_all(settlements)
    session.commit()
    for settlement in settlements:
        session.refresh(settlement)

    # --- Adjustments ---
    adjustments = [
        Adjustment(
            settlement_id=settlements[2].settlement_id,
            type="chargeback",
            amount=Decimal("-50.00"),
            reason="Partial chargeback from customer dispute",
        ),
        Adjustment(
            settlement_id=settlements[1].settlement_id,
            type="fee_rebate",
            amount=Decimal("5.00"),
            reason="Promotional fee rebate for merchant 501",
        ),
    ]
    session.add_all(adjustments)
    session.commit()

    # --- Bank transactions ---
    bank_txns = [
        BankTransaction(
            transaction_date=_dt(4, 19),
            amount=Decimal("1464.60"),
            description="NEFT settlement pay_ref_001",
            reference="BNK-20260301-001",
        ),
        BankTransaction(
            transaction_date=_dt(3, 19),
            amount=Decimal("2685.59"),
            description="NEFT settlement pay_ref_002",
            reference="BNK-20260302-002",
        ),
        BankTransaction(
            transaction_date=_dt(2, 19),
            amount=Decimal("925.42"),
            description="NEFT settlement pay_ref_003",
            reference="BNK-20260303-003",
        ),
        # Underpaid vs settlement net of 4100.88
        BankTransaction(
            transaction_date=_dt(1, 19),
            amount=Decimal("4000.00"),
            description="NEFT settlement pay_ref_004",
            reference="BNK-20260304-004",
        ),
        # Orphan bank credit with no matching payment
        BankTransaction(
            transaction_date=_dt(0, 10),
            amount=Decimal("100.00"),
            description="Unidentified credit",
            reference="BNK-ORPHAN-999",
        ),
    ]
    session.add_all(bank_txns)
    session.commit()
    for bank_txn in bank_txns:
        session.refresh(bank_txn)

    # --- Reconciliation cases ---
    cases = [
        ReconciliationCase(
            payment_id=payments[0].payment_id,
            settlement_id=settlements[0].settlement_id,
            bank_transaction_id=bank_txns[0].bank_transaction_id,
            status="matched",
            confidence=0.98,
            expected_amount=Decimal("1464.60"),
            actual_amount=Decimal("1464.60"),
            difference_amount=Decimal("0.00"),
            explanation="Payment, settlement, and bank credit amounts align.",
        ),
        ReconciliationCase(
            payment_id=payments[1].payment_id,
            settlement_id=settlements[1].settlement_id,
            bank_transaction_id=bank_txns[1].bank_transaction_id,
            status="matched",
            confidence=0.95,
            expected_amount=Decimal("2685.59"),
            actual_amount=Decimal("2685.59"),
            difference_amount=Decimal("0.00"),
            explanation="Matched after applying standard MDR fees.",
        ),
        ReconciliationCase(
            payment_id=payments[2].payment_id,
            settlement_id=settlements[2].settlement_id,
            bank_transaction_id=bank_txns[2].bank_transaction_id,
            status="adjusted",
            confidence=0.88,
            expected_amount=Decimal("975.42"),
            actual_amount=Decimal("925.42"),
            difference_amount=Decimal("-50.00"),
            explanation="Chargeback adjustment of 50.00 reduced net settlement.",
        ),
        ReconciliationCase(
            payment_id=payments[3].payment_id,
            settlement_id=settlements[3].settlement_id,
            bank_transaction_id=bank_txns[3].bank_transaction_id,
            status="mismatch",
            confidence=0.72,
            expected_amount=Decimal("4100.88"),
            actual_amount=Decimal("4000.00"),
            difference_amount=Decimal("-100.88"),
            explanation="Bank credit is short by 100.88 versus settlement net.",
        ),
        ReconciliationCase(
            payment_id=payments[4].payment_id,
            settlement_id=None,
            bank_transaction_id=None,
            status="unmatched",
            confidence=0.40,
            expected_amount=Decimal("350.75"),
            actual_amount=Decimal("0.00"),
            difference_amount=Decimal("-350.75"),
            explanation="Payment failed; no settlement or bank credit found.",
        ),
    ]
    session.add_all(cases)
    session.commit()

    print(
        f"Seeded {len(orders)} orders, {len(payments)} payments, "
        f"{len(settlements)} settlements, {len(adjustments)} adjustments, "
        f"{len(bank_txns)} bank transactions, {len(cases)} reconciliation cases."
    )


def main() -> None:
    engine = create_engine(DATABASE_STRING)
    try:
        with Session(engine) as session:
            seed(session)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
