from tests.integration.base import BaseApiTestCase


class QuickPaymentTests(BaseApiTestCase):
    def income(self, amount=100):
        return self.client.post(
            "/salary_logs/",
            json={"amount": amount, "source": "salary", "month": "2026-10"},
        ).json()["data"]["id"]

    def test_records_consumption_and_payment_atomically_and_can_undo(self):
        income_id = self.income()
        created = self.client.post(
            "/transactions/",
            json={
                "title": "超市消费",
                "category": "personal",
                "amount_out": 40.05,
                "payment_salary_log_id": income_id,
            },
        )
        self.assertEqual(created.status_code, 200)
        transaction_id = created.json()["data"]["id"]
        transaction = self.client.get("/transactions/").json()["data"][0]
        self.assertEqual(transaction["status"], "settled")
        self.assertEqual(transaction["amount_reimbursed"], 40.05)
        self.assertEqual(
            self.client.get("/salary_logs/").json()["data"][0]["amount_unused"], 59.95
        )
        history = self.client.get(f"/transactions/{transaction_id}/settlements").json()[
            "data"
        ]
        self.assertEqual(len(history), 1)
        self.client.delete(f'/settlements/{history[0]["id"]}')
        self.assertEqual(
            self.client.get("/salary_logs/").json()["data"][0]["amount_unused"], 100
        )
        self.assertEqual(
            self.client.get("/transactions/").json()["data"][0]["status"], "pending"
        )

    def test_insufficient_income_and_invalid_amount_leave_ledger_unchanged(self):
        income_id = self.income(10)
        response = self.client.post(
            "/transactions/",
            json={
                "title": "超额支出",
                "category": "personal",
                "amount_out": 11,
                "payment_salary_log_id": income_id,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/transactions/").json()["data"], [])
        self.assertEqual(
            self.client.get("/salary_logs/").json()["data"][0]["amount_unused"], 10
        )
        for amount in [0, -1, 1.001]:
            self.assertEqual(
                self.client.post(
                    "/transactions/", json={"title": "无效", "amount_out": amount}
                ).status_code,
                422,
            )

    def test_cannot_use_quick_payment_for_work_bill(self):
        income_id = self.income()
        response = self.client.post(
            "/transactions/",
            json={
                "title": "工作垫付",
                "category": "work",
                "amount_out": 10,
                "payment_salary_log_id": income_id,
            },
        )
        self.assertEqual(response.status_code, 400)
