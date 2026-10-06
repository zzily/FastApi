from datetime import datetime, timedelta

from app.core.time import now_local
from app.models import Transaction
from tests.integration.base import BaseApiTestCase


class TransactionDateTests(BaseApiTestCase):
    def test_backdated_expense_is_persisted_and_summarized_in_occurrence_month(self):
        response = self.client.post(
            "/transactions/",
            json={
                "title": "补录九月支出",
                "amount_out": 300,
                "category": "personal",
                "occurred_at": "2026-09-30",
            },
        )
        self.assertEqual(response.status_code, 200)
        record_id = response.json()["data"]["id"]
        with self.testing_session_local() as db:
            db.get(Transaction, record_id).created_at = datetime(2026, 10, 6, 12)
            db.commit()
        record = self.client.get("/transactions/").json()["data"][0]
        self.assertEqual(record["occurred_at"], "2026-09-30")
        self.assertFalse(record["occurred_at_inferred"])
        september = self.client.get("/summary?month=2026-09").json()["data"]
        october = self.client.get("/summary?month=2026-10").json()["data"]
        self.assertEqual(
            september["financial_status"]["family_loop"]["personal_spending"], 300
        )
        self.assertEqual(
            october["financial_status"]["family_loop"]["personal_spending"], 0
        )
        self.assertEqual(
            september["chart_data"]["monthly_timeline"][0]["spending_personal"], 300
        )
        updated = self.client.put(
            f"/transactions/{record_id}", json={"occurred_at": "2026-08-31"}
        ).json()["data"]
        self.assertEqual(updated["occurred_at"], "2026-08-31")
        self.assertTrue(updated["created_at"].startswith("2026-10-06"))

    def test_omitted_date_defaults_today_and_partial_update_keeps_it(self):
        record_id = self.client.post(
            "/transactions/", json={"title": "今天", "amount_out": 10}
        ).json()["data"]["id"]
        record = self.client.put(
            f"/transactions/{record_id}", json={"title": "保留日期"}
        ).json()["data"]
        self.assertEqual(record["occurred_at"], now_local().date().isoformat())
        self.assertEqual(
            self.client.put(
                f"/transactions/{record_id}", json={"occurred_at": None}
            ).status_code,
            400,
        )
        future = (now_local().date() + timedelta(days=1)).isoformat()
        self.assertEqual(
            self.client.post(
                "/transactions/",
                json={"title": "未来", "amount_out": 10, "occurred_at": future},
            ).status_code,
            400,
        )

    def test_month_report_separates_cohort_outstanding_and_current_receivable(self):
        self.client.post(
            "/transactions/",
            json={
                "title": "九月工作",
                "amount_out": 100,
                "category": "work",
                "occurred_at": "2026-09-30",
            },
        )
        self.client.post(
            "/transactions/",
            json={
                "title": "十月工作",
                "amount_out": 50,
                "category": "work",
                "occurred_at": "2026-10-01",
            },
        )
        self.client.post(
            "/salary_logs/",
            json={"amount": 100, "source": "reimbursement", "month": "2026-10"},
        )
        summary = self.client.get("/summary?month=2026-09").json()["data"]
        self.assertEqual(
            summary["financial_status"]["business_loop"]["period_outstanding"], 100
        )
        self.assertEqual(
            summary["financial_status"]["business_loop"]["current_debt"], 50
        )
        self.assertEqual(summary["operational_status"]["cash_waiting_allocation"], 100)
        self.assertEqual(summary["operational_status"]["bills_pending_settlement"], 150)
