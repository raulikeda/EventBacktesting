from event_processing.subscriber import Subscriber
from event_backtesting.order import Order, OrderSide, OrderStatus
from event_backtesting.constants import *
import numpy as np

# TODO: implement original strategy receive
# TODO: make it generic for dict[id, etc]


class Risk(Subscriber):
    def __init__(self):
        self.position: dict[str, dict[int, int]] = {}

        self._prices = {}  # vector of prices by instrument
        self._last = {}  # dictionary of last prices by instrument

        self._trade: dict[int, Trade] = {}  # Actual open trade for each strategy
        self._trades: dict[
            int, list[Trade]
        ] = {}  # list of all trades for each strategy
        self._days: dict[
            int, dict
        ] = {}  # Struct of daily aggregated mectrics for each strategy

        self._orders: dict[
            int, int
        ]  # List of orders for flow control for each strategy

        # Fee, Tax, Carry and Capital information
        # See constants.py for more information
        self.fee_order = ORDER_FEE
        self.fee_flow = FLOW_FEE
        self.tax_flow_buy = FLOW_BUY_TAX
        self.tax_flow_sell = FLOW_SELL_TAX
        self.tax_profit = PROFIT_TAX
        self.init_capital = INITIAL_CAPITAL
        self.avail_capital = self.init_capital
        self.risk_free_rate = RISK_FREE_RATE

        # TODO: implement for each instrument
        self.margin = MARGIN
        self.leverage = LEVERAGE

    def receive(self, event):

        if event.topic == Topic.SYSTEM and event.partition == Partition.LOAD:

            for instrument in event.value:
                self.position[instrument] = {}
                self._prices[instrument] = []

        elif event.topic in self.position:
            if event.partition == Partition.PRICE:
                self._prices[event.topic].append(event.value)

                # Update results MtM
                for trade in self._trade.values():
                    if not trade.zeroed():
                        pass 



            elif event.partition in [
                Partition.BUY,
                Partition.SELL,
                Partition.SELLSHORT,
            ]:
                owner = event.sender
                if owner not in self.position[event.topic]:
                    self.position[event.topic][owner] = 0

                partition = Partition.EXECUTE

                if event.partition == Partition.SELLSHORT:
                    # Check if position is 0
                    if self.position[event.topic][owner] != 0:
                        partition = OrderStatus.REJECTED

                # Create the Execute Event
                order = event(
                    event.topic,
                    partition,
                    {
                        Order.OWNER: owner,
                        Order.QUANTITY: event.value[Order.QUANTITY],
                        Order.PRICE: event.value[Order.PRICE],
                        Order.SIDE: event.partition,
                        Order.STATUS: partition,
                    },
                )

                self.send(order)

            elif event.partition == OrderStatus.PARTIAL:

                instrument = event.topic
                owner = event.value[Order.OWNER]

                id = event.value[Order.ID]
                price = event.value[Fill.PRICE]
                quantity = event.value[Fill.QUANTITY]
                side = event.value[Order.SIDE]

                if price != 0 and quantity != 0:

                    # Update Strategy position in position dictionary
                    if instrument in self.position:
                        if owner not in self.position[instrument]:
                            self.position[instrument][owner] = 0

                        self.position[instrument][owner] += event.value[Fill.QUANTITY]

                    # order list of a trade. One trade may contain n orders
                    if id not in self._trade.orders:
                        self._trade.orders.append(id)
                        self._trade.fee += self.fee_order

                # if it was a BUY
                if side == OrderSide.BUY:

                    # Buy Cash Flow
                    self._trade.buy_flow -= price * quantity * self.leverage

                    # Fee and tax calculation (flow is negative)
                    self._trade.fee += self.fee_flow * quantity * price
                    self._trade.tax -= self.tax_flow_buy * quantity * price

                elif side == OrderSide.SELL or side == OrderSide.SELLSHORT:

                    # Sell Cash Flow
                    self._trade.sell_flow = price * quantity * self.leverage

                    # Fee and tax calculation (flow is positive)
                    self._trade.fee -= self.fee_flow * quantity * price
                    self._trade.tax = self.tax_flow_sell * quantity * price

                # Update max alloc to calculate return
                self._trade.update_alloc()

                # If the trade is completed zeroed, the trade is over
                if self._trade.zeroed():

                    # Update P&L (sum of cashflows)
                    self._trade.pnl = self._trade.sell_flow + self._trade.buy_flow

                    # Revenue tax
                    if self._trade.pnl > 0:
                        self._trade.tax += self.tax_profit * self._trade.pnl

                    # Update capital, this is not the result, it is balance
                    self.avail_capital += (
                        self._trade.pnl - self._trade.tax - self._trade.fee
                    )

                    # Return! Think on multi-instrument or arbitrage strategy to understand it
                    self._trade.ret = self._trade.pnl / self._trade.max_alloc

                    # Net return - including fees and taxes
                    self._trade.net_ret = (
                        self._trade.pnl - self._trade.fee - self._trade.tax
                    ) / self._trade.max_alloc

                    # Archive the trade and start another one
                    self._trades.append(self._trade)

                    # It is always available even though it is not used
                    self._trade = Trade()

    def close(self, strategy_id: int) -> None:  # close all open positions

        for instrument, position in self._trade.position.items():
            if position > 0:
                self.submit(self.id, Order(instrument, Order.S, position, 0))
            elif position < 0:
                self.submit(self.id, Order(instrument, Order.B, position, 0))

        # Fill last item in vector days
        max_timestamp = max(self._days.keys())
        self._days[max_timestamp][0] = self.avail_capital + self._trade.partial_result(
            self._last, self.leverage
        )
        daily_rate = (1 + self.risk_free_rate / 100) ** (1 / 252) - 1
        self._days[max_timestamp][1] = (
            self.avail_capital - self._trade.max_alloc
        ) * daily_rate

    def summary(self, strategy_id: int) -> str:

        if len(self._trades) == 0:
            res = "No trades in the period\n\n"
            gross = 0
            fee = 0
            tax = 0
        else:

            res = ""
            res += "Gross Profit: ${0:.2f}\n".format(
                sum([trade.pnl for trade in self._trades if trade.pnl > 0])
            )
            res += "Gross Loss: ${0:.2f}\n".format(
                sum([trade.pnl for trade in self._trades if trade.pnl < 0])
            )
            res += "Gross Total: ${0:.2f}\n\n".format(
                sum([trade.pnl for trade in self._trades])
            )

            res += "Number of trades: {0}\n".format(len(self._trades))
            res += "Hitting Ratio: {0:.2f}%\n".format(
                100
                * len([trade.pnl for trade in self._trades if trade.pnl > 0])
                / len(self._trades)
            )
            res += "Number of profit trades: {0}\n".format(
                len([trade.pnl for trade in self._trades if trade.pnl > 0])
            )
            res += "Number of loss trades: {0}\n".format(
                len([trade.pnl for trade in self._trades if trade.pnl < 0])
            )
            res += "Average number of events per trade: {0:.2f}\n\n".format(
                np.mean([len(trade.events) for trade in self._trades])
            )

            win = [trade.pnl for trade in self._trades if trade.pnl > 0]
            loss = [trade.pnl for trade in self._trades if trade.pnl < 0]

            if len(win) > 0:
                res += "Max win trade: ${0:.2f}\n".format(max(win))
                res += "Avg win trade: ${0:.2f}\n".format(np.mean(win))
            else:
                res += "Max win trade: $-\n"
                res += "Avg win trade: $-\n"

            if len(loss) > 0:
                res += "Max loss trade: ${0:.2f}\n".format(min(loss))
                res += "Avg loss trade: ${0:.2f}\n".format(np.mean(loss))
            else:
                res += "Max loss trade: $-\n"
                res += "Avg loss trade: $-\n"

            res += "Avg all trades: ${0:.2f}\n".format(
                np.mean([trade.pnl for trade in self._trades])
            )
            if len(win) > 0 and len(loss) > 0:
                res += "Win/Loss ratio: {0:.2f}\n\n".format(
                    -np.mean(win) / np.mean(loss)
                )
            else:
                res += "Win/Loss ratio: -\n\n"

            res += "Max Profit: ${0:.2f}\n".format(
                max([trade.max_profit_close for trade in self._trades])
            )
            res += "Max Profit High/Low: ${0:.2f}\n".format(
                max([trade.max_profit_high for trade in self._trades])
            )
            res += "Max Drawdown: ${0:.2f}\n".format(
                min([trade.max_dd_close for trade in self._trades])
            )
            res += "Max Drawdown High/Low: ${0:.2f}\n\n".format(
                min([trade.max_dd_low for trade in self._trades])
            )

            max_alloc = max([trade.max_alloc for trade in self._trades])
            res += "Max Allocation: ${0:.2f}\n".format(max_alloc)
            res += "Avg Allocation: ${0:.2f}\n".format(
                np.mean([trade.max_alloc for trade in self._trades])
            )
            res += "Max Cash Required (margin): ${0:.2f}\n\n".format(
                max_alloc * self.margin
            )

            gross = sum([trade.pnl for trade in self._trades])
            fee = sum([trade.fee for trade in self._trades])
            tax = sum([trade.tax for trade in self._trades])

            res += "Gross Total: ${0:.2f}\n".format(gross)
            res += "Total Fees: ${0:.2f}\n".format(fee)
            res += "Total Taxes: ${0:.2f}\n".format(tax)
            res += "Net Total: ${0:.2f}\n\n".format(gross - fee - tax)

            res += "Gross Return: {0:.2f}%\n".format(
                100 * sum([trade.ret for trade in self._trades])
            )
            res += "Average Return: {0:.2f}%\n".format(
                100 * np.mean([trade.ret for trade in self._trades])
            )
            res += "Net Return: {0:.2f}%\n".format(
                100 * sum([trade.net_ret for trade in self._trades])
            )
            res += "Net Return Avg Alocation: {0:.2f}%\n\n".format(
                100
                * (gross - fee - tax)
                / np.mean([trade.max_alloc for trade in self._trades])
            )

        res += "Number of days: {}\n".format(len(self._days))
        res += "Initial Capital: ${0:.2f}\n".format(self.init_capital)
        daily_rate = (1 + self.risk_free_rate / 100) ** (1 / 252) - 1
        res += "Risk Free Rate: {0:.2f}% yearly/{1:.4f}% daily\n".format(
            self.risk_free_rate, 100 * daily_rate
        )
        carry = sum([day[1] for day in self._days.values()])
        res += "Total Carry: ${0:.2f}\n".format(carry)
        res += "Net Total + Carry: ${0:.2f}\n".format(gross - fee - tax + carry)
        ret_cap = (gross - fee - tax + carry) / self.init_capital
        res += "Net Return Capital: {0:.2f}%\n".format(100 * ret_cap)
        res += "Net Return Capital Yearly: {0:.2f}%\n\n".format(
            100 * ((1 + ret_cap) ** (252 / len(self._days)) - 1)
        )

        return res


class Trade:
    def __init__(self):
        self.timestamp = ""
        self.position = {}
        self.orders = []
        self.fee = 0
        self.tax = 0
        self.avg_sell_price = 0
        self.avg_buy_price = 0
        self.sell_flow = 0
        self.buy_flow = 0
        self.max_alloc = 0
        self.ret = 0
        self.net_ret = 0
        self.max_profit_high = 0
        self.max_profit_close = 0
        self.max_dd_low = 0
        self.max_dd_close = 0
        self.events = []

    def zeroed(self):
        for pos in self.position.values():
            if pos != 0:
                return False
        return True

    def update_alloc(self):
        alloc = self.sell_flow + self.buy_flow
        self.max_alloc = max(max(self.max_alloc, alloc), -alloc)

    def partial_result(self, prices, leverage):
        result = self.sell_flow + self.buy_flow
        for instrument in self.position:
            result += self.position[instrument] * prices[instrument][3] * leverage
        return result

    def partial_result_high(self, prices, leverage):
        result = self.sell_flow + self.buy_flow
        for instrument in self.position:
            result += self.position[instrument] * prices[instrument][1] * leverage
        return result

    def partial_result_low(self, prices, leverage):
        result = self.sell_flow + self.buy_flow
        for instrument in self.position:
            result += self.position[instrument] * prices[instrument][2] * leverage
        return result
