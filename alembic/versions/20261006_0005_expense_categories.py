"""Add user managed expense categories without changing work/personal grouping."""

from alembic import op
import sqlalchemy as sa

revision = "20261006_0005"
down_revision = "20261006_0004"
branch_labels = None
depends_on = None


def upgrade():
    categories = op.create_table(
        "expense_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("kind", sa.Enum("work", "personal", name="category"), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("name", "kind", name="uq_expense_category_name_kind"),
    )
    defaults = [
        ("餐饮", "personal"),
        ("居家", "personal"),
        ("交通", "personal"),
        ("购物", "personal"),
        ("医疗", "personal"),
        ("其他", "personal"),
        ("差旅", "work"),
        ("办公", "work"),
    ]
    op.bulk_insert(
        categories,
        [{"name": name, "kind": kind, "archived": False} for name, kind in defaults],
    )
    with op.batch_alter_table("transactions") as batch:
        batch.add_column(sa.Column("expense_category_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_transactions_expense_category",
            "expense_categories",
            ["expense_category_id"],
            ["id"],
        )
        batch.create_index(
            "ix_transactions_expense_category_id", ["expense_category_id"]
        )


def downgrade():
    with op.batch_alter_table("transactions") as batch:
        batch.drop_constraint("fk_transactions_expense_category", type_="foreignkey")
        batch.drop_index("ix_transactions_expense_category_id")
        batch.drop_column("expense_category_id")
    op.drop_table("expense_categories")
