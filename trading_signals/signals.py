from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class Action(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OptionType(Enum):
    CALL = "CALL"
    PUT = "PUT"


class CreditDebit(Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


@dataclass
class StockSignal:
    ticker: str
    price: float
    action: Action
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class OptionSignal:
    ticker: str
    strike: float
    option_type: OptionType
    price: float
    action: Action
    expiration: str
    credit_debit: CreditDebit
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()