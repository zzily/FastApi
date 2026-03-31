"""Extend trade records with structured review fields

Revision ID: 20260331_0003
Revises: 20260331_0002
Create Date: 2026-03-31 00:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260331_0003"
down_revision: Union[str, Sequence[str], None] = "20260331_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


trade_plan_clarity_enum = sa.Enum("clear", "mixed", "missing", name="tradeplanclarity")
trade_execution_quality_enum = sa.Enum(
    "disciplined",
    "drifted",
    "broken",
    name="tradeexecutionquality",
)
trade_option_right_enum = sa.Enum("call", "put", name="tradeoptionright")
trade_option_structure_enum = sa.Enum(
    "single",
    "vertical_spread",
    "iron_condor",
    "straddle",
    "strangle",
    "other",
    name="tradeoptionstructure",
)
trade_premium_type_enum = sa.Enum("debit", "credit", name="tradepremiumtype")


def upgrade() -> None:
    op.add_column("trade_records", sa.Column("entry_at", sa.DateTime(), nullable=True))
    op.add_column("trade_records", sa.Column("exit_at", sa.DateTime(), nullable=True))
    op.add_column("trade_records", sa.Column("entry_price", sa.Numeric(18, 6), nullable=True))
    op.add_column("trade_records", sa.Column("exit_price", sa.Numeric(18, 6), nullable=True))
    op.add_column("trade_records", sa.Column("position_size", sa.Numeric(18, 4), nullable=True))
    op.add_column("trade_records", sa.Column("thesis", sa.Text(), nullable=True))
    op.add_column("trade_records", sa.Column("planned_stop", sa.Numeric(18, 6), nullable=True))
    op.add_column("trade_records", sa.Column("planned_target", sa.Numeric(18, 6), nullable=True))
    op.add_column("trade_records", sa.Column("actual_stop", sa.Numeric(18, 6), nullable=True))
    op.add_column("trade_records", sa.Column("actual_target", sa.Numeric(18, 6), nullable=True))
    op.add_column("trade_records", sa.Column("fees", sa.Numeric(18, 4), nullable=True))
    op.add_column("trade_records", sa.Column("slippage", sa.Numeric(18, 4), nullable=True))
    op.add_column("trade_records", sa.Column("followed_plan", sa.Boolean(), nullable=True))
    op.add_column("trade_records", sa.Column("plan_clarity", trade_plan_clarity_enum, nullable=True))
    op.add_column(
        "trade_records",
        sa.Column("execution_quality", trade_execution_quality_enum, nullable=True),
    )
    op.add_column("trade_records", sa.Column("mistake_tags", sa.JSON(), nullable=True))
    op.add_column("trade_records", sa.Column("lesson", sa.Text(), nullable=True))
    op.add_column("trade_records", sa.Column("option_expiration", sa.Date(), nullable=True))
    op.add_column("trade_records", sa.Column("option_strike", sa.Numeric(18, 6), nullable=True))
    op.add_column("trade_records", sa.Column("option_right", trade_option_right_enum, nullable=True))
    op.add_column(
        "trade_records",
        sa.Column("option_structure", trade_option_structure_enum, nullable=True),
    )
    op.add_column(
        "trade_records",
        sa.Column("option_premium_type", trade_premium_type_enum, nullable=True),
    )
    op.add_column("trade_records", sa.Column("option_max_risk", sa.Numeric(18, 4), nullable=True))
    op.add_column("trade_records", sa.Column("option_max_reward", sa.Numeric(18, 4), nullable=True))
    op.add_column("trade_records", sa.Column("option_delta", sa.Numeric(10, 4), nullable=True))

    op.execute("UPDATE trade_records SET mistake_tags = '[]' WHERE mistake_tags IS NULL")


def downgrade() -> None:
    op.drop_column("trade_records", "option_delta")
    op.drop_column("trade_records", "option_max_reward")
    op.drop_column("trade_records", "option_max_risk")
    op.drop_column("trade_records", "option_premium_type")
    op.drop_column("trade_records", "option_structure")
    op.drop_column("trade_records", "option_right")
    op.drop_column("trade_records", "option_strike")
    op.drop_column("trade_records", "option_expiration")
    op.drop_column("trade_records", "lesson")
    op.drop_column("trade_records", "mistake_tags")
    op.drop_column("trade_records", "execution_quality")
    op.drop_column("trade_records", "plan_clarity")
    op.drop_column("trade_records", "followed_plan")
    op.drop_column("trade_records", "slippage")
    op.drop_column("trade_records", "fees")
    op.drop_column("trade_records", "actual_target")
    op.drop_column("trade_records", "actual_stop")
    op.drop_column("trade_records", "planned_target")
    op.drop_column("trade_records", "planned_stop")
    op.drop_column("trade_records", "thesis")
    op.drop_column("trade_records", "position_size")
    op.drop_column("trade_records", "exit_price")
    op.drop_column("trade_records", "entry_price")
    op.drop_column("trade_records", "exit_at")
    op.drop_column("trade_records", "entry_at")

    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        trade_premium_type_enum.drop(bind, checkfirst=True)
        trade_option_structure_enum.drop(bind, checkfirst=True)
        trade_option_right_enum.drop(bind, checkfirst=True)
        trade_execution_quality_enum.drop(bind, checkfirst=True)
        trade_plan_clarity_enum.drop(bind, checkfirst=True)
