import pytest
from event_processing.event import Event
from event_processing.engine import Engine
from event_processing.subscriber import Subscriber
from src.event_backtesting.book import Book
from src.event_backtesting.order import Order


def test_event_subscription_and_dispatch():
    engine = Engine()
    book = Book()

    topic = "instrument"
    partition = Order

    # Subscribe the mock subscriber to the engine
    engine.subscribe(mock_subscriber, topic)

    # Create and send an event
    event = Event(topic=topic, partition=partition, value="test_event")
    engine.inject(event)

    # Allow some time for the event to be processed
    # This is a simplistic approach; in real scenarios, consider using threading conditions or other synchronization methods.
    import time

    time.sleep(0.1)

    # Assert that the mock subscriber received the event
    assert len(mock_subscriber.received_events) == 1
    assert mock_subscriber.received_events[0].value == "test_event"
