import pytest
from event_processing.event import Event
from event_processing.engine import Engine
from event_processing.subscriber import Subscriber
from datetime import datetime

from src.event_backtesting.data_manager import DataManager
from src.event_backtesting.book import Book
from src.event_backtesting.order import Order, OrderStatus, OrderSide
from src.event_backtesting.constants import *


def test_data_load_and_run():
    # with open("a.txt", "w") as file:
    #     file.write("a")

    instrument = "instrument"
    # timestamp = datetime.now()

    engine = Engine()
    dm = DataManager()
    engine.subscribe(dm, Topic.SYSTEM)

    # Set up a Subscriber to ge the fills
    class MockSubscriber(Subscriber):
        def __init__(self):
            self.received_events = []

        def receive(self, event: Event):
            self.received_events.append(event)

    mock_subscriber = MockSubscriber()
    engine.subscribe(mock_subscriber, instrument)

    book = Book(instrument)
    engine.subscribe(book, instrument)

    # Test bloomberg tick
    event = Event(
        Topic.SYSTEM,
        Partition.LOAD,
        {
            instrument: {
                Data.SOURCE: DataSource.BLOOMBERG,
                Data.TYPE: DataType.TICK,
                Data.FILE: "./tests/2018-10-01.csv",
            },
        },
    )
    engine.inject(event)

    assert len(dm.events) == 1

    # Test bloomberg tick
    event = Event(
        Topic.SYSTEM,
        Partition.RUN,
        None,
    )
    engine.inject(event)

    # Verify the price received

    assert len(mock_subscriber.received_events) == 41

    assert mock_subscriber.received_events[0].topic == instrument
    assert mock_subscriber.received_events[0].partition == Partition.BEST_BID
    assert mock_subscriber.received_events[0].value[Order.QUANTITY] == 400
    assert mock_subscriber.received_events[0].value[Order.PRICE] == 59.68

    assert mock_subscriber.received_events[-1].topic == instrument
    assert mock_subscriber.received_events[-1].partition == Partition.BEST_ASK
    assert mock_subscriber.received_events[-1].value[Order.QUANTITY] == 99
    assert mock_subscriber.received_events[-1].value[Order.PRICE] == 59.95

    # Check Book bid/ask LOB
    assert book.bids[0].price == 59.72
    assert book.bids[0].quantity == 300
    assert book.asks[0].price == 59.95
    assert book.asks[0].quantity == 99

    # check trade list
    assert book.trades[0].instrument == instrument
    assert book.trades[0].quantity == 100
    assert book.trades[0].price == 59.77
    assert book.trades[-1].instrument == instrument
    assert book.trades[-1].quantity == 400
    assert book.trades[-1].price == 59.72


# TODO: blooberg intr and yahoo hist (other functions)
