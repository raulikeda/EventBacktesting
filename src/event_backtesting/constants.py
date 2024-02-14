# Events:
SYSTEM = "system"

CSV_SEPARATOR = ";"
DEC_SYMBOL = ","
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

# Partitions:
class System:
    LOAD, RUN = ["LOAD", "RUN"]


class DataType:
    BID, ASK, NEG, TICK, HIST, INTR = ["BID", "ASK", "NEG", "TICK", "HIST", "INTR"]


class DataSource:
    BLOOMBERG, YAHOO, RAW = ["BLOOMBERG", "YAHOO", "RAW"]


class Data:
    SOURCE, TYPE, FILE = ["source", "type", "file"]


class Instrument:
    # Raw data
    BID, ASK, NEG = [
        "BID",
        "ASK",
        "NEG",
    ]
    # Tick data:
    BEST_BID, BEST_ASK, TRADE = [
        "BEST_BID",
        "BEST_ASK",
        "TRADE",
    ]
    # Candle:
    CANDLE = "CANDLE"

    # Order:
    BUY, SELL, SELLSHORT, EXECUTE, ORDER = [
        # From Strategy to Risk
        "BUY",
        "SELL",
        "SELLSHORT",
        # From Risk to Execution
        "EXECUTE",
        # From Execution to Book
        "ORDER",
    ]

    # Order Status:
    PLACED, MODIFIED, CANCELLED, REJECTED, PARTIAL, FILLED = [
        "PLACED",
        "MODIFIED",
        "CANCELLED",
        "REJECTED",
        "PARTIAL",
        "FILLED",
    ]


class Candle:
    OPEN, HIGH, LOW, CLOSE, VOLUME = [
        "OPEN",
        "HIGH",
        "LOW",
        "CLOSE",
        "VOLUME",
    ]
