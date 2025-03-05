from backtesting import Backtest, Strategy
from backtesting.lib import crossover, resample_apply
import yfinance as yf
import pandas as pd
import numpy as np
import talib as ta

class WeightedStrat(Strategy):
    rsi_daily_days = 7
    rsi_upper_bound = 72.5
    rsi_lower_bound = 27.5
    fast_period = 12
    slow_period = 26
    signal_period = 9
    bb_period = 20
    bb_stdev = 2
    buy_threshold = 1.0  # Threshold for executing buy orders
    sell_threshold = -1.0  # Threshold for executing sell orders
    rsi_daily_weight = 0.25
    rsi_weekly_weight = 0.25
    macd_weight = 0.5
    bb_weight = 0.5
    signal_window = 9
    recovery_window = 5

    def init(self):
        close = self.data.Close
        self.rsi_daily = self.I(ta.RSI, close, self.rsi_daily_days)
        self.macd, self.signal, _ = self.I(ta.MACD, close, self.fast_period, self.slow_period, self.signal_period)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(ta.BBANDS, close, self.bb_period, self.bb_stdev)

        # Calculate weekly RSI
        weekly_close = resample_apply('W-FRI', ta.RSI, close, self.rsi_daily_days)
        self.rsi_weekly = self.I(lambda: weekly_close, name='Weekly RSI')
        
        self.rsi_daily_signals = []
        self.rsi_weekly_signals = []
        self.macd_signals = []
        self.bb_signals = []
        self.sell_price = None
        self.sell_day = None
        
        # Register self-defined indicator for plotting
        self.bb_signal_values = np.full(len(self.data.Close), np.nan)
        self.buy_signal_values = np.full(len(self.data.Close), np.nan)
        self.sell_signal_values = np.full(len(self.data.Close), np.nan)
        self.I(lambda: self.bb_signal_values, name='BB Signal')
        self.I(lambda: self.buy_signal_values, name='Buy Signal')
        self.I(lambda: self.sell_signal_values, name='Sell Signal')
  
    def next(self):
        price = self.data.Close[-1]
        current_day = len(self.data.Close) - 1 # Day count starts at 34

        # Calculate weighted signals
        if crossover(self.rsi_daily, self.rsi_lower_bound):
            rsi_daily_signal = 1 
        elif crossover(self.rsi_upper_bound, self.rsi_daily):
            rsi_daily_signal = -1
        else: rsi_daily_signal = 0
        
        if crossover(self.rsi_weekly, self.rsi_lower_bound):
            rsi_weekly_signal = 1 
        elif crossover(self.rsi_upper_bound, self.rsi_weekly):
            rsi_weekly_signal = -1
        else: rsi_weekly_signal = 0
        
        if crossover(self.macd, self.signal):
            macd_signal = 1 
        elif crossover(self.signal, self.macd):
            macd_signal = -1
        else: macd_signal = 0
        
        if price < self.bb_lower[-1]:
            bb_signal = 1 
        elif price > self.bb_upper[-1]:
            bb_signal = -1
        else: 
            bb_signal = 1 - 2 * ((price - self.bb_lower[-1]) / (self.bb_upper[-1] - self.bb_lower[-1]))
        
        # Store signals in lists
        self.rsi_daily_signals.append(rsi_daily_signal)
        self.rsi_weekly_signals.append(rsi_weekly_signal)
        self.macd_signals.append(macd_signal)
        self.bb_signals.append(bb_signal)
        
        # Keep only the last `signal_window` signals
        if len(self.rsi_daily_signals) > self.signal_window:
            self.rsi_daily_signals.pop(0)
        if len(self.rsi_weekly_signals) > self.signal_window:
            self.rsi_weekly_signals.pop(0)
        if len(self.macd_signals) > self.signal_window:
            self.macd_signals.pop(0)
        if len(self.bb_signals) > self.signal_window:
            self.bb_signals.pop(0)

        # Calculate total weighted signal value over the lookback period
        buy_signal = (
            np.max(self.rsi_daily_signals) * self.rsi_daily_weight +
            np.max(self.rsi_weekly_signals) * self.rsi_weekly_weight +
            np.max(self.macd_signals) * self.macd_weight +
            np.max(self.bb_signals) * self.bb_weight
        )
        
        sell_signal = (
            np.min(self.rsi_daily_signals) * self.rsi_daily_weight +
            np.min(self.rsi_weekly_signals) * self.rsi_weekly_weight +
            np.min(self.macd_signals) * self.macd_weight +
            np.min(self.bb_signals) * self.bb_weight
        )
        
        # Execute buy order if total weighted signal value exceeds the threshold
        if buy_signal >= self.buy_threshold:
            self.buy(
                #size=0.5, 
                sl=0.95*price,
            )

        # Execute sell order if total weighted signal value exceeds the threshold
        if sell_signal <= self.sell_threshold and self.position.is_long:
            self.sell_price = price
            self.sell_day = current_day
            self.position.close()
            
            
        """
        # Check for price recovery within the recovery timeframe
        if self.sell_price is not None and self.sell_day is not None:
            if current_day - self.sell_day <= self.recovery_window and price > self.sell_price:
                self.buy()
                self.sell_price = None
                self.sell_day = None
        """
        # Update self-defined values for plotting
        self.bb_signal_values[current_day] = bb_signal
        self.buy_signal_values[current_day] = buy_signal
        self.sell_signal_values[current_day] = sell_signal

# BACKTESTING
# Get financial data from yfinance
ticker = 'QQQ' 
stock = yf.download(ticker, start='2023-01-01', end='2024-12-31')[['Open', 'High', 'Low', 'Close', 'Volume']]
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