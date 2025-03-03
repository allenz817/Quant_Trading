from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import yfinance as yf
import pandas as pd
import talib as ta

class WeightedStrat(Strategy):
    rsi_period = 7
    rsi_upper_bound = 75
    rsi_lower_bound = 25
    fast_period = 12
    slow_period = 26
    signal_period = 9
    bb_period = 20
    bb_stdev = 2
    buy_threshold = 1.0  # Threshold for executing buy orders
    sell_threshold = -1.0  # Threshold for executing sell orders
    rsi_weight = 0.5
    macd_weight = 0.5
    bb_weight = 0.5
    signal_window = 9

    def init(self):
        close = self.data.Close
        self.daily_rsi = self.I(ta.RSI, close, self.rsi_period)
        self.macd, self.signal, _ = self.I(ta.MACD, close, self.fast_period, self.slow_period, self.signal_period)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(ta.BBANDS, close, self.bb_period, self.bb_stdev)

        self.rsi_signals = []
        self.macd_signals = []
        self.bb_signals = []
        
        self.buy()
        
    def next(self):
        price = self.data.Close[-1]
        current_day = len(self.data.Close) - 1 # Day count starts at 34


        # Calculate weighted signals
        if crossover(self.daily_rsi, self.rsi_lower_bound):
            rsi_signal = 1 
        elif crossover(self.rsi_upper_bound, self.daily_rsi):
            rsi_signal = -1
        else: rsi_signal = 0
        
        if crossover(self.macd, self.signal):
            macd_signal = 1 
        elif crossover(self.signal, self.macd):
            macd_signal = -1
        else: macd_signal = 0
        
        if price < self.bb_lower[-1]:
            bb_signal = 1 
        elif price > self.bb_upper[-1]:
            bb_signal = -1
        else: bb_signal = 0
        
        # Store signals in lists
        self.rsi_signals.append(rsi_signal)
        self.macd_signals.append(macd_signal)
        self.bb_signals.append(bb_signal)
        
        # Keep only the last `signal_window` signals
        if len(self.rsi_signals) > self.signal_window:
            self.rsi_signals.pop(0)
        if len(self.macd_signals) > self.signal_window:
            self.macd_signals.pop(0)
        if len(self.bb_signals) > self.signal_window:
            self.bb_signals.pop(0)

        # Calculate total weighted signal value over the lookback period
        total_signal = (
            sum(self.rsi_signals) * self.rsi_weight +
            sum(self.macd_signals) * self.macd_weight +
            sum(self.bb_signals) * self.bb_weight
        )
        
        # Execute buy order if total weighted signal value exceeds the threshold
        if total_signal >= self.buy_threshold:
            self.buy(
                #size=0.5, 
                sl=0.95*price,
            )

        # Execute sell order if total weighted signal value exceeds the threshold
        if total_signal <= self.sell_threshold and self.position.is_long:
            self.position.close()

# BACKTESTING
# Get financial data from yfinance
ticker = 'MSFT' 
stock = yf.download(ticker, start='2024-01-01', end='2024-12-31')[['Open', 'High', 'Low', 'Close', 'Volume']]
# reshape multi-index columns
stock.columns = stock.columns.droplevel(1) 

bt = Backtest(stock, WeightedStrat, cash=10000, commission=.002, exclusive_orders=True)

# Choose output option
output = bt.run()
"""
output = bt.optimize(
    rsi_period=range(7, 28),
    rsi_upper_bound=range(75, 90, 5),
    rsi_lower_bound=range(20, 30, 5),
    #maximize = 'Sharpe Ratio',
    #maximize = optim_func,
    constraint=lambda p: p.rsi_upper_bound > p.rsi_lower_bound,
    #max_tries = 100
)
"""

# Print result
print(output._strategy)
print(output._trades)

print(output)
bt.plot(filename='backtest_result.html')