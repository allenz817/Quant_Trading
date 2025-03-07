from backtesting import Backtest, Strategy
from backtesting.lib import crossover, resample_apply
import yfinance as yf
import pandas as pd
import numpy as np
import talib as ta

class IndicatorInit:
    def __init__(self, data):
        self.data = data
        self.rsi_daily_days = 7
        self.rsi_upper_bound = 80
        self.rsi_lower_bound = 25
        self.fast_period = 12
        self.slow_period = 26
        self.signal_period = 9
        self.bb_period = 20
        self.bb_stdev = 2

    def init_indicators(self):
        close = self.data.Close
        self.rsi_daily = ta.RSI(close, self.rsi_daily_days)
        self.macd, self.signal, _ = ta.MACD(close, self.fast_period, self.slow_period, self.signal_period)
        self.bb_upper, self.bb_middle, self.bb_lower = ta.BBANDS(close, self.bb_period, self.bb_stdev)

    def get_signals(self):
        signals = {
            'rsi_daily': self.rsi_daily,
            'macd': self.macd,
            'signal': self.signal,
            'bb_upper': self.bb_upper,
            'bb_middle': self.bb_middle,
            'bb_lower': self.bb_lower
        }
        return signals

class SignalCalc:
    def __init__(self, signals, indicator_signals):
        self.signals = signals
        self.indicator_signals = indicator_signals

    def calc_rsi_daily_signal(self):
        if crossover(self.signals['rsi_daily'], self.indicator_signals.rsi_lower_bound):
            return 1
        elif crossover(self.indicator_signals.rsi_upper_bound, self.signals['rsi_daily']):
            return -1
        else:
            return 0

    def calc_macd_signal(self):
        if crossover(self.signals['macd'], self.signals['signal']):
            return 1
        elif crossover(self.signals['signal'], self.signals['macd']):
            return -1
        else:
            return 0

    def calc_bb_signal(self, price):
        if price < self.signals['bb_lower'][-1]:
            return 1
        elif price > self.signals['bb_upper'][-1]:
            return -1
        else:
            return 0

class WeightedStrat(Strategy):

    rsi_daily_weight_buy = 0.5
    rsi_daily_weight_sell = 0.25
    rsi_weekly_weight = 0
    macd_weight = 0.5
    bb_weight_buy = 0.5
    bb_weight_sell = 0.25
    bb_reversal_weight_buy = 0
    bb_reversal_weight_sell = 0.25
    
    buy_threshold = 1.0  # Threshold for executing buy orders
    sell_threshold = -1.0  # Threshold for executing sell orders
    
    signal_window = 9
    recovery_window = 5

    def init(self):
        self.indicator_init = IndicatorInit(self.data)
        self.indicator_init.init_indicators()
        self.signals = self.indicator_init.get_signals()
        self.signal_calc = SignalCalc(self.signals, self.indicator_init)

        self.rsi_daily_signals = []
        self.macd_signals = []
        self.bb_signals = []
        self.bb_middle_above_test = []  # List to store results of Bollinger Bands middle line above test
        self.bb_middle_below_test = []  # List to store results of Bollinger Bands middle line below test
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
        current_day = len(self.data.Close) - 1

        # Calculate weighted signals
        rsi_daily_signal = self.signal_calc.calc_rsi_daily_signal()
        macd_signal = self.signal_calc.calc_macd_signal()
        bb_signal = self.signal_calc.calc_bb_signal(price)

        # Store signals in lists
        self.rsi_daily_signals.append(rsi_daily_signal)
        self.macd_signals.append(macd_signal)
        self.bb_signals.append(bb_signal)

        # Keep only the last `signal_window` signals
        if len(self.rsi_daily_signals) > self.signal_window:
            self.rsi_daily_signals.pop(0)
        if len(self.macd_signals) > self.signal_window:
            self.macd_signals.pop(0)
        if len(self.bb_signals) > self.signal_window:
            self.bb_signals.pop(0)

        # Check if price is above or below the middle line of Bollinger Bands
        if price > self.signals['bb_middle'][-1]:
            self.bb_middle_above_test.append(1)
            self.bb_middle_below_test.append(0)
        elif price < self.signals['bb_middle'][-1]:
            self.bb_middle_above_test.append(0)
            self.bb_middle_below_test.append(1)
        else:
            self.bb_middle_above_test.append(0)
            self.bb_middle_below_test.append(0)

        # Keep only the last 6 days for the Bollinger Bands middle line test
        if len(self.bb_middle_above_test) > 6:
            self.bb_middle_above_test.pop(0)
        if len(self.bb_middle_below_test) > 6:
            self.bb_middle_below_test.pop(0)

        # Check if price has been above the middle line for 3 consecutive days and then below for 3 consecutive days
        if sum(self.bb_middle_above_test[:3]) == 3 and sum(self.bb_middle_below_test[3:]) == 3:
            bb_reversal_signal = -1
        # Check if price has been below the middle line for 3 consecutive days and then above for 3 consecutive days
        elif sum(self.bb_middle_below_test[:3]) == 3 and sum(self.bb_middle_above_test[3:]) == 3:
            bb_reversal_signal = 1
        else:
            bb_reversal_signal = 0

        # Calculate total weighted signal value over the lookback period
        buy_signal = (
            np.max(self.rsi_daily_signals) * self.rsi_daily_weight_buy +
            np.max(self.macd_signals) * self.macd_weight +
            np.max(self.bb_signals) * self.bb_weight_buy +
            bb_reversal_signal * self.bb_reversal_weight_buy
        )

        sell_signal = (
            np.min(self.rsi_daily_signals) * self.rsi_daily_weight_sell +
            np.min(self.macd_signals) * self.macd_weight +
            np.min(self.bb_signals) * self.bb_weight_sell +
            bb_reversal_signal * self.bb_reversal_weight_sell
        )

        # Execute buy order if total weighted signal value exceeds the threshold
        if buy_signal >= self.buy_threshold and not self.position.is_long:
            self.buy(sl=0.95*price)

        # Execute sell order if total weighted signal value exceeds the threshold
        if sell_signal <= self.sell_threshold and self.position.is_long:
            self.sell_price = price
            self.sell_day = current_day
            self.position.close()

        # Update self-defined values for plotting
        self.bb_signal_values[current_day] = bb_signal
        self.buy_signal_values[current_day] = buy_signal
        self.sell_signal_values[current_day] = sell_signal

# BACKTESTING
# Get financial data from yfinance
ticker = 'SPY' 
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