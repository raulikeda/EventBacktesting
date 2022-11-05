from event_processing.subscriber import Subscriber
from event_processing.event import Event
from constants import *

# TODO: sorted dict on bid/ask

class Book(Subscriber):

    def __init__(self, instrument):
        # timestamp of last update
        self.timestamp = None

        # list of trades
        self.trades = []

        # list of bids
        self.bids = []

        # list of asks
        self.asks = []

        # list of pending orders
        self.orders: dict[int, Order] = []

        # book instrument
        self.instrument = instrument
    
    def receive(self, event: Event):
        if event.topic == self.instrument:
            
            # save last update and price
            self.timestamp = event.timestamp

            if event.partition == CANDLE:
                order = Order(event.topic, 0, event.value[3])
                order.timestamp = event.timestamp
                self.trades.append(order)

                self.bids = [order]
                self.asks = [order]

                filled_orders = self.try_match(event.value[2], event.value[1])
                for fill in filled_orders:
                    del self.orders[fill.id]
                    self.send(Event(FILL, fill.id, fill.__dict__, order.timestamp))

            # TODO: TICK-BY-TICK & RAW DATA
            # elif event.partition == TRADE:
            #     order = Order(event.topic, event.value[0], event.value[1])
            #     order.timestamp = event.timestamp
            #     self.trades.append(order)

            # elif event.partition == BEST_BID:
            #     order = Order(event.topic, event.value[0], event.value[1])
            #     order.timestamp = event.timestamp
            #     self.bid = [order]

            # elif event.partition == BEST_ASK:
            #     order = Order(event.topic, event.value[0], event.value[1])
            #     order.timestamp = event.timestamp
            #     self.ask = [order]

            elif event.partition == ORDER:
                order = Order(event.topic,event.value.quantity, event.value.price)
                order.owner = event.sender

                if order.quantity > 0:
                    if order.price == 0 or order.price >= self.bids[0].price:
                        pass # HERE


                    self.orders[order.id] = order
                    pass
                elif order.quantity < 0:
                    pass
                # TODO: try_match


#Process and then yield
        
    def try_match(self, low, high):
        filled_orders = []
        for order in self.orders.values():
            if order.price >= low and order.price <= high:
                order.executed = order.quantity
                order.average = order.price
                filled_orders.append(order)
        
        return filled_orders

#### Old code

    def old(self, event):
            if event.partition == BID or event.partition == CANDLE:

                self.bid = event
                for order in self.orders:
                    if order.quantity < 0:
                        if order.price <= event.price:
                            rem = order.quantity - order.executed

                            if event.quantity == 0:
                                qty = rem
                            else:
                                qty = max(rem, -event.quantity)

                            average = order.average * order.executed + qty * event.price

                            order.executed += qty
                            order.average = average / order.executed

                            if order.quantity == order.executed:
                                order.status = Order.FILLED

                            self.fill(order.id, event.price, qty, order.status)

            if event.type == Event.ASK or event.type == Event.CANDLE:
                self.ask = event
                for order in self.orders:
                    if order.quantity > 0:
                        if order.price >= event.price:
                            rem = order.quantity - order.executed

                            if event.quantity == 0:
                                qty = rem
                            else:
                                qty = min(rem, event.quantity)

                            average = order.average * order.executed + qty * event.price

                            order.executed += qty
                            order.average = average / order.executed

                            if order.quantity == order.executed:
                                order.status = Order.FILLED

                            self.fill(order.id, event.price, qty, order.status)

            if event.type == Event.TRADE:
                self.trade = event
                for order in self.orders:
                    if order.quantity > 0 and order.price >= event.price:
                        rem = order.quantity - order.executed

                        if event.quantity == 0:
                            qty = rem
                        else:
                            qty = min(rem, event.quantity)

                        average = order.average * order.executed + qty * event.price

                        order.executed += qty
                        order.average = average / order.executed

                        if order.quantity == order.executed:
                            order.status = Order.FILLED

                        self.fill(order.id, event.price, qty, order.status)

                    if order.quantity < 0 and order.price <= event.price:
                        rem = order.quantity - order.executed

                        if event.quantity == 0:
                            qty = rem
                        else:
                            qty = max(rem, -event.quantity)

                        average = order.average * order.executed + qty * event.price

                        order.executed += qty
                        order.average = average / order.executed

                        if order.quantity == order.executed:
                            order.status = Order.FILLED

                        self.fill(order.id, event.price, qty, order.status)

            i = 0
            while i < len(self.orders):
                if self.orders[i].status == Order.FILLED:
                    del self.orders[i]
                else:
                    i += 1

        