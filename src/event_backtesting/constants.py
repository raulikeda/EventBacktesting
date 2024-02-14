# Events:
SYSTEM = "system"
# instrument

# Partitions:
class System:
    LOAD, RUN = ["LOAD", "RUN"]


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
