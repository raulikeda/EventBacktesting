from event_processing.subscriber import Subscriber
from event_backtesting.constants import *
from event_processing.event import Event


class Execution(Subscriber):
    """
    Execution class is responsible for executing orders.
    This is where you can create new synthetic orders, modify or cancel orders.

    Methods
    -------
    receive(event)
        Receives an event and processes it.
    """

    def receive(self, event: Event) -> None:
        """
        Receives an EXECUTE event and processes it.

        Parameters
        ----------
        event : Event
            The event to be processed.

        Returns
        -------
        """
        if event.partition == Partition.EXECUTE:

            # BYPASSING: you can create new syntethic orders here

            # TODO: Modify/Cancel Order

            order = event(
                event.topic,
                Partition.ORDER,
                {event.__dict__.copy()},
            )

            self.send(order)
        elif event.partition == Partition.CANCEL:
            pass
