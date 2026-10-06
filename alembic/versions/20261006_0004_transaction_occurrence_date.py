"""Keep expense occurrence date separate from recording time."""

from datetime import datetime
import os
from zoneinfo import ZoneInfo

from alembic import op
import sqlalchemy as sa

revision = "20261006_0004"
down_revision = "20260331_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("transactions", sa.Column("occurred_at", sa.Date(), nullable=True))
    op.add_column(
        "transactions",
        sa.Column(
            "occurred_at_inferred",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    transactions = sa.table(
        "transactions",
        sa.column("occurred_at", sa.Date()),
        sa.column("created_at", sa.DateTime()),
    )
    today = datetime.now(ZoneInfo(os.getenv("APP_TIMEZONE", "Asia/Shanghai"))).date()
    # Existing naive datetime values are ledger wall times; retain their calendar day.
    op.execute(
        transactions.update().values(
            occurred_at=sa.func.coalesce(sa.func.date(transactions.c.created_at), today)
        )
    )
    with op.batch_alter_table("transactions") as batch:
        batch.alter_column("occurred_at", existing_type=sa.Date(), nullable=False)
        batch.alter_column(
            "occurred_at_inferred",
            existing_type=sa.Boolean(),
            server_default=sa.false(),
        )
        batch.create_index("ix_transactions_occurred_at", ["occurred_at"])


def downgrade():
    with op.batch_alter_table("transactions") as batch:
        batch.drop_index("ix_transactions_occurred_at")
        batch.drop_column("occurred_at_inferred")
        batch.drop_column("occurred_at")
