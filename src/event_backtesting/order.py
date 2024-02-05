class Order():

    _id = 0

    NEW, PARTIAL, FILLED, REJECTED, CANCELED = [
        'NEW', 'PARTIAL', 'FILLED', 'REJECTED', 'CANCELED']
    
    B, S, SS = ['BUY','SELL','SELL SHORT']

    @staticmethod
    def get_id():
        Order._id += 1
        return Order._id

    def __new__(cls, *args, **kwargs):
        instance = super(Order, cls).__new__(cls) #, *args, **kwargs)
        instance.id = Order.get_id()
        return instance

    def __init__(self, instrument, side, quantity, price, timestamp):
        self.owner = 0
        self.instrument = instrument
        self.status = Order.NEW
        self.timestamp = timestamp
        if side not in [Order.B, Order.S, Order.SS]:
            raise Exception('Invalid order side')
        self.side = side
        self.quantity = quantity
        self.price = price
        self.executed = 0
        self.average = 0

    def __repr__(self):
        return '{0} - {1} - {5}: {2}/{3}@{4}'.format(self.id, self.timestamp, self.executed, self.quantity, self.price, self.instrument)
