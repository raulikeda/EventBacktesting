import pytest
from event_processing.event import Event
from event_processing.engine import Engine
from event_processing.subscriber import Subscriber
from datetime import datetime

# from event_processing.subscriber import Subscriber
from src.event_backtesting.book import Book
from src.event_backtesting.order import Order, OrderStatus, OrderSide
from src.event_backtesting.constants import *


def test_event_subscription_and_dispatch():
    topic = "instrument"
    timestamp = datetime.now()

    engine = Engine()
    book = Book(topic)
    engine.subscribe(book, topic)

    event = Event(
        topic,
        Partition.CANDLE,
        {
            Candle.OPEN: 1,
            Candle.HIGH: 2,
            Candle.LOW: 3,
            Candle.CLOSE: 4,
            Candle.VOLUME: 5,
        },
        timestamp,
    )

    # Send OHLC Event
    engine.inject(event)

    # Check Book bid/ask LOB
    assert book.bids[0].price == 4
    assert book.bids[0].quantity == 0
    assert book.asks[0].price == 4
    assert book.asks[0].quantity == 0

    # check trade list
    assert book.trades[0].instrument == topic
    assert book.trades[0].timestamp == timestamp
    assert book.trades[0].quantity == 5
    assert book.trades[0].price == 4

    # Send a bid
    bid = Event(
        topic,
        Partition.BEST_BID,
        {Order.QUANTITY: 10, Order.PRICE: 20.30},
        timestamp,
    )
    engine.inject(bid)

    # Send an ask
    ask = Event(
        topic,
        Partition.BEST_ASK,
        {Order.QUANTITY: 20, Order.PRICE: 20.31},
        timestamp,
    )
    engine.inject(ask)

    # Check Book bid/ask LOB
    assert book.bids[0].price == 20.3
    assert book.bids[0].quantity == 10
    assert book.asks[0].price == 20.31
    assert book.asks[0].quantity == 20

    # Set up a Subscriber to ge the fills
    class MockSubscriber(Subscriber):
        def __init__(self):
            self.received_events: list[Event] = []

        def receive(self, event: Event):
            self.received_events.append(event)

    mock_subscriber = MockSubscriber()
    engine.subscribe(mock_subscriber, topic)

    # Send a mkt order & capture fill
    order = Event(
        topic,
        Partition.ORDER,
        {
            Order.OWNER: "me",
            Order.SIDE: OrderSide.BUY,
            Order.QUANTITY: 10,
            Order.PRICE: 0,
        },
        timestamp,
    )
    engine.inject(order)

    # Verify the placement
    # It starts with id 5 because of the book formation before
    assert mock_subscriber.received_events[-3].topic == topic
    assert mock_subscriber.received_events[-3].partition == OrderStatus.NEW
    assert mock_subscriber.received_events[-3].value[Order.ID] == 5
    assert mock_subscriber.received_events[-3].value[Order.OWNER] == "me"
    assert mock_subscriber.received_events[-3].value[Order.STATUS] == OrderStatus.NEW
    assert mock_subscriber.received_events[-3].value[Order.QUANTITY] == 10
    assert mock_subscriber.received_events[-3].value[Order.PRICE] == 0
    assert mock_subscriber.received_events[-3].value[Order.EXECUTED] == 0
    assert mock_subscriber.received_events[-3].value[Order.AVERAGE] == 0
    assert mock_subscriber.received_events[-3].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-3].timestamp == timestamp

    # The fill
    assert mock_subscriber.received_events[-2].topic == topic
    assert mock_subscriber.received_events[-2].partition == OrderStatus.PARTIAL
    assert mock_subscriber.received_events[-2].value[Order.ID] == 5
    assert mock_subscriber.received_events[-2].value[Order.OWNER] == "me"
    assert (
        mock_subscriber.received_events[-2].value[Order.STATUS] == OrderStatus.PARTIAL
    )
    assert mock_subscriber.received_events[-2].value[Order.QUANTITY] == 10
    assert mock_subscriber.received_events[-2].value[Order.PRICE] == 0
    assert mock_subscriber.received_events[-2].value[Order.EXECUTED] == 10
    assert mock_subscriber.received_events[-2].value[Order.AVERAGE] == 20.31
    assert mock_subscriber.received_events[-2].value[Fill.QUANTITY] == 10
    assert mock_subscriber.received_events[-2].value[Fill.PRICE] == 20.31
    assert mock_subscriber.received_events[-2].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-2].timestamp == timestamp

    # Verify the termination
    assert mock_subscriber.received_events[-1].topic == topic
    assert mock_subscriber.received_events[-1].partition == OrderStatus.FILLED
    assert mock_subscriber.received_events[-1].value[Order.ID] == 5
    assert mock_subscriber.received_events[-1].value[Order.OWNER] == "me"
    assert mock_subscriber.received_events[-1].value[Order.STATUS] == OrderStatus.FILLED
    assert mock_subscriber.received_events[-1].value[Order.QUANTITY] == 10
    assert mock_subscriber.received_events[-1].value[Order.PRICE] == 0
    assert mock_subscriber.received_events[-1].value[Order.EXECUTED] == 10
    assert mock_subscriber.received_events[-1].value[Order.AVERAGE] == 20.31
    assert mock_subscriber.received_events[-1].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-1].timestamp == timestamp

    ## Send a mkt order higher than best bid and capture the fill

    order = Event(
        topic,
        Partition.ORDER,
        {
            Order.OWNER: "me",
            Order.SIDE: OrderSide.SELL,
            Order.QUANTITY: 30,
            Order.PRICE: 0,
        },
        timestamp,
    )
    engine.inject(order)

    assert mock_subscriber.received_events[-3].topic == topic
    assert mock_subscriber.received_events[-3].partition == OrderStatus.NEW
    assert mock_subscriber.received_events[-3].value[Order.ID] == 6
    assert mock_subscriber.received_events[-3].value[Order.OWNER] == "me"
    assert mock_subscriber.received_events[-3].value[Order.STATUS] == OrderStatus.NEW
    assert mock_subscriber.received_events[-3].value[Order.QUANTITY] == 30
    assert mock_subscriber.received_events[-3].value[Order.PRICE] == 0
    assert mock_subscriber.received_events[-3].value[Order.EXECUTED] == 0
    assert mock_subscriber.received_events[-3].value[Order.AVERAGE] == 0
    assert mock_subscriber.received_events[-3].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-3].timestamp == timestamp

    # The fill
    assert mock_subscriber.received_events[-2].topic == topic
    assert mock_subscriber.received_events[-2].partition == OrderStatus.PARTIAL
    assert mock_subscriber.received_events[-2].value[Order.ID] == 6
    assert mock_subscriber.received_events[-2].value[Order.OWNER] == "me"
    assert (
        mock_subscriber.received_events[-2].value[Order.STATUS] == OrderStatus.PARTIAL
    )
    assert mock_subscriber.received_events[-2].value[Order.QUANTITY] == 30
    assert mock_subscriber.received_events[-2].value[Order.PRICE] == 0
    assert mock_subscriber.received_events[-2].value[Order.EXECUTED] == 10
    assert mock_subscriber.received_events[-2].value[Order.AVERAGE] == 20.30
    assert mock_subscriber.received_events[-2].value[Fill.QUANTITY] == 10
    assert mock_subscriber.received_events[-2].value[Fill.PRICE] == 20.30
    assert mock_subscriber.received_events[-2].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-2].timestamp == timestamp

    # Verify the termination
    assert mock_subscriber.received_events[-1].topic == topic
    assert mock_subscriber.received_events[-1].partition == OrderStatus.FILLED
    assert mock_subscriber.received_events[-1].value[Order.ID] == 6
    assert mock_subscriber.received_events[-1].value[Order.OWNER] == "me"
    assert mock_subscriber.received_events[-1].value[Order.STATUS] == OrderStatus.FILLED
    assert mock_subscriber.received_events[-1].value[Order.QUANTITY] == 30
    assert mock_subscriber.received_events[-1].value[Order.PRICE] == 0
    assert mock_subscriber.received_events[-1].value[Order.EXECUTED] == 10
    assert mock_subscriber.received_events[-1].value[Order.AVERAGE] == 20.30
    assert mock_subscriber.received_events[-1].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-1].timestamp == timestamp

    ## Send a lmt order & capture fill
    order = Event(
        topic,
        Partition.ORDER,
        {
            Order.OWNER: "me",
            Order.SIDE: OrderSide.BUY,
            Order.QUANTITY: 5,
            Order.PRICE: 20.32,
        },
        timestamp,
    )
    engine.inject(order)

    # Verify the placement
    assert mock_subscriber.received_events[-3].topic == topic
    assert mock_subscriber.received_events[-3].partition == OrderStatus.NEW
    assert mock_subscriber.received_events[-3].value[Order.ID] == 7
    assert mock_subscriber.received_events[-3].value[Order.OWNER] == "me"
    assert mock_subscriber.received_events[-3].value[Order.STATUS] == OrderStatus.NEW
    assert mock_subscriber.received_events[-3].value[Order.QUANTITY] == 5
    assert mock_subscriber.received_events[-3].value[Order.PRICE] == 20.32
    assert mock_subscriber.received_events[-3].value[Order.EXECUTED] == 0
    assert mock_subscriber.received_events[-3].value[Order.AVERAGE] == 0
    assert mock_subscriber.received_events[-3].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-3].timestamp == timestamp

    # Verify the order filling
    assert mock_subscriber.received_events[-1].topic == topic
    assert mock_subscriber.received_events[-1].partition == OrderStatus.FILLED
    assert mock_subscriber.received_events[-2].value[Order.ID] == 7
    assert mock_subscriber.received_events[-1].value[Order.OWNER] == "me"
    assert mock_subscriber.received_events[-1].value[Order.STATUS] == OrderStatus.FILLED
    assert mock_subscriber.received_events[-1].value[Order.QUANTITY] == 5
    assert mock_subscriber.received_events[-1].value[Order.PRICE] == 20.32
    assert mock_subscriber.received_events[-1].value[Order.EXECUTED] == 5
    assert mock_subscriber.received_events[-1].value[Order.AVERAGE] == 20.31
    assert mock_subscriber.received_events[-1].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-1].timestamp == timestamp

    # Send a lmt buy order without match
    order = Event(
        topic,
        Partition.ORDER,
        {
            Order.OWNER: "me",
            Order.SIDE: OrderSide.BUY,
            Order.QUANTITY: 15,
            Order.PRICE: 20.30,
        },
        timestamp,
    )
    engine.inject(order)

    # Verify last fill
    # There is an event between each test (thats why it is -3)
    assert mock_subscriber.received_events[-3].partition == OrderStatus.FILLED
    assert mock_subscriber.received_events[-3].value[Order.ID] == 7
    assert mock_subscriber.received_events[-3].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-3].timestamp == timestamp

    # Verify the placement
    assert mock_subscriber.received_events[-1].topic == topic
    assert mock_subscriber.received_events[-1].partition == OrderStatus.NEW
    assert mock_subscriber.received_events[-1].value[Order.ID] == 8
    assert mock_subscriber.received_events[-1].value[Order.OWNER] == "me"
    assert mock_subscriber.received_events[-1].value[Order.STATUS] == OrderStatus.NEW
    assert mock_subscriber.received_events[-1].value[Order.QUANTITY] == 15
    assert mock_subscriber.received_events[-1].value[Order.PRICE] == 20.30
    assert mock_subscriber.received_events[-1].value[Order.EXECUTED] == 0
    assert mock_subscriber.received_events[-1].value[Order.AVERAGE] == 0
    assert mock_subscriber.received_events[-1].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-1].timestamp == timestamp

    # Verify pending orders
    assert len(book.orders) == 1
    assert book.orders[8].status == OrderStatus.NEW

    # send an ask and partial fill
    ask = Event(
        topic,
        Partition.BEST_ASK,
        {Order.QUANTITY: 10, Order.PRICE: 20.29},
        timestamp,
    )
    engine.inject(ask)

    assert mock_subscriber.received_events[-1].topic == topic
    assert mock_subscriber.received_events[-1].partition == OrderStatus.PARTIAL
    assert mock_subscriber.received_events[-1].value[Order.ID] == 8
    assert mock_subscriber.received_events[-1].value[Order.OWNER] == "me"
    assert (
        mock_subscriber.received_events[-1].value[Order.STATUS] == OrderStatus.PARTIAL
    )
    assert mock_subscriber.received_events[-1].value[Order.QUANTITY] == 15
    assert mock_subscriber.received_events[-1].value[Order.PRICE] == 20.30
    assert mock_subscriber.received_events[-1].value[Order.EXECUTED] == 10
    assert mock_subscriber.received_events[-1].value[Order.AVERAGE] == 20.30
    assert mock_subscriber.received_events[-1].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-1].timestamp == timestamp

    # Verify pending orders
    assert len(book.orders) == 1
    assert book.orders[8].status == OrderStatus.PARTIAL

    # New ask and fill the partial filled order

    # send an ask and partial fill
    ask = Event(
        topic,
        Partition.BEST_ASK,
        {Order.QUANTITY: 5, Order.PRICE: 20.29},
        timestamp,
    )
    engine.inject(ask)

    assert mock_subscriber.received_events[-1].topic == topic
    assert mock_subscriber.received_events[-1].partition == OrderStatus.FILLED
    assert mock_subscriber.received_events[-1].value[Order.ID] == 8
    assert mock_subscriber.received_events[-1].value[Order.OWNER] == "me"
    assert mock_subscriber.received_events[-1].value[Order.STATUS] == OrderStatus.FILLED
    assert mock_subscriber.received_events[-1].value[Order.QUANTITY] == 15
    assert mock_subscriber.received_events[-1].value[Order.PRICE] == 20.30
    assert mock_subscriber.received_events[-1].value[Order.EXECUTED] == 15
    assert mock_subscriber.received_events[-1].value[Order.AVERAGE] == 20.30
    assert mock_subscriber.received_events[-1].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-1].timestamp == timestamp

    assert len(book.orders) == 0

    # send an ask and partial fill
    ask = Event(
        topic,
        Partition.BEST_ASK,
        {Order.QUANTITY: 10, Order.PRICE: 20.30},
        timestamp,
    )
    engine.inject(ask)

    assert mock_subscriber.received_events[-2].value[Order.ID] == 8
    assert mock_subscriber.received_events[-2].value[Order.EXECUTED] == 15
    assert mock_subscriber.received_events[-2].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-2].timestamp == timestamp

    # Send a lmt buy order without match
    order = Event(
        topic,
        Partition.ORDER,
        {
            Order.OWNER: "me",
            Order.SIDE: OrderSide.BUY,
            Order.QUANTITY: 30,
            Order.PRICE: 20.15,
        },
        timestamp,
    )
    engine.inject(order)

    order = Event(
        topic,
        Partition.ORDER,
        {
            Order.OWNER: "me",
            Order.SIDE: OrderSide.SELL,
            Order.QUANTITY: 40,
            Order.PRICE: 20.35,
        },
        timestamp,
    )
    engine.inject(order)

    assert len(book.orders) == 2

    # send a OHLC and fill by low/high range

    event = Event(
        topic,
        Partition.CANDLE,
        {
            Candle.OPEN: 20.20,
            Candle.HIGH: 20.45,
            Candle.LOW: 20.10,
            Candle.CLOSE: 20.20,
            Candle.VOLUME: 5,
        },
        timestamp,
    )

    # Send OHLC Event
    engine.inject(event)

    assert len(book.orders) == 0

    assert mock_subscriber.received_events[-2].topic == topic
    assert mock_subscriber.received_events[-2].partition == OrderStatus.FILLED
    assert mock_subscriber.received_events[-2].value[Order.ID] == 12
    assert mock_subscriber.received_events[-2].value[Order.OWNER] == "me"
    assert mock_subscriber.received_events[-2].value[Order.STATUS] == OrderStatus.FILLED
    assert mock_subscriber.received_events[-2].value[Order.QUANTITY] == 30
    assert mock_subscriber.received_events[-2].value[Order.PRICE] == 20.15
    assert mock_subscriber.received_events[-2].value[Order.EXECUTED] == 30
    assert mock_subscriber.received_events[-2].value[Order.AVERAGE] == 20.15
    assert mock_subscriber.received_events[-2].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-2].timestamp == timestamp

    assert mock_subscriber.received_events[-1].topic == topic
    assert mock_subscriber.received_events[-1].partition == OrderStatus.FILLED
    assert mock_subscriber.received_events[-1].value[Order.ID] == 13
    assert mock_subscriber.received_events[-1].value[Order.OWNER] == "me"
    assert mock_subscriber.received_events[-1].value[Order.STATUS] == OrderStatus.FILLED
    assert mock_subscriber.received_events[-1].value[Order.QUANTITY] == 40
    assert mock_subscriber.received_events[-1].value[Order.PRICE] == 20.35
    assert mock_subscriber.received_events[-1].value[Order.EXECUTED] == 40
    assert mock_subscriber.received_events[-1].value[Order.AVERAGE] == 20.35
    assert mock_subscriber.received_events[-1].value[Order.TIMESTAMP] == timestamp
    assert mock_subscriber.received_events[-1].timestamp == timestamp

    # TODO: bid/ask/trade events
