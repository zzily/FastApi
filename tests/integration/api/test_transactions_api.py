from tests.integration.base import BaseApiTestCase


class TransactionApiTests(BaseApiTestCase):
    def test_list_transactions_returns_envelope(self):
        response = self.client.get("/transactions/")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["message"], "获取账单成功")
        self.assertEqual(body["data"], [])

    def test_create_and_list_transactions(self):
        create_response = self.client.post(
            "/transactions/",
            json={"title": "垫付办公用品", "amount_out": 88.5, "category": "work"},
        )

        self.assertEqual(create_response.status_code, 200)
        create_body = create_response.json()
        self.assertEqual(create_body["code"], 200)
        self.assertGreater(create_body["data"]["id"], 0)

        list_response = self.client.get("/transactions/", params={"unpaid_only": True})

        self.assertEqual(list_response.status_code, 200)
        body = list_response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(len(body["data"]), 1)
        self.assertEqual(body["data"][0]["title"], "垫付办公用品")
        self.assertEqual(body["data"][0]["status"], "pending")

    def test_update_transaction_returns_updated_entity(self):
        create_response = self.client.post(
            "/transactions/",
            json={"title": "初始账单", "amount_out": 88.5, "category": "work"},
        )
        transaction_id = create_response.json()["data"]["id"]

        update_response = self.client.put(
            f"/transactions/{transaction_id}",
            json={"title": "更新后的账单", "amount_out": 120, "category": "personal"},
        )

        self.assertEqual(update_response.status_code, 200)
        body = update_response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["message"], "账单更新成功")
        self.assertEqual(body["data"]["id"], transaction_id)
        self.assertEqual(body["data"]["title"], "更新后的账单")
        self.assertEqual(body["data"]["category"], "personal")
        self.assertEqual(body["data"]["amount_out"], 120.0)
        self.assertEqual(body["data"]["amount_reimbursed"], 0.0)
        self.assertEqual(body["data"]["status"], "pending")

    def test_delete_transaction_returns_stable_message_when_linked_settlements_exist(self):
        transaction_response = self.client.post(
            "/transactions/",
            json={"title": "关联账单", "amount_out": 100, "category": "work"},
        )
        transaction_id = transaction_response.json()["data"]["id"]

        salary_response = self.client.post(
            "/salary_logs/",
            json={
                "amount": 100,
                "month": "2024-02",
                "source": "reimbursement",
                "remark": "关联回款",
            },
        )
        salary_log_id = salary_response.json()["data"]["id"]

        settle_response = self.client.post(
            "/settle",
            json={"transaction_id": transaction_id, "salary_log_id": salary_log_id, "amount": 60},
        )
        self.assertEqual(settle_response.status_code, 200)

        delete_response = self.client.delete(f"/transactions/{transaction_id}")

        self.assertEqual(delete_response.status_code, 400)
        body = delete_response.json()
        self.assertEqual(body["code"], 400)
        self.assertEqual(
            body["message"],
            "该账单已有 1 条核销记录，无法直接删除。请先撤销相关核销。",
        )
        self.assertIsNone(body["data"])
