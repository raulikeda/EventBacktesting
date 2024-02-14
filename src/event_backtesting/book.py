from event_processing.subscriber import Subscriber
from event_processing.event import Event
from event_backtesting.order import Order, Trade
from event_backtesting.constants import *
from datetime import datetime


class Book(Subscriber):
    def __init__(self, instrument: str) -> None:

        # book instrument
        self.instrument: str = instrument

        # timestamp of last update
        self.timestamp: datetime = None

        # list of trades
        self.trades: list[Trade] = []

        # list of bids
        self.bids: list[Order] = []

        # list of asks
        self.asks: list[Order] = []

        # list of pending orders
        self.orders: dict[int, Order] = {}

    def receive(self, event: Event) -> None:
        if event.topic == self.instrument:

            # Save last update
            self.timestamp = event.timestamp

            # Received a candle price event
            if event.partition == Instrument.CANDLE:

                # Append the candle as last trade
                bid = Order(
                    event.topic,
                    Order.BUY,
                    0,
                    event.value[Candle.CLOSE],
                )
                ask = Order(
                    event.topic,
                    Order.SELL,
                    0,
                    event.value[Candle.CLOSE],
                )

                trade = Trade(
                    event.timestamp,
                    event.topic,
                    event.value[Candle.VOLUME],
                    event.value[Candle.CLOSE],
                )
                self.trades.append(trade)

                # Update bid/ask book. This is the best guess we have
                self.bids = [bid]
                self.asks = [ask]

                # Try match pending orders
                # We assume infinity liquidity and
                # the Low/High range will cross the limit price
                filled_orders = self.try_match_range(
                    event.value[Candle.LOW], event.value[Candle.HIGH]
                )

                # Send fill event
                for fill in filled_orders:

                    # Remove from pending list
                    del self.orders[fill.id]

                    # Send the FILLED event

                    self.send(
                        Event(
                            event.topic,
                            Instrument.FILLED,
                            fill.__dict__,
                            order.timestamp,
                        )
                    )

            # TODO: RAW DATA & Event LOB
            # TODO: sorted dict on bid/ask for LOB
            elif event.partition == Instrument.BID:
                pass
            elif event.partition == Instrument.ASK:
                pass
            elif event.partition == Instrument.NEG:
                pass
            elif event.partition == Instrument.TRADE:

                # Save the trade in the trades list
                trade = Trade(
                    self.timestamp, event.topic, event.value.quantity, event.value.price
                )
                self.trades.append(trade)

            elif (
                event.partition == Instrument.BEST_BID
                or event.partition == Instrument.BEST_ASK
            ):
                if event.partition == Instrument.BEST_BID:
                    # Replace the best bid in the book
                    order = Order(
                        event.topic, Order.BUY, event.value.quantity, event.value.price
                    )
                    order.timestamp = event.timestamp
                    self.bids = [order]

                elif event.partition == Instrument.BEST_ASK:
                    # Replace the best ask in the book
                    order = Order(
                        event.topic, Order.SELL, event.value.quantity, event.value.price
                    )
                    order.timestamp = event.timestamp
                    self.asks = [order]

                # Try to fill the pending orders under new lob
                filled = self.try_fill_orders(self.orders.values())
                # Remove if filled
                for fill in filled:
                    del self.orders[fill.id]

            # If receive an order request from execution
            elif event.partition == Instrument.ORDER:

                # Create the order object
                order = Order(
                    event.topic,
                    event.value.side,
                    event.value.quantity,
                    event.value.price,
                )
                order.owner = event.value.owner

                # try to fill the order
                filled = self.try_fill_orders([order])
                # if it was not possible to fill it completely
                if len(filled) == 0:
                    # Add to pending orders list
                    self.orders[order.id] = order

    # Filling ALL pending orders when received a Candle event
    # If target price is inside low-high range, it fills in order price
    # Assuming that the order was placed already
    def try_match_range(self, low: float, high: float):
        filled_orders = []

        # Try all pending orders
        for order in self.orders.values():
            # If order price is inside the range
            if order.price >= low and order.price <= high:
                # Fill it fully, assuming infinite liquidity
                order.executed = order.quantity
                order.average = order.price
                filled_orders.append(order)

        return filled_orders

    # Method to try to fill list of orders with all LOB
    def try_fill_orders(self, orders: list[Order]):
        filled_orders = []
        for order in orders:
            # Buy Order
            if order.side == Order.BUY:
                book = self.asks
            # Sell Order
            elif order.side == Order.SELL:
                book = self.bids

            # Book position
            i = 0
            # Initialize a quantity greater than 0
            q = order.quantity
            # while there is a book and filled anything
            while i < len(book) and q > 0:
                # Try fill with i-th depth of the book
                q = self.try_fill_order(order, book[i])
                # Next book line
                i += 1

            if order.executed == order.quantity:
                # filled fully a new order
                self.send(
                    Event(
                        order.instrument,
                        Order.FILLED,
                        order.__dict__,
                        self.timestamp,
                    )
                )
                filled_orders.append(order)
            else:
                # filled partially a new order
                self.send(
                    Event(
                        order.instrument,
                        Order.PARTIAL,
                        order.__dict__,
                        self.timestamp,
                    )
                )

        return filled_orders

    # Method to try to fill ONE order with one line of LOB
    def try_fill_order_offer(self, order: Order, offer: Order):
        # Pending order quantity
        rem = order.quantity - order.executed

        if (
            # If buy order and the price is above ask
            (order.side == Order.BUY and order.price >= offer.price)
            # If sell order and the price is bellow bid
            or (order.side == Order.SELL and order.price <= offer.price)
            # If market order
            or (order.price == 0)
        ):
            # amount filled before new fill
            amount = order.executed * order.average

            # If book has infinite quantity (OHLC)
            if offer.quantity == 0:
                quantity = rem
            else:
                quantity = min(rem, offer.quantity)

            # New amount filled in the order
            amount += quantity * offer.price

            # Update order
            order.executed += quantity
            order.average = amount / order.executed
            return quantity

        # no quantity filled
        return 0
