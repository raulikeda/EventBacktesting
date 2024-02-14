import pytest
from datetime import datetime
from src.event_backtesting.order import Order, Trade, OrderSide, OrderStatus


def test_order_initialization_and_repr():
    timestamp = datetime.now()
    order = Order(instrument="instrument", side=OrderSide.BUY, quantity=1, price=10)
    order.timestamp = timestamp

    # Verify that all attributes are correctly assigned
    assert order.id == 1
    assert order.instrument == "instrument"
    assert order.side == OrderSide.BUY
    assert order.quantity == 1
    assert order.price == 10
    assert order.executed == 0
    assert order.average == 0

    # Verify the string representation
    expected_repr = f"1 - {timestamp} - instrument: 0/1@10.000000"
    assert repr(order) == expected_repr

    new_order = order = Order(
        instrument="instrument2", side=OrderSide.SELL, quantity=2, price=20
    )
    assert new_order.id == 2


def test_order_creation():
    order = Order("AAPL", OrderSide.BUY, 100, 150.00)
    assert order.instrument == "AAPL"
    assert order.side == OrderSide.BUY
    assert order.quantity == 100
    assert order.price == 150.00
    assert order.status == OrderStatus.NEW
    assert isinstance(order.id, int) and order.id > 0


def test_order_invalid_side():
    with pytest.raises(ValueError) as excinfo:
        order = Order("AAPL", "INVALID_SIDE", 100, 150.00)
    assert "Invalid side order." in str(excinfo.value)


def test_trade_creation():
    timestamp = datetime.now()
    trade = Trade(timestamp, "AAPL", 100, 150.50)
    assert trade.timestamp == timestamp
    assert trade.instrument == "AAPL"
    assert trade.quantity == 100
    assert trade.price == 150.50

    expected_repr = f"{timestamp} - AAPL: 100@150.500000"
    assert repr(trade) == expected_repr
