from event_processing.engine import Engine
from event_processing.subscriber import Subscriber
from event_processing.event import Event

class MarketData(Subscriber):

    def receive(self, event):
        print(event)

md = MarketData()
engine = Engine()
engine.subscribe(md.id,'ABCD',md.receive)
engine.inject(Event('','ABCD','',1))






