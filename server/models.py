from datetime import datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    order_id: int | None = Field(default=None, primary_key=True)
    customer_id: int
    merchant_id: int
    gross_amount: Decimal = Field(max_digits=12, decimal_places=2)
    currency: str


class BankTransaction(SQLModel, table=True):
    __tablename__ = "bank_transactions"

    bank_transaction_id: int | None = Field(default=None, primary_key=True)
    transaction_date: datetime
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    description: str
    reference: str


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    payment_id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.order_id")
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    payment_date: datetime
    provider_reference: str
    status: str


class Settlement(SQLModel, table=True):
    __tablename__ = "settlements"

    settlement_id: int | None = Field(default=None, primary_key=True)
    payment_id: int = Field(foreign_key="payments.payment_id")
    gross_amount: Decimal = Field(max_digits=12, decimal_places=2)
    fee_amount: Decimal = Field(max_digits=12, decimal_places=2)
    tax_amount: Decimal = Field(max_digits=12, decimal_places=2)
    adjustment_amount: Decimal = Field(max_digits=12, decimal_places=2)
    net_amount: Decimal = Field(max_digits=12, decimal_places=2)
    settlement_date: datetime


class Adjustment(SQLModel, table=True):
    __tablename__ = "adjustments"

    adjustment_id: int | None = Field(default=None, primary_key=True)
    settlement_id: int = Field(foreign_key="settlements.settlement_id")
    type: str
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    reason: str


class ReconciliationCase(SQLModel, table=True):
    __tablename__ = "reconciliation_cases"

    case_id: int | None = Field(default=None, primary_key=True)
    payment_id: int = Field(foreign_key="payments.payment_id")
    settlement_id: int | None = Field(default=None, foreign_key="settlements.settlement_id")
    bank_transaction_id: int | None = Field(
        default=None, foreign_key="bank_transactions.bank_transaction_id"
    )
    status: str
    confidence: float
    expected_amount: Decimal = Field(max_digits=12, decimal_places=2)
    actual_amount: Decimal = Field(max_digits=12, decimal_places=2)
    difference_amount: Decimal = Field(max_digits=12, decimal_places=2)
    explanation: str
