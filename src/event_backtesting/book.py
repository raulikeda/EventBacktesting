from event_processing.subscriber import Subscriber
from event_processing.event import Event
from event_backtesting.order import Order, Trade, OrderSide, OrderStatus
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
                    OrderSide.BUY,
                    0,
                    event.value[Candle.CLOSE],
                )
                ask = Order(
                    event.topic,
                    OrderSide.SELL,
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
                    fill.status = OrderStatus.FILLED

                    self.send(
                        Event(
                            event.topic,
                            Instrument.FILLED,
                            fill.__dict__.copy(),
                            event.timestamp,
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
                    self.timestamp,
                    event.topic,
                    event.value[Order.QUANTITY],
                    event.value[Order.PRICE],
                )
                self.trades.append(trade)

            elif (
                event.partition == Instrument.BEST_BID
                or event.partition == Instrument.BEST_ASK
            ):
                if event.partition == Instrument.BEST_BID:
                    # Replace the best bid in the book
                    order = Order(
                        event.topic,
                        OrderSide.BUY,
                        event.value[Order.QUANTITY],
                        event.value[Order.PRICE],
                    )
                    order.timestamp = event.timestamp
                    self.bids = [order]

                elif event.partition == Instrument.BEST_ASK:
                    # Replace the best ask in the book
                    order = Order(
                        event.topic,
                        OrderSide.SELL,
                        event.value[Order.QUANTITY],
                        event.value[Order.PRICE],
                    )
                    order.timestamp = event.timestamp
                    self.asks = [order]

                # Try to fill the pending orders under new lob with order price
                filled = self.try_fill_orders(self.orders.values(), order_price=True)
                # Remove if filled
                for fill in filled:
                    del self.orders[fill.id]

            # If receive an order request from execution
            elif event.partition == Instrument.ORDER:

                # Create the order object
                order = Order(
                    event.topic,
                    event.value[Order.SIDE],
                    event.value[Order.QUANTITY],
                    event.value[Order.PRICE],
                )
                order.owner = event.value[Order.OWNER]

                self.send(
                    Event(
                        order.instrument,
                        OrderStatus.NEW,
                        order.__dict__.copy(),
                        self.timestamp,
                    )
                )

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
    def try_fill_orders(self, orders: list[Order], order_price: bool = False):
        filled_orders = []
        for order in orders:
            # Buy Order
            if order.side == OrderSide.BUY:
                book = self.asks
            # Sell Order
            elif order.side == OrderSide.SELL:
                book = self.bids

            # Book position
            i = 0
            # Initialize a quantity greater than 0
            q = order.quantity
            # while there is a book and filled anything
            total = 0
            while i < len(book) and q > 0:
                # Try fill with i-th depth of the book
                q = self.try_fill_order_offer(order, book[i], order_price)
                total += q
                # Next book line
                i += 1

            # If it filled any quantity in the order
            if total > 0:
                if order.executed == order.quantity:
                    # filled fully a new order
                    order.status = OrderStatus.FILLED
                    self.send(
                        Event(
                            order.instrument,
                            OrderStatus.FILLED,
                            order.__dict__.copy(),
                            self.timestamp,
                        )
                    )
                    filled_orders.append(order)
                else:
                    # filled partially a new order
                    order.status = OrderStatus.PARTIAL
                    self.send(
                        Event(
                            order.instrument,
                            OrderStatus.PARTIAL,
                            order.__dict__.copy(),
                            self.timestamp,
                        )
                    )

        return filled_orders

    # Method to try to fill ONE order with one line of LOB
    def try_fill_order_offer(self, order: Order, offer: Order, order_price: bool):
        # Pending order quantity
        rem = order.quantity - order.executed

        if (
            # If buy order and the price is above ask
            (order.side == OrderSide.BUY and order.price >= offer.price)
            # If sell order and the price is bellow bid
            or (order.side == OrderSide.SELL and order.price <= offer.price)
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
            if order_price:  # Use the order price
                amount += quantity * order.price
            else:  # use the offer price
                amount += quantity * offer.price

            # Update order
            order.executed += quantity
            order.average = amount / order.executed
            return quantity

        # no quantity filled
        return 0
