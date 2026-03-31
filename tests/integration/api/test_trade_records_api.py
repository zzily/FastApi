from tests.integration.base import BaseApiTestCase


class TradeRecordApiTests(BaseApiTestCase):
    def test_list_trade_records_returns_envelope(self):
        response = self.client.get("/trade_records/")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["message"], "获取交易记录成功")
        self.assertEqual(body["data"], [])

    def test_create_and_list_trade_records_with_structured_fields(self):
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
                "entry_at": "2026-03-31T09:30:00",
                "exit_at": "2026-03-31T11:00:00",
                "entry_price": 88000,
                "exit_price": 88320,
                "position_size": 1,
                "thesis": "突破后延续",
                "planned_stop": 87800,
                "planned_target": 88500,
                "actual_stop": None,
                "actual_target": 88320,
                "fees": 12,
                "slippage": 3,
                "followed_plan": True,
                "plan_clarity": "clear",
                "execution_quality": "disciplined",
                "mistake_tags": ["early_exit"],
                "lesson": "确认放量后加仓更稳",
                "option_expiration": "2026-04-18",
                "option_strike": 90000,
                "option_right": "call",
                "option_structure": "single",
                "option_premium_type": "debit",
                "option_max_risk": 350,
                "option_max_reward": 900,
                "option_delta": 0.32,
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
        record = body["data"][0]
        self.assertEqual(record["symbol"], "BTCUSDT")
        self.assertEqual(record["market"], "crypto")
        self.assertEqual(record["side"], "long")
        self.assertEqual(record["traded_at"], "2026-03-31")
        self.assertEqual(record["entry_at"], "2026-03-31T09:30:00")
        self.assertEqual(record["exit_at"], "2026-03-31T11:00:00")
        self.assertEqual(record["position_size"], 1.0)
        self.assertEqual(record["fees"], 12.0)
        self.assertEqual(record["mistake_tags"], ["early_exit"])
        self.assertEqual(record["option_structure"], "single")
        self.assertEqual(record["option_delta"], 0.32)

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
                "mistake_tags": [],
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
                "entry_at": "2026-03-27T09:45:00",
                "exit_at": "2026-03-27T10:30:00",
                "entry_price": 4021.5,
                "exit_price": 4040,
                "position_size": 2,
                "followed_plan": False,
                "plan_clarity": "mixed",
                "execution_quality": "drifted",
                "mistake_tags": ["holding_loser", "oversized"],
                "lesson": "先缩仓再验证 setup",
            },
        )

        self.assertEqual(update_response.status_code, 200)
        body = update_response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["message"], "交易记录更新成功")
        self.assertEqual(body["data"]["id"], trade_record_id)
        self.assertEqual(body["data"]["symbol"], "IF 主连")
        self.assertEqual(body["data"]["market"], "futures")
        self.assertEqual(body["data"]["position_size"], 2.0)
        self.assertFalse(body["data"]["followed_plan"])
        self.assertEqual(body["data"]["plan_clarity"], "mixed")
        self.assertEqual(body["data"]["execution_quality"], "drifted")
        self.assertEqual(body["data"]["mistake_tags"], ["holding_loser", "oversized"])
        self.assertEqual(body["data"]["lesson"], "先缩仓再验证 setup")

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
                "note": "需要清空",
                "thesis": "原始逻辑",
                "mistake_tags": ["unplanned"],
                "lesson": "原始结论",
            },
        )
        trade_record_id = create_response.json()["data"]["id"]

        update_response = self.client.put(
            f"/trade_records/{trade_record_id}",
            json={
                "setup": None,
                "note": None,
                "thesis": None,
                "mistake_tags": [],
                "lesson": None,
                "followed_plan": None,
                "plan_clarity": None,
                "execution_quality": None,
            },
        )

        self.assertEqual(update_response.status_code, 200)
        body = update_response.json()
        self.assertIsNone(body["data"]["setup"])
        self.assertIsNone(body["data"]["note"])
        self.assertIsNone(body["data"]["thesis"])
        self.assertEqual(body["data"]["mistake_tags"], [])
        self.assertIsNone(body["data"]["lesson"])
        self.assertIsNone(body["data"]["followed_plan"])
        self.assertIsNone(body["data"]["plan_clarity"])
        self.assertIsNone(body["data"]["execution_quality"])

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
                "mistake_tags": [],
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
