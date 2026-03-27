from tests.integration.base import BaseApiTestCase


class SalaryLogApiTests(BaseApiTestCase):
    def test_list_salary_logs_returns_envelope(self):
        response = self.client.get("/salary_logs/")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["message"], "获取回款记录成功")
        self.assertEqual(body["data"], [])

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
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["message"], "回款记录更新成功")
        self.assertEqual(body["data"]["id"], salary_log_id)
        self.assertEqual(body["data"]["month"], "2024-01")
        self.assertEqual(body["data"]["remark"], "调整金额")
        self.assertEqual(body["data"]["amount"], 120.0)
        self.assertEqual(body["data"]["amount_unused"], 120.0)

    def test_delete_salary_log_returns_stable_message_when_linked_settlements_exist(self):
        transaction_response = self.client.post(
            "/transactions/",
            json={"title": "关联账单", "amount_out": 120, "category": "work"},
        )
        transaction_id = transaction_response.json()["data"]["id"]

        salary_response = self.client.post(
            "/salary_logs/",
            json={
                "amount": 120,
                "month": "2024-03",
                "source": "salary",
                "remark": "关联回款",
            },
        )
        salary_log_id = salary_response.json()["data"]["id"]

        settle_response = self.client.post(
            "/settle",
            json={"transaction_id": transaction_id, "salary_log_id": salary_log_id, "amount": 80},
        )
        self.assertEqual(settle_response.status_code, 200)

        delete_response = self.client.delete(f"/salary_logs/{salary_log_id}")

        self.assertEqual(delete_response.status_code, 400)
        body = delete_response.json()
        self.assertEqual(body["code"], 400)
        self.assertEqual(
            body["message"],
            "该回款已被 1 条核销记录引用，无法直接删除。请先撤销相关核销。",
        )
        self.assertIsNone(body["data"])
