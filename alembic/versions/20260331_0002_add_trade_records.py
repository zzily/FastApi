"""Add trade records

Revision ID: 20260331_0002
Revises: 20260327_0001
Create Date: 2026-03-31 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260331_0002"
down_revision: Union[str, Sequence[str], None] = "20260327_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trade_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=255), nullable=False),
        sa.Column(
            "market",
            sa.Enum("stock", "crypto", "futures", "forex", "options", "other", name="trademarket"),
            nullable=False,
        ),
        sa.Column(
            "side",
            sa.Enum("long", "short", name="tradeside"),
            nullable=False,
        ),
        sa.Column("traded_at", sa.Date(), nullable=False),
        sa.Column("pnl", sa.Numeric(12, 2), nullable=False),
        sa.Column("setup", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trade_records_symbol"), "trade_records", ["symbol"], unique=False)
    op.create_index(op.f("ix_trade_records_traded_at"), "trade_records", ["traded_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trade_records_traded_at"), table_name="trade_records")
    op.drop_index(op.f("ix_trade_records_symbol"), table_name="trade_records")
    op.drop_table("trade_records")

    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        sa.Enum(name="tradeside").drop(bind, checkfirst=True)
        sa.Enum(name="trademarket").drop(bind, checkfirst=True)
