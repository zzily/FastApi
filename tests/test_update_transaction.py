from decimal import Decimal
import unittest

import schemas
from main import _calculate_transaction_status, update_transaction
from models import TransactionStatus, Category


class DummyTransaction:
    def __init__(self):
        self.id = 1
        self.title = "原始标题"
        self.amount_out = Decimal("100")
        self.amount_reimbursed = Decimal("20")
        self.category = Category.work
        self.status = TransactionStatus.partially_settled


class DummySession:
    def __init__(self, txn):
        self.txn = txn
        self.committed = False
        self.rolled_back = False

    def get(self, model, transaction_id):
        if transaction_id == self.txn.id:
            return self.txn
        return None

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class TransactionUpdateTests(unittest.TestCase):
    def test_calculate_transaction_status_boundaries(self):
        self.assertEqual(_calculate_transaction_status(Decimal("100"), Decimal("0")), TransactionStatus.pending)
        self.assertEqual(_calculate_transaction_status(Decimal("100"), Decimal("50")), TransactionStatus.partially_settled)
        self.assertEqual(_calculate_transaction_status(Decimal("100"), Decimal("100")), TransactionStatus.settled)

    def test_update_transaction_does_not_overwrite_missing_fields(self):
        txn = DummyTransaction()
        db = DummySession(txn)

        payload = schemas.TransactionUpdate(amount_out=120)
        response = update_transaction(1, payload, db)

        self.assertEqual(response["code"], 200)
        self.assertTrue(db.committed)
        self.assertEqual(txn.title, "原始标题")
        self.assertEqual(txn.category, Category.work)
        self.assertEqual(txn.amount_out, Decimal("120"))
        self.assertEqual(txn.status, TransactionStatus.partially_settled)


if __name__ == "__main__":
    unittest.main()
