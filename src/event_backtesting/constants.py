BID, ASK, TRADE, CANDLE, BEST_BID, BEST_ASK, ORDER = ['BID', 'ASK', 'TRADE', 'CANDLE', 'BEST_BID', 'BEST_ASK', 'ORDER']
FILL = 'FILL'

class Order():

    _id = 0

    def get_id():
        Order._id += 1
        return Order._id

    def __new__(cls, instrument, quantity, price, *args, **kwargs):
        instance = super(Order, cls).__new__(cls, *args, **kwargs)
        instance.id = Order.get_id()
        return instance

    NEW, PARTIAL, FILLED, REJECTED, CANCELED = [
        'NEW', 'PARTIAL', 'FILLED', 'REJECTED', 'CANCELED']

    def __init__(self, instrument, quantity, price):        
        self.owner = 0
        self.instrument = instrument
        self.status = Order.NEW
        self.timestamp = ''
        self.quantity = quantity
        self.price = price
        self.executed = 0
        self.average = 0

    def __repr__(self):
        return '{0} - {1} - {5}: {2}/{3}@{4}'.format(self.id, self.timestamp, self.executed, self.quantity, self.price, self.instrument)
