import pytest
from event_processing.event import Event
from event_processing.engine import Engine

# from event_processing.subscriber import Subscriber
from src.event_backtesting.book import Book
from src.event_backtesting.order import Order
from src.event_backtesting.constants import *


def test_event_subscription_and_dispatch():
    topic = "instrument"

    engine = Engine()
    book = Book(topic)
    engine.subscribe(book, topic)

    # Send OHLC Event
    engine.inject(
        Event(
            topic,
            Instrument.CANDLE,
            {
                Candle.OPEN: 1,
                Candle.HIGH: 2,
                Candle.LOW: 3,
                Candle.CLOSE: 4,
                Candle.VOLUME: 5,
            },
        )
    )

    # Check Book bid/ask LOB
    assert book.bids[0].price == 4
    assert book.bids[0].quantity == 0
    assert book.asks[0].price == 4
    assert book.asks[0].quantity == 0

    # check trade list

    # Send a bid

    # Send an ask

    # Send a mkt order & capture fill

    # Send a lmt order & capture fill

    # Send a lmt buy order without match

    # send an ask and fill

    # Send a lmt buy order without match

    # send a OHLC and fill by low/high range

    # TODO: bid/ask/trade events
