from event_processing.subscriber import Subscriber
from event_processing.event import Event
from datetime import datetime
from market_data import MarketData

class DataManager(Subscriber):

    BID, ASK, NEG, TICK, HIST, INTR = ['BID', 'ASK', 'NEG', 'TICK', 'HIST', 'INTR']
    BLOOMBERG, YAHOO, RAW = ['BLOOMBERG', 'YAHOO', 'RAW']

    def __init__(self):
        self.events = {}

    def receive(self, event: Event):
        if event.topic == 'BACKTESTING' and event.partition == 'run':
            for instrument in event.value:
                if event.value[instrument].source == BLOOMBERG:
                    if event.value[instrument].type == TICK:
                        pass
                    elif event.value[instrument].type == INTR:
                        pass
                    elif event.value[instrument].type == HIST:
                        pass
                elif event.value[instrument].source == YAHOO:
                    if event.value[instrument].type == HIST:
                        pass
                if event.value[instrument].source == BLOOMBERG:
                    if event.value[instrument].type == TICK:
                        pass
                    elif event.value[instrument].type == INTR:
                        pass
                    elif event.value[instrument].type == HIST:
                        pass
                




    # Specific methods for different data sources

    def load_bloomberg_tick(self, instrument, data):

        events = data.split('\n')

        # Skip first row
        events = events[1:]

        for event in events:

            # Split the columns with ;
            cols = event.split(';')

            if len(cols) == 4:

                timestamp = datetime.strptime(cols[0], '%d/%m/%Y %H:%M:%S')
                price = float(cols[2].replace(',', '.'))
                quantity = int(cols[3])
                type = cols[1]

                if timestamp.toordinal() not in self.events:
                    self.events[timestamp.toordinal()] = []

                self.events[timestamp.toordinal()].append(
                    MarketData(instrument, timestamp, type, price, quantity))

    def loadYAHOOHist(self, file, instrument, type=Event.CANDLE):

        with open(file, 'r') as file:
            data = file.read()

        events = data.split('\n')
        events = events[1:]
        for event in events:
            cols = event.split(',')
            if len(cols) == 7 and cols[1] != 'null':

                date = datetime.strptime(cols[0], '%Y-%m-%d')
                price = (float(cols[1]), float(cols[2]),
                         float(cols[3]), float(cols[5]))
                quantity = float(cols[6])
                #quantity = 0

                if date.toordinal() not in self.events:
                    self.events[date.toordinal()] = []

                self.events[date.toordinal()].append(
                    Event(instrument, date, type, price, quantity))

    def loadBBGIntr(self, file, instrument, type=Event.CANDLE):

        with open(file, 'r') as file:
            data = file.read()

        events = data.split('\n')
        events = events[1:]
        for event in events:
            cols = event.split(';')
            if len(cols) == 5:

                date = datetime.strptime(cols[0], '%d/%m/%Y %H:%M:%S')
                price = (float(cols[1].replace(',', '.')),
                         float(cols[3].replace(',', '.')),
                         float(cols[4].replace(',', '.')),
                         float(cols[2].replace(',', '.')))
                quantity = 0

                if date.timestamp() not in self.events:
                    self.events[date.timestamp()] = []

                self.events[date.timestamp()].append(
                    Event(instrument, date, type, price, quantity))

    def run(self, ts):
        dates = list(self.events.keys())
        dates.sort()
        for date in dates:
            for event in self.events[date]:
                ts.inject(event)