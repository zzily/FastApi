from tests.integration.base import BaseApiTestCase


class SalaryLogApiTests(BaseApiTestCase):
    def test_update_salary_log_preserves_month_when_omitted(self):
        create_response = self.client.post(
            "/salary_logs/",
            json={
                "amount": 100,
                "month": "2024-01",
                "source": "salary",
                "remark": "初始入账",
            },
        )
        salary_log_id = create_response.json()["data"]["id"]

        update_response = self.client.put(
            f"/salary_logs/{salary_log_id}",
            json={"amount": 120, "source": "salary", "remark": "调整金额"},
        )

        self.assertEqual(update_response.status_code, 200)
        body = update_response.json()
        self.assertEqual(body["month"], "2024-01")
        self.assertEqual(body["remark"], "调整金额")
        self.assertEqual(body["amount"], 120.0)
        self.assertEqual(body["amount_unused"], 120.0)
