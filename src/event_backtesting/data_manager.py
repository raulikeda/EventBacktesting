from event_processing.subscriber import Subscriber
from event_processing.event import Event
from event_backtesting.constants import *
from event_backtesting.order import Order
from datetime import datetime

# from market_data import MarketData


class DataManager(Subscriber):
    def __init__(self):
        self.events: dict = {}

    def receive(self, event: Event):
        if event.topic == Topic.SYSTEM and event.partition == Partition.LOAD:
            # Reset the data
            self.events: dict = {}

            events = []
            for instrument in event.value:

                if event.value[instrument][Data.SOURCE] == DataSource.BLOOMBERG:
                    if event.value[instrument][Data.TYPE] == DataType.TICK:
                        data = self.load_bloomberg_tick(
                            instrument, event.value[instrument][Data.FILE]
                        )
                    elif event.value[instrument][Data.TYPE] == DataType.INTR:
                        data = self.load_bloomberg_intr(
                            instrument, event.value[instrument][Data.FILE]
                        )
                elif event.value[instrument][Data.SOURCE] == DataSource.YAHOO:
                    if event.value[instrument][Data.TYPE] == DataType.HIST:
                        data = self.load_yahoo_hist(
                            instrument, event.value[instrument][Data.FILE]
                        )

                events += data

            for event in events:
                if event.timestamp.toordinal() not in self.events:
                    self.events[event.timestamp.toordinal()] = []

                self.events[event.timestamp.toordinal()].append(event)

        if event.topic == Topic.SYSTEM and event.partition == Partition.RUN:
            # Start simulation

            dates = list(self.events.keys())
            dates.sort()
            for date in dates:
                for event in self.events[date]:
                    self.send(event)

    # Specific methods for different data sources

    def load_bloomberg_tick(self, instrument, file_name):

        events = []

        with open(file_name, "r") as file:
            data = file.read()

        # Break in lines
        rows = data.split("\n")

        # Skip first row (header row)
        rows = rows[1:]

        for row in rows:

            # Split the columns with ;
            cols = row.split(CSV_SEPARATOR)

            # It should be date, action, value, volume
            if len(cols) == 4:

                timestamp = datetime.strptime(cols[0], DATETIME_FORMAT)
                # Brazilian decimal format
                price = float(cols[2].replace(",", "."))
                quantity = int(cols[3])
                partition = cols[1]

                if partition == Partition.BID:
                    partition = Partition.BEST_BID
                elif partition == Partition.ASK:
                    partition = Partition.BEST_ASK

                events.append(
                    Event(
                        topic=instrument,
                        partition=partition,
                        value={Order.QUANTITY: quantity, Order.PRICE: price},
                        timestamp=timestamp,
                    )
                )

        return events

    def load_yahoo_hist(self, instrument, file_name):

        events = []

        with open(file_name, "r") as file:
            data = file.read()

        # Break in lines
        rows = data.split("\n")

        # Skip first row (header row)
        rows = rows[1:]

        for row in rows:
            cols = row.split(",")  # It is fixed for yahoo
            # Sometimes the row is null
            if len(cols) == 7 and cols[1] != "null":

                date = datetime.strptime(cols[0], "%Y-%m-%d")  # It is fixed for yahoo
                price = (float(cols[1]), float(cols[2]), float(cols[3]), float(cols[5]))
                quantity = int(cols[6])

                # TODO: fix Open, High, Low as Adjusted Close
                # TODO: arg adjusted to choose from adjusted o dividend event

                events.append(
                    Event(
                        topic=instrument,
                        partition=Partition.CANDLE,
                        value={
                            Candle.OPEN: price[0],
                            Candle.HIGH: price[1],
                            Candle.LOW: price[2],
                            Candle.CLOSE: price[3],
                            Candle.VOLUME: quantity,
                        },
                        timestamp=date,
                    )
                )

        return events

    def load_bloomberg_intr(self, instrument, file_name):

        events = []

        with open(file_name, "r") as file:
            data = file.read()

        # Break in lines
        rows = data.split("\n")

        # Skip first row (header row)
        rows = rows[1:]

        for row in rows:
            cols = row.split(CSV_SEPARATOR)

            if len(cols) == 5:

                date = datetime.strptime(cols[0], DATETIME_FORMAT)
                price = (
                    float(cols[1].replace(",", ".")),
                    float(cols[3].replace(",", ".")),
                    float(cols[4].replace(",", ".")),
                    float(cols[2].replace(",", ".")),
                )
                quantity = 0

                events.append(
                    Event(
                        topic=instrument,
                        partition=Partition.CANDLE,
                        value={
                            Candle.OPEN: price[0],
                            Candle.HIGH: price[1],
                            Candle.LOW: price[2],
                            Candle.CLOSE: price[3],
                            Candle.VOLUME: quantity,
                        },
                        timestamp=date,
                    )
                )

        return events
