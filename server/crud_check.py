"""Exercise SQLModel CRUD against the Supabase database."""

from __future__ import annotations

import os
from datetime import datetime, timezone
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


def _ok(label: str) -> None:
    print(f"  PASS  {label}")


def _fail(label: str, err: Exception) -> None:
    print(f"  FAIL  {label}: {err}")
    raise


def read_existing(session: Session) -> None:
    print("\n[READ] existing seeded rows")
    counts = {
        "orders": len(session.exec(select(Order)).all()),
        "payments": len(session.exec(select(Payment)).all()),
        "settlements": len(session.exec(select(Settlement)).all()),
        "adjustments": len(session.exec(select(Adjustment)).all()),
        "bank_transactions": len(session.exec(select(BankTransaction)).all()),
        "reconciliation_cases": len(session.exec(select(ReconciliationCase)).all()),
    }
    for name, count in counts.items():
        print(f"  {name}: {count}")

    matched = session.exec(
        select(ReconciliationCase).where(ReconciliationCase.status == "matched")
    ).all()
    _ok(f"filtered reconciliation cases status=matched -> {len(matched)}")

    first_order = session.exec(select(Order)).first()
    if first_order is None:
        raise RuntimeError("No orders found; run seed_data.py first")
    by_pk = session.get(Order, first_order.order_id)
    assert by_pk is not None
    _ok(f"session.get(Order, {first_order.order_id})")


def create_chain(session: Session) -> dict[str, int]:
    print("\n[CREATE] full related chain")

    order = Order(
        customer_id=9001,
        merchant_id=901,
        gross_amount=Decimal("777.25"),
        currency="INR",
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    assert order.order_id is not None
    _ok(f"Order order_id={order.order_id}")

    payment = Payment(
        order_id=order.order_id,
        amount=Decimal("777.25"),
        payment_date=datetime.now(timezone.utc),
        provider_reference="crud_test_pay_001",
        status="captured",
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    assert payment.payment_id is not None
    _ok(f"Payment payment_id={payment.payment_id}")

    settlement = Settlement(
        payment_id=payment.payment_id,
        gross_amount=Decimal("777.25"),
        fee_amount=Decimal("15.55"),
        tax_amount=Decimal("2.80"),
        adjustment_amount=Decimal("0.00"),
        net_amount=Decimal("758.90"),
        settlement_date=datetime.now(timezone.utc),
    )
    session.add(settlement)
    session.commit()
    session.refresh(settlement)
    assert settlement.settlement_id is not None
    _ok(f"Settlement settlement_id={settlement.settlement_id}")

    adjustment = Adjustment(
        settlement_id=settlement.settlement_id,
        type="rounding",
        amount=Decimal("0.10"),
        reason="CRUD test rounding adjustment",
    )
    session.add(adjustment)
    session.commit()
    session.refresh(adjustment)
    assert adjustment.adjustment_id is not None
    _ok(f"Adjustment adjustment_id={adjustment.adjustment_id}")

    bank_txn = BankTransaction(
        transaction_date=datetime.now(timezone.utc),
        amount=Decimal("758.90"),
        description="CRUD test bank credit",
        reference="CRUD-BNK-001",
    )
    session.add(bank_txn)
    session.commit()
    session.refresh(bank_txn)
    assert bank_txn.bank_transaction_id is not None
    _ok(f"BankTransaction bank_transaction_id={bank_txn.bank_transaction_id}")

    case = ReconciliationCase(
        payment_id=payment.payment_id,
        settlement_id=settlement.settlement_id,
        bank_transaction_id=bank_txn.bank_transaction_id,
        status="matched",
        confidence=0.99,
        expected_amount=Decimal("758.90"),
        actual_amount=Decimal("758.90"),
        difference_amount=Decimal("0.00"),
        explanation="CRUD test matched case",
    )
    session.add(case)
    session.commit()
    session.refresh(case)
    assert case.case_id is not None
    _ok(f"ReconciliationCase case_id={case.case_id}")

    return {
        "order_id": order.order_id,
        "payment_id": payment.payment_id,
        "settlement_id": settlement.settlement_id,
        "adjustment_id": adjustment.adjustment_id,
        "bank_transaction_id": bank_txn.bank_transaction_id,
        "case_id": case.case_id,
    }


def update_rows(session: Session, ids: dict[str, int]) -> None:
    print("\n[UPDATE] mutate and verify")

    payment = session.get(Payment, ids["payment_id"])
    assert payment is not None
    payment.sqlmodel_update({"status": "settled", "provider_reference": "crud_test_pay_001_upd"})
    session.add(payment)
    session.commit()
    session.refresh(payment)
    assert payment.status == "settled"
    assert payment.provider_reference == "crud_test_pay_001_upd"
    _ok("Payment status/provider_reference via sqlmodel_update")

    case = session.get(ReconciliationCase, ids["case_id"])
    assert case is not None
    case.status = "reviewed"
    case.confidence = 1.0
    case.explanation = "CRUD test updated explanation"
    session.add(case)
    session.commit()
    session.refresh(case)
    assert case.status == "reviewed"
    assert case.confidence == 1.0
    _ok("ReconciliationCase direct field assignment")

    order = session.get(Order, ids["order_id"])
    assert order is not None
    order.gross_amount = Decimal("780.00")
    session.add(order)
    session.commit()
    session.refresh(order)
    assert order.gross_amount == Decimal("780.00")
    _ok("Order gross_amount")

    # Filtered read after update
    settled = session.exec(
        select(Payment).where(Payment.provider_reference == "crud_test_pay_001_upd")
    ).one()
    assert settled.payment_id == ids["payment_id"]
    _ok("select(...).one() after update")


def delete_chain(session: Session, ids: dict[str, int]) -> None:
    print("\n[DELETE] reverse FK order")

    case = session.get(ReconciliationCase, ids["case_id"])
    assert case is not None
    session.delete(case)
    session.commit()
    assert session.get(ReconciliationCase, ids["case_id"]) is None
    _ok("ReconciliationCase")

    adjustment = session.get(Adjustment, ids["adjustment_id"])
    assert adjustment is not None
    session.delete(adjustment)
    session.commit()
    assert session.get(Adjustment, ids["adjustment_id"]) is None
    _ok("Adjustment")

    settlement = session.get(Settlement, ids["settlement_id"])
    assert settlement is not None
    session.delete(settlement)
    session.commit()
    assert session.get(Settlement, ids["settlement_id"]) is None
    _ok("Settlement")

    bank_txn = session.get(BankTransaction, ids["bank_transaction_id"])
    assert bank_txn is not None
    session.delete(bank_txn)
    session.commit()
    assert session.get(BankTransaction, ids["bank_transaction_id"]) is None
    _ok("BankTransaction")

    payment = session.get(Payment, ids["payment_id"])
    assert payment is not None
    session.delete(payment)
    session.commit()
    assert session.get(Payment, ids["payment_id"]) is None
    _ok("Payment")

    order = session.get(Order, ids["order_id"])
    assert order is not None
    session.delete(order)
    session.commit()
    assert session.get(Order, ids["order_id"]) is None
    _ok("Order")


def main() -> None:
    engine = create_engine(DATABASE_STRING)
    try:
        with Session(engine) as session:
            print("SQLModel CRUD check against Supabase")
            read_existing(session)
            ids = create_chain(session)
            update_rows(session, ids)
            delete_chain(session, ids)
            print("\nAll CRUD operations passed.")
    except Exception as err:
        print(f"\nCRUD check failed: {err}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
