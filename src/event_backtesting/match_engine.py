from event_processing.subscriber import Subscriber
from event_processing.event import Event
from book import Book
from constants import *


class MatchEngine(Subscriber):
    def __init__(self):
        self.books = {}
        self.position = {}
        self.orders = {}
        self.listeners = {}
        self.strategies = {}

    def receive(self, event: Event):
        if event.topic == SETUP and event.partition == LOAD:
            parameters = event.value
            instrument = parameters["instrument"]
            self.create_book(instrument)
        elif event.topic == DATA:
            event.value

    def create_book(self, instrument):
        if instrument not in self.books:
            self.books[instrument] = Book(instrument, self.fill)

        if instrument not in self.position:
            self.position[instrument] = {}

        if instrument not in self.listeners:
            self.listeners[instrument] = []

    # Old Code

    def inject(self, event):
        instrument = event.instrument
        if instrument in self.books:
            self.books[instrument].inject(deepcopy(event))

            for id in self.listeners[instrument]:
                if id in self.strategies:
                    self.strategies[id]._receive(event)

    def subscribe(self, instrument, strategy):
        if strategy.id not in self.strategies:
            self.strategies[strategy.id] = strategy
            strategy.cancel = self.cancel
            strategy.submit = self.submit

        if instrument in self.books:
            if strategy.id not in self.position[instrument]:
                self.position[instrument][strategy.id] = 0

            if strategy.id not in self.listeners[instrument]:
                self.listeners[instrument].append(strategy.id)

    def submit(self, id, order):
        if order is not None:

            order.owner = id
            instrument = order.instrument

            if instrument in self.position:
                if id in self.position[instrument]:
                    position = self.position[instrument][id]

            if sign(position) * sign(position + order.quantity) == -1:
                order.status = Order.REJECTED
                if id in self.strategies:
                    strategy = self.strategies[id]
                    strategy._fill(order.id, instrument, 0, 0, order.status)
            else:
                if order.id not in self.orders:
                    self.orders[order.id] = order

                if instrument in self.books:
                    self.books[instrument].submit(order)

    def cancel(self, owner, id):
        if id in self.orders:
            if self.orders[id].owner == owner:
                instrument = self.orders[id].instrument
                if instrument in self.books:
                    self.books[instrument].cancel(id)

    def fill(self, id, price, quantity, status):

        if id in self.orders:

            order = self.orders[id]
            instrument = order.instrument
            owner = order.owner

            if instrument in self.position:
                if owner in self.position[instrument]:
                    self.position[instrument][owner] += quantity

            if owner in self.strategies:
                strategy = self.strategies[owner]
                strategy._fill(id, instrument, price, quantity, status)
