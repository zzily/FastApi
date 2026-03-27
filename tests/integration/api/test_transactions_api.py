from tests.integration.base import BaseApiTestCase


class TransactionApiTests(BaseApiTestCase):
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
        items = list_response.json()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "垫付办公用品")
        self.assertEqual(items[0]["status"], "pending")
