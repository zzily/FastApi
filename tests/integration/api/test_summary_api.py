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
