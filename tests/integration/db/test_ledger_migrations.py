import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class LedgerMigrationTests(unittest.TestCase):
    def test_existing_settled_history_survives_upgrade_and_rollback(self):
        with TemporaryDirectory(prefix="finance-migration-") as temp:
            path = Path(temp) / "ledger.db"
            env = {
                **os.environ,
                "DATABASE_URL": f"sqlite:///{path}",
                "APP_TIMEZONE": "Asia/Shanghai",
            }

            def migrate(revision, direction="upgrade"):
                result = subprocess.run(
                    [sys.executable, "-m", "alembic", direction, revision],
                    env=env,
                    cwd=Path(__file__).resolve().parents[3],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            migrate("20260331_0003")
            with sqlite3.connect(path) as db:
                db.execute(
                    "INSERT INTO transactions(id,title,category,amount_out,amount_reimbursed,status,created_at) VALUES (1,'旧账单','personal',100,40,'partially_settled','2026-09-30 23:30:00')"
                )
                db.execute(
                    "INSERT INTO salary_logs(id,amount,amount_unused,month,source,received_date) VALUES (1,100,60,'2026-09','salary','2026-09-29 09:00:00')"
                )
                db.execute(
                    "INSERT INTO transaction_settlements(id,transaction_id,salary_log_id,amount) VALUES (1,1,1,40)"
                )
            migrate("head")
            with sqlite3.connect(path) as db:
                self.assertEqual(
                    db.execute(
                        "SELECT occurred_at,occurred_at_inferred,amount_reimbursed,status FROM transactions"
                    ).fetchone(),
                    ("2026-09-30", 1, 40, "partially_settled"),
                )
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM expense_categories").fetchone()[0],
                    8,
                )
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM ledger_guard").fetchone()[0], 1
                )
                self.assertEqual(
                    db.execute("SELECT amount FROM transaction_settlements").fetchone()[
                        0
                    ],
                    40,
                )
            migrate("20260331_0003", "downgrade")
            with sqlite3.connect(path) as db:
                self.assertEqual(
                    db.execute(
                        "SELECT amount_reimbursed,status FROM transactions"
                    ).fetchone(),
                    (40, "partially_settled"),
                )
                self.assertEqual(
                    db.execute("SELECT amount_unused FROM salary_logs").fetchone()[0],
                    60,
                )
            migrate("head")
