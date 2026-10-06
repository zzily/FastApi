from dataclasses import replace
from unittest.mock import patch
from app.core.config import settings
from app.models import ExpenseCategory, LedgerRestore
from app.modules.ledger import repository, service
from tests.fixtures.ledger import snapshot
from tests.integration.base import BaseApiTestCase


class LedgerApiTests(BaseApiTestCase):
    def setUp(self):
        super().setUp()
        self.settings_patch = patch(
            "app.modules.ledger.router.settings",
            replace(settings, ledger_restore_token="test-only"),
        )
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.headers = {"x-ledger-restore-key": "test-only"}

    def test_restore_round_trip_preserves_links_precision_and_is_idempotent(self):
        with self.testing_session_local() as db:
            db.add(ExpenseCategory(name="其他", kind="personal", archived=False))
            db.commit()
        data = snapshot().model_dump(mode="json")
        preview = self.client.post(
            "/ledger/restore/preview", json=data, headers=self.headers
        )
        self.assertTrue(preview.json()["data"]["can_restore"])
        response = self.client.post("/ledger/restore", json=data, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        bill = self.client.get("/transactions/").json()["data"][0]
        self.assertEqual(bill["occurred_at"], "2026-09-30")
        self.assertEqual(bill["expense_category_name"], "餐饮")
        self.assertNotEqual(bill["expense_category_id"], 7)
        exported = self.client.get("/ledger/backup").json()["data"]
        self.assertEqual(
            exported["ledger"]["transactions"][0]["receipt_url"],
            "https://example.test/receipt",
        )
        self.assertEqual(
            exported["ledger"]["trade_records"][0]["entry_price"], "1.123456"
        )
        self.assertEqual(exported["ledger"]["trade_records"][0]["lesson"], "遵守计划")
        settlement = exported["ledger"]["settlements"][0]
        self.assertEqual(settlement["transaction_id"], bill["id"])
        replay = self.client.post("/ledger/restore", json=data, headers=self.headers)
        self.assertTrue(replay.json()["data"]["already_restored"])
        self.assertEqual(len(self.client.get("/transactions/").json()["data"]), 1)
        self.client.delete(f'/settlements/{settlement["id"]}')
        self.assertEqual(
            self.client.get("/salary_logs/").json()["data"][0]["amount_unused"], 100
        )

    def test_authorization_and_nonempty_guard(self):
        data = snapshot().model_dump(mode="json")
        self.assertEqual(
            self.client.post("/ledger/restore", json=data).status_code, 401
        )
        with patch(
            "app.modules.ledger.router.settings",
            replace(settings, ledger_restore_token=""),
        ):
            self.assertFalse(
                self.client.get("/ledger/capabilities").json()["data"]["restore"]
            )
            self.assertEqual(
                self.client.post(
                    "/ledger/restore", json=data, headers=self.headers
                ).status_code,
                403,
            )
        self.client.post(
            "/transactions/",
            json={"title": "已有记录", "amount_out": 2, "category": "personal"},
        )
        self.assertFalse(
            self.client.post(
                "/ledger/restore/preview", json=data, headers=self.headers
            ).json()["data"]["can_restore"]
        )
        self.assertEqual(
            self.client.post(
                "/ledger/restore", json=data, headers=self.headers
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.get("/transactions/").json()["data"][0]["title"], "已有记录"
        )

    def test_commit_failure_rolls_back_entire_restore(self):
        with self.testing_session_local() as db:
            with patch.object(
                db, "commit", side_effect=RuntimeError("simulated database failure")
            ):
                with self.assertRaises(RuntimeError):
                    service.restore_backup(db, snapshot())
            self.assertFalse(any(repository.financial_counts(db).values()))
            self.assertEqual(db.query(ExpenseCategory).count(), 0)
            self.assertEqual(db.query(LedgerRestore).count(), 0)

    def test_snapshot_export_includes_more_than_default_page_size(self):
        from app.models import Transaction
        from datetime import date

        with self.testing_session_local() as db:
            db.add_all(
                [
                    Transaction(
                        title=f"账单{i}",
                        amount_out=1,
                        amount_reimbursed=0,
                        category="personal",
                        status="pending",
                        occurred_at=date(2026, 9, 1),
                    )
                    for i in range(105)
                ]
            )
            db.commit()
        self.assertEqual(len(self.client.get("/transactions/").json()["data"]), 100)
        self.assertEqual(
            len(
                self.client.get("/ledger/backup").json()["data"]["ledger"][
                    "transactions"
                ]
            ),
            105,
        )
