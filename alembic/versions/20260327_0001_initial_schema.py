"""Initial schema

Revision ID: 20260327_0001
Revises:
Create Date: 2026-03-27 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260327_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.Enum("work", "personal", name="category"), nullable=True),
        sa.Column("amount_out", sa.Numeric(10, 2), nullable=False),
        sa.Column("amount_reimbursed", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "partially_settled", "settled", name="transactionstatus"),
            nullable=True,
        ),
        sa.Column("receipt_url", sa.String(length=512), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_status"), "transactions", ["status"], unique=False)

    op.create_table(
        "salary_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("amount_unused", sa.Numeric(10, 2), nullable=False),
        sa.Column("month", sa.String(length=20), nullable=False),
        sa.Column(
            "source",
            sa.Enum("salary", "reimbursement", "other", name="incomesource"),
            nullable=True,
        ),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("received_date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "transaction_settlements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("salary_log_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["salary_log_id"], ["salary_logs.id"]),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("transaction_settlements")
    op.drop_table("salary_logs")
    op.drop_index(op.f("ix_transactions_status"), table_name="transactions")
    op.drop_table("transactions")
