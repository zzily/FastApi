from tests.integration.base import BaseApiTestCase


class TradeRecordApiTests(BaseApiTestCase):
    def test_list_trade_records_returns_envelope(self):
        response = self.client.get("/trade_records/")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["message"], "获取交易记录成功")
        self.assertEqual(body["data"], [])

    def test_create_and_list_trade_records(self):
        create_response = self.client.post(
            "/trade_records/",
            json={
                "symbol": "BTCUSDT",
                "market": "crypto",
                "side": "long",
                "traded_at": "2026-03-31",
                "pnl": 320.5,
                "setup": "趋势突破",
                "note": "顺势加仓",
            },
        )

        self.assertEqual(create_response.status_code, 200)
        create_body = create_response.json()
        self.assertEqual(create_body["code"], 200)
        self.assertGreater(create_body["data"]["id"], 0)

        list_response = self.client.get("/trade_records/")

        self.assertEqual(list_response.status_code, 200)
        body = list_response.json()
        self.assertEqual(len(body["data"]), 1)
        self.assertEqual(body["data"][0]["symbol"], "BTCUSDT")
        self.assertEqual(body["data"][0]["market"], "crypto")
        self.assertEqual(body["data"][0]["side"], "long")
        self.assertEqual(body["data"][0]["traded_at"], "2026-03-31")
        self.assertEqual(body["data"][0]["pnl"], 320.5)

    def test_update_trade_record_returns_updated_entity(self):
        create_response = self.client.post(
            "/trade_records/",
            json={
                "symbol": "ETHUSDT",
                "market": "crypto",
                "side": "short",
                "traded_at": "2026-03-25",
                "pnl": -80,
                "setup": "回撤做空",
                "note": "初始备注",
            },
        )
        trade_record_id = create_response.json()["data"]["id"]

        update_response = self.client.put(
            f"/trade_records/{trade_record_id}",
            json={
                "symbol": "IF 主连",
                "market": "futures",
                "side": "long",
                "traded_at": "2026-03-27",
                "pnl": 180,
                "setup": "早盘反转",
                "note": "按计划减仓",
            },
        )

        self.assertEqual(update_response.status_code, 200)
        body = update_response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["message"], "交易记录更新成功")
        self.assertEqual(body["data"]["id"], trade_record_id)
        self.assertEqual(body["data"]["symbol"], "IF 主连")
        self.assertEqual(body["data"]["market"], "futures")
        self.assertEqual(body["data"]["side"], "long")
        self.assertEqual(body["data"]["traded_at"], "2026-03-27")
        self.assertEqual(body["data"]["pnl"], 180.0)
        self.assertEqual(body["data"]["setup"], "早盘反转")
        self.assertEqual(body["data"]["note"], "按计划减仓")

    def test_update_trade_record_can_clear_optional_fields(self):
        create_response = self.client.post(
            "/trade_records/",
            json={
                "symbol": "SOLUSDT",
                "market": "crypto",
                "side": "long",
                "traded_at": "2026-03-22",
                "pnl": 20,
                "setup": "突破回踩",
                "note": "需要保留",
            },
        )
        trade_record_id = create_response.json()["data"]["id"]

        update_response = self.client.put(
            f"/trade_records/{trade_record_id}",
            json={"setup": None, "note": None},
        )

        self.assertEqual(update_response.status_code, 200)
        body = update_response.json()
        self.assertIsNone(body["data"]["setup"])
        self.assertIsNone(body["data"]["note"])

    def test_delete_trade_record_removes_data(self):
        create_response = self.client.post(
            "/trade_records/",
            json={
                "symbol": "AAPL",
                "market": "stock",
                "side": "long",
                "traded_at": "2026-03-20",
                "pnl": 40,
                "setup": "财报波段",
            },
        )
        trade_record_id = create_response.json()["data"]["id"]

        delete_response = self.client.delete(f"/trade_records/{trade_record_id}")

        self.assertEqual(delete_response.status_code, 200)
        body = delete_response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["message"], "交易记录删除成功")
        self.assertEqual(body["data"]["id"], trade_record_id)

        list_response = self.client.get("/trade_records/")
        self.assertEqual(list_response.json()["data"], [])
