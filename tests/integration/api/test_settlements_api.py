from tests.integration.base import BaseApiTestCase


class SettlementApiTests(BaseApiTestCase):
    def test_settlement_workflow_round_trip(self):
        transaction_response = self.client.post(
            "/transactions/",
            json={"title": "客户垫付", "amount_out": 100, "category": "work"},
        )
        transaction_id = transaction_response.json()["data"]["id"]

        salary_response = self.client.post(
            "/salary_logs/",
            json={
                "amount": 100,
                "month": "2024-02",
                "source": "reimbursement",
                "remark": "老板回款",
            },
        )
        salary_log_id = salary_response.json()["data"]["id"]

        settle_response = self.client.post(
            "/settle",
            json={"transaction_id": transaction_id, "salary_log_id": salary_log_id, "amount": 60},
        )

        self.assertEqual(settle_response.status_code, 200)
        settle_body = settle_response.json()
        self.assertEqual(settle_body["code"], 200)
        self.assertEqual(settle_body["data"]["transaction_status"], "partially_settled")
        self.assertEqual(settle_body["data"]["salary_remaining"], 40.0)
        self.assertEqual(settle_body["data"]["transaction_remaining_debt"], 40.0)

        history_response = self.client.get(f"/transactions/{transaction_id}/settlements")

        self.assertEqual(history_response.status_code, 200)
        history_body = history_response.json()
        self.assertEqual(history_body["code"], 200)
        self.assertEqual(len(history_body["data"]), 1)
        self.assertEqual(history_body["data"][0]["salary_month"], "2024-02")
        self.assertEqual(history_body["data"][0]["salary_source"], "reimbursement")

        settlement_id = history_body["data"][0]["id"]
        undo_response = self.client.delete(f"/settlements/{settlement_id}")

        self.assertEqual(undo_response.status_code, 200)
        undo_body = undo_response.json()
        self.assertEqual(undo_body["data"]["transaction_status"], "pending")
        self.assertEqual(undo_body["data"]["salary_remaining"], 100.0)
        self.assertEqual(undo_body["data"]["transaction_remaining_debt"], 100.0)
