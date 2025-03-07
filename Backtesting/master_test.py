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

    def init_indicators(self, window):
        # Compute indicators up to the current bar (window)
        close = pd.Series(window.Close)
        if len(close) >= self.rsi_daily_days:
            self.rsi_daily = ta.RSI(close, self.rsi_daily_days)[-1]
        else:
            self.rsi_daily = np.nan
        
        if len(close) >= self.slow_period:
            macd, signal, _ = ta.MACD(close, self.fast_period, self.slow_period, self.signal_period)
            self.macd = macd[-1]
            self.signal = signal[-1]
        else:
            self.macd = np.nan
            self.signal = np.nan
        
        if len(close) >= self.bb_period:
            bb_upper, bb_middle, bb_lower = ta.BBANDS(close, self.bb_period, self.bb_stdev)
            self.bb_upper = bb_upper[-1]
            self.bb_middle = bb_middle[-1]
            self.bb_lower = bb_lower[-1]
        else:
            self.bb_upper = np.nan
            self.bb_middle = np.nan
            self.bb_lower = np.nan

    def get_signals(self):
        signals = {
            'rsi_daily': self.rsi_daily,
            'macd': self.macd,
            'signal_line': self.signal,
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
        rsi = self.signals['rsi_daily']
        if np.isnan(rsi):
            return 0
        if crossover([self.signals['rsi_daily_prev'], rsi], self.indicator_signals.rsi_lower_bound):
            return 1
        elif crossover(self.indicator_signals.rsi_upper_bound, [self.signals['rsi_daily_prev'], rsi]):
            return -1
        else:
            return 0

    def calc_macd_signal(self):
        macd = self.signals['macd']
        signal = self.signals['signal_line']
        if np.isnan(macd) or np.isnan(signal):
            return 0
        if crossover([self.signals['macd_prev'], macd], [self.signals['signal_prev'], signal]):
            return 1
        elif crossover([self.signals['signal_prev'], signal], [self.signals['macd_prev'], macd]):
            return -1
        else:
            return 0

    def calc_bb_signal(self, price):
        if np.isnan(self.signals['bb_lower']) or np.isnan(self.signals['bb_upper']):
            return 0
        if price < self.signals['bb_lower']:
            return 1
        elif price > self.signals['bb_upper']:
            return -1
        else:
            return 0

class WeightedStrat(Strategy):
    rsi_daily_weight_buy = 0.5
    rsi_daily_weight_sell = 0.25
    macd_weight = 0.5
    bb_weight_buy = 0.5
    bb_weight_sell = 0.25
    bb_reversal_weight_buy = 0
    bb_reversal_weight_sell = 0.25
    
    buy_threshold = 1.0
    sell_threshold = -1.0
    
    signal_window = 9
    recovery_window = 5

    def init(self):
        self.indicator_init = IndicatorInit(self.data)
        self.prev_rsi = np.nan
        self.prev_macd = np.nan
        self.prev_signal = np.nan

        # Initialize indicators for plotting
        self.rsi_values = []
        self.macd_values = []
        self.signal_values = []
        self.bb_upper_values = []
        self.bb_middle_values = []
        self.bb_lower_values = []

        self.I(lambda: self.rsi_values, name='RSI')
        self.I(lambda: self.macd_values, name='MACD')
        self.I(lambda: self.signal_values, name='Signal')
        self.I(lambda: self.bb_upper_values, name='BB Upper')
        self.I(lambda: self.bb_middle_values, name='BB Middle')
        self.I(lambda: self.bb_lower_values, name='BB Lower')

    def next(self):
        if len(self.data.Close) < 2:
            return

        # Prepare the window of data up to the current bar
        current_index = len(self.data.Close) - 1
        window = self.data.df.iloc[:current_index + 1]

        # Update indicators incrementally
        self.indicator_init.init_indicators(window)
        signals = self.indicator_init.get_signals()

        # Store previous values for crossover calculations
        signals['rsi_daily_prev'] = self.prev_rsi
        signals['macd_prev'] = self.prev_macd
        signals['signal_prev'] = self.prev_signal

        signal_calc = SignalCalc(signals, self.indicator_init)
        rsi_signal = signal_calc.calc_rsi_daily_signal()
        macd_signal = signal_calc.calc_macd_signal()
        bb_signal = signal_calc.calc_bb_signal(self.data.Close[-1])

        # Update previous values
        self.prev_rsi = signals['rsi_daily']
        self.prev_macd = signals['macd']
        self.prev_signal = signals['signal_line']

        # Append values for plotting
        self.rsi_values.append(signals['rsi_daily'] if not np.isnan(signals['rsi_daily']) else np.nan)
        self.macd_values.append(signals['macd'] if not np.isnan(signals['macd']) else np.nan)
        self.signal_values.append(signals['signal_line'] if not np.isnan(signals['signal_line']) else np.nan)
        self.bb_upper_values.append(signals['bb_upper'] if not np.isnan(signals['bb_upper']) else np.nan)
        self.bb_middle_values.append(signals['bb_middle'] if not np.isnan(signals['bb_middle']) else np.nan)
        self.bb_lower_values.append(signals['bb_lower'] if not np.isnan(signals['bb_lower']) else np.nan)

        # Bollinger Bands reversal logic
        bb_middle = signals['bb_middle']
        price = self.data.Close[-1]
        if len(self.bb_middle_values) >= 6:
            above = [1 if price > bb_middle else 0 for price in self.data.Close[-6:]]
            below = [1 if price < bb_middle else 0 for price in self.data.Close[-6:]]
            if sum(above[:3]) == 3 and sum(below[3:]) == 3:
                bb_reversal_signal = -1
            elif sum(below[:3]) == 3 and sum(above[3:]) == 3:
                bb_reversal_signal = 1
            else:
                bb_reversal_signal = 0
        else:
            bb_reversal_signal = 0

        # Calculate weighted signals using current values
        buy_signal = (
            rsi_signal * self.rsi_daily_weight_buy +
            macd_signal * self.macd_weight +
            bb_signal * self.bb_weight_buy +
            bb_reversal_signal * self.bb_reversal_weight_buy
        )

        sell_signal = (
            rsi_signal * self.rsi_daily_weight_sell +
            macd_signal * self.macd_weight +
            bb_signal * self.bb_weight_sell +
            bb_reversal_signal * self.bb_reversal_weight_sell
        )

        # Execute orders based on thresholds
        if buy_signal >= self.buy_threshold and not self.position.is_long:
            self.buy()
        elif sell_signal <= self.sell_threshold and self.position.is_long:
            self.position.close()

# BACKTESTING
ticker = 'SPY'
stock = yf.download(ticker, start='2023-01-01', end='2024-12-31')[['Open', 'High', 'Low', 'Close', 'Volume']]

bt = Backtest(stock, WeightedStrat, cash=10000, commission=.002, exclusive_orders=True)
output = bt.run()
print(output)
bt.plot(filename='backtest_result.html')