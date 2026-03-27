from datetime import datetime

from app.models import Transaction
from tests.integration.base import BaseApiTestCase


class SummaryApiTests(BaseApiTestCase):
    def test_summary_returns_aggregated_financial_overview(self):
        self.client.post(
            "/transactions/",
            json={"title": "工作垫付", "amount_out": 100, "category": "work"},
        )
        self.client.post(
            "/transactions/",
            json={"title": "家庭消费", "amount_out": 20, "category": "personal"},
        )
        self.client.post(
            "/salary_logs/",
            json={"amount": 200, "month": "2026-03", "source": "salary", "remark": "工资"},
        )
        self.client.post(
            "/salary_logs/",
            json={"amount": 30, "month": "2026-03", "source": "reimbursement", "remark": "报销"},
        )

        response = self.client.get("/summary")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["data"]["financial_status"]["business_loop"]["total_lent"], 100.0)
        self.assertEqual(body["data"]["financial_status"]["business_loop"]["total_reimbursed"], 30.0)
        self.assertEqual(body["data"]["financial_status"]["business_loop"]["current_debt"], 70.0)
        self.assertEqual(body["data"]["financial_status"]["family_loop"]["gross_income"], 200.0)
        self.assertEqual(body["data"]["financial_status"]["family_loop"]["personal_spending"], 20.0)
        self.assertEqual(body["data"]["financial_status"]["total_assets"], 350.0)
        self.assertEqual(body["data"]["operational_status"]["bills_pending_settlement"], 120.0)
        self.assertEqual(body["data"]["operational_status"]["cash_waiting_allocation"], 230.0)
        self.assertEqual(body["data"]["operational_status"]["action_needed"], "有闲钱，快去销账")

    def test_summary_can_filter_by_month(self):
        march_work = self.client.post(
            "/transactions/",
            json={"title": "March work", "amount_out": 100, "category": "work"},
        )
        march_work_id = march_work.json()["data"]["id"]

        march_personal = self.client.post(
            "/transactions/",
            json={"title": "March personal", "amount_out": 20, "category": "personal"},
        )
        march_personal_id = march_personal.json()["data"]["id"]

        april_work = self.client.post(
            "/transactions/",
            json={"title": "April work", "amount_out": 60, "category": "work"},
        )
        april_work_id = april_work.json()["data"]["id"]

        with self.testing_session_local() as db:
            db.get(Transaction, march_work_id).created_at = datetime(2026, 3, 10, 12, 0, 0)
            db.get(Transaction, march_personal_id).created_at = datetime(2026, 3, 11, 12, 0, 0)
            db.get(Transaction, april_work_id).created_at = datetime(2026, 4, 2, 12, 0, 0)
            db.commit()

        self.client.post(
            "/salary_logs/",
            json={"amount": 200, "month": "2026-03", "source": "salary", "remark": "March salary"},
        )
        self.client.post(
            "/salary_logs/",
            json={"amount": 30, "month": "2026-03", "source": "reimbursement", "remark": "March reimbursement"},
        )
        self.client.post(
            "/salary_logs/",
            json={"amount": 500, "month": "2026-04", "source": "salary", "remark": "April salary"},
        )

        response = self.client.get("/summary", params={"month": "2026-03"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["data"]["financial_status"]["business_loop"]["total_lent"], 100.0)
        self.assertEqual(body["data"]["financial_status"]["business_loop"]["total_reimbursed"], 30.0)
        self.assertEqual(body["data"]["financial_status"]["family_loop"]["gross_income"], 200.0)
        self.assertEqual(body["data"]["financial_status"]["family_loop"]["personal_spending"], 20.0)
        self.assertEqual(body["data"]["operational_status"]["cash_waiting_allocation"], 230.0)
        self.assertEqual(body["data"]["operational_status"]["bills_pending_settlement"], 120.0)
        self.assertEqual(len(body["data"]["chart_data"]["monthly_timeline"]), 1)
        self.assertEqual(body["data"]["chart_data"]["monthly_timeline"][0]["month"], "2026-03")
