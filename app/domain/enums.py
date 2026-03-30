import enum


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    partially_settled = "partially_settled"
    settled = "settled"


class Category(str, enum.Enum):
    work = "work"
    personal = "personal"


class IncomeSource(str, enum.Enum):
    salary = "salary"
    reimbursement = "reimbursement"
    other = "other"


class TradeSide(str, enum.Enum):
    long = "long"
    short = "short"


class TradeMarket(str, enum.Enum):
    stock = "stock"
    crypto = "crypto"
    futures = "futures"
    forex = "forex"
    options = "options"
    other = "other"
