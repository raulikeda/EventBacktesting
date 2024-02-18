# Events:

CSV_SEPARATOR = ";"
DEC_SYMBOL = ","
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

ORDER_FEE = 0.1
FLOW_FEE = 0.00  # 0%
FLOW_BUY_TAX = 0.00  # 0%
FLOW_SELL_TAX = 0.001  # 0.1% Tax
PROFIT_TAX = 0.149  # 15% Tax with paid flow sell
INITIAL_CAPITAL = 10000
RISK_FREE_RATE = 13.75  # 13.75%

MARGIN = 100 / 100  # 100% = cash
LEVERAGE = 1  # leverage multiplier


class Topic:
    SYSTEM = "SYSTEM"
    # [INSTRUMENT] = ... Every instrument is a topic


class OrderStatus:
    # Enum for status attribute
    _status = [
        "NEW",
        "PARTIAL",
        "FILLED",
        "REJECTED",
        "CANCELED",
    ]

    NEW, PARTIAL, FILLED, REJECTED, CANCELED = _status


class OrderSide:
    # Enum for side attribute
    _sides = [
        "BUY",
        "SELL",
        "SELLSHORT",
    ]

    BUY, SELL, SELLSHORT = _sides


class DataType:
    _types = ["BID", "ASK", "NEG", "TRADE", "TICK", "HIST", "INTR"]
    BID, ASK, NEG, TRADE, TICK, HIST, INTR = _types


class DataSource:
    BLOOMBERG, YAHOO, RAW = ["BLOOMBERG", "YAHOO", "RAW"]


class Data:
    SOURCE, TYPE, FILE = ["SOURCE", "TYPE", "FILE"]


# Partitions:
class SystemCommand:
    LOAD, RUN = ["LOAD", "RUN"]


class Partition(SystemCommand, OrderStatus, OrderSide, DataType):

    # Order:
    EXECUTE, CANCEL, ORDER = [
        # From Risk to Execution
        "EXECUTE",
        "CANCEL",
        # From Execution to Book
        "ORDER",
    ]

    BEST_BID, BEST_ASK, CANDLE = ["BEST_BID", "BEST_ASK", "CANDLE"]

    PRICE = ["PRICE"]


class Candle:
    OPEN, HIGH, LOW, CLOSE, VOLUME = [
        "OPEN",
        "HIGH",
        "LOW",
        "CLOSE",
        "VOLUME",
    ]


class Fill:
    QUANTITY, PRICE = ["FILLED_QUANTITY", "FILLED_PRICE"]
