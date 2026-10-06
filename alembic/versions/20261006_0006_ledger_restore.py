"""Serialize writes for atomic backups and record restore idempotency."""

from alembic import op
import sqlalchemy as sa

revision = "20261006_0006"
down_revision = "20261006_0005"
branch_labels = None
depends_on = None


def upgrade():
    guard = op.create_table(
        "ledger_guard",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
    )
    op.bulk_insert(guard, [{"id": 1, "revision": 0}])
    op.create_table(
        "ledger_restores",
        sa.Column("checksum", sa.String(64), primary_key=True),
        sa.Column("restored_at", sa.DateTime(), nullable=False),
        sa.Column("counts", sa.JSON(), nullable=False),
    )


def downgrade():
    op.drop_table("ledger_restores")
    op.drop_table("ledger_guard")
