from event_processing.subscriber import Subscriber

class Strategy(Subscriber):

    def __init__(self, instrument):
        self.instrument = instrument
    
    def receive(self, event):
        pass