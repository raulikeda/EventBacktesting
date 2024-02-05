from event_processing.event import Event

class MarketData(Event):

    types = ['BID', 'ASK', 'TRADE', 'CANDLE', 'BEST_BID', 'BEST_ASK', 'ORDER']
    BID, ASK, TRADE, CANDLE, BEST_BID, BEST_ASK, ORDER = types

    def __init__(self, timestamp, instrument, type, value):
        super().__init__(instrument, type, value, timestamp)
        self.timestamp = timestamp
        self.instrument = instrument
        self.type = type
        if type not in MarketData.types:
            raise Exception(f'Invalid type {type}')
        self.value = value