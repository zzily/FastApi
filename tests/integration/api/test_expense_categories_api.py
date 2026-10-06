from tests.integration.base import BaseApiTestCase


class ExpenseCategoryTests(BaseApiTestCase):
    def test_custom_category_persists_and_appears_in_month_breakdown(self):
        category = self.client.post(
            "/expense_categories/", json={"name": "养宠", "kind": "personal"}
        ).json()["data"]
        self.assertEqual(
            self.client.post(
                "/expense_categories/", json={"name": "养宠", "kind": "personal"}
            ).status_code,
            400,
        )
        record_id = self.client.post(
            "/transactions/",
            json={
                "title": "宠物用品",
                "amount_out": 80,
                "category": "personal",
                "expense_category_id": category["id"],
                "occurred_at": "2026-09-30",
            },
        ).json()["data"]["id"]
        record = self.client.get("/transactions/").json()["data"][0]
        self.assertEqual(record["expense_category_name"], "养宠")
        pie = self.client.get("/summary?month=2026-09").json()["data"]["chart_data"][
            "personal_category_breakdown"
        ]
        self.assertEqual(pie, [{"name": "养宠", "value": 80}])
        renamed = self.client.put(
            f'/expense_categories/{category["id"]}', json={"name": "宠物"}
        )
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(
            self.client.get("/transactions/").json()["data"][0][
                "expense_category_name"
            ],
            "宠物",
        )
        self.client.delete(f'/expense_categories/{category["id"]}')
        self.assertEqual(self.client.get("/expense_categories/").json()["data"], [])
        # Historical categories are kept and may remain on edits.
        updated = self.client.put(
            f"/transactions/{record_id}", json={"title": "历史记录"}
        ).json()["data"]
        self.assertEqual(updated["expense_category_name"], "宠物")
        self.assertEqual(
            self.client.post(
                "/transactions/",
                json={
                    "title": "新账单",
                    "amount_out": 10,
                    "expense_category_id": category["id"],
                },
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.put(
                f"/transactions/{record_id}", json={"expense_category_id": None}
            ).json()["data"]["expense_category_id"],
            None,
        )

    def test_rejects_category_from_another_bill_type(self):
        category = self.client.post(
            "/expense_categories/", json={"name": "餐饮", "kind": "personal"}
        ).json()["data"]
        response = self.client.post(
            "/transactions/",
            json={
                "title": "工作垫付",
                "amount_out": 50,
                "category": "work",
                "expense_category_id": category["id"],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/transactions/").json()["data"], [])
