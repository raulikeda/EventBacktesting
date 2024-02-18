from datetime import datetime
from event_backtesting.constants import *


class Order:
    """
    Represents a trading order in a financial market system. Each order is uniquely identified and
    contains details about the trade to be executed, including the type of instrument, the side of the trade
    (buy, sell, short-sell), the quantity of the instrument, and the price at which the trade should occur.

    Static Methods:
        get_id: Generates a unique identifier for each new order instance.

    Attributes:
        id (int): Unique identifier for the order, automatically assigned upon creation.
        owner (int): Placeholder for the owner's identifier. Defaults to 0.
        instrument (str): The trading instrument's symbol or identifier.
        side (str): The side of the order, indicating buy, sell, or short-sell.
        status (str): The current status of the order (e.g., new, partial, filled).
        timestamp (str): Timestamp of order creation or submission. Initially empty.
        quantity (int): The amount of the instrument to be traded.
        price (float): The price at which the trade should be executed.
        executed (int): Quantity of the instrument that has been executed. Defaults to 0.
        average (float): The average price of executed trades. Defaults to 0.0.

    Raises:
        ValueError: If the specified side is not one of the predefined options (BUY, SELL, SELLSHORT).
    """

    _id = 0

    @staticmethod
    def get_id() -> int:
        """
        Generates a unique ID for a new order instance.

        Returns:
            int: A unique subscriber ID.
        """
        Order._id += 1
        return Order._id

    def __new__(cls, instrument, side, quantity, price, *args, **kwargs) -> "Order":
        """
        Overrides the default __new__ method to assign a unique ID to each order instance.

        Returns:
            Order: A new instance of order with a unique ID.
        """
        instance = super(Order, cls).__new__(cls, *args, **kwargs)
        instance.id = Order.get_id()
        return instance

    #  Enum for class attributes
    (
        ID,
        INSTRUMENT,
        SIDE,
        STATUS,
        QUANTITY,
        PRICE,
        EXECUTED,
        AVERAGE,
        OWNER,
        TIMESTAMP,
    ) = [
        "id",
        "instrument",
        "side",
        "status",
        "quantity",
        "price",
        "executed",
        "average",
        "owner",
        "timestamp",
    ]

    def __init__(self, instrument: str, side: str, quantity: int, price: float) -> None:
        """
        Initializes a new instance of Order with the given trade details. Validates the side of the order
        to ensure it matches one of the allowed options.
        """

        self.owner = 0
        self.instrument = instrument
        if side not in [OrderSide.BUY, OrderSide.SELL, OrderSide.SELLSHORT]:
            raise ValueError("Invalid side order.")
        self.side = side
        self.status = OrderStatus.NEW
        self.timestamp = ""
        self.quantity = quantity
        self.price = price
        self.executed = 0
        self.average = 0

    def __repr__(self) -> str:
        """
        Returns a string representation of the Order instance, including its unique ID, timestamp,
        instrument, executed quantity, total quantity, and price.
        """

        return "{0} - {1} - {5}: {2}/{3}@{4:0.6f}".format(
            self.id,
            self.timestamp,
            self.executed,
            self.quantity,
            self.price,
            self.instrument,
        )


class Trade:
    """
    Represents a completed trade transaction. Includes details such as the timestamp of the trade,
    the instrument traded, the quantity of the instrument, and the price at which the trade was executed.

    Attributes:
        timestamp (datetime): The timestamp at which the trade occurred.
        instrument (str): The trading instrument's symbol or identifier involved in the trade.
        quantity (int): The amount of the instrument that was traded.
        price (float): The price at which the trade was executed.
    """

    def __init__(
        self, timestamp: datetime, instrument: str, quantity: int, price: float
    ):
        """
        Initializes a new instance of Trade with the given details of the trade transaction.
        """
        self.timestamp = timestamp
        self.instrument = instrument
        self.quantity = quantity
        self.price = price

    def __repr__(self) -> str:
        """
        Returns a string representation of the Trade instance, detailing the timestamp, instrument,
        quantity traded, and the execution price.
        """
        return "{0} - {1}: {2}@{3:0.6f}".format(
            self.timestamp, self.instrument, self.quantity, self.price
        )
