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


class TradePlanClarity(str, enum.Enum):
    clear = "clear"
    mixed = "mixed"
    missing = "missing"


class TradeExecutionQuality(str, enum.Enum):
    disciplined = "disciplined"
    drifted = "drifted"
    broken = "broken"


class TradeMistakeType(str, enum.Enum):
    chasing = "chasing"
    early_exit = "early_exit"
    holding_loser = "holding_loser"
    oversized = "oversized"
    no_edge = "no_edge"
    unplanned = "unplanned"


class TradeOptionRight(str, enum.Enum):
    call = "call"
    put = "put"


class TradeOptionStructure(str, enum.Enum):
    single = "single"
    vertical_spread = "vertical_spread"
    iron_condor = "iron_condor"
    straddle = "straddle"
    strangle = "strangle"
    other = "other"


class TradePremiumType(str, enum.Enum):
    debit = "debit"
    credit = "credit"
