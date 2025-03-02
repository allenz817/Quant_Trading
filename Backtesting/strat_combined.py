from backtesting import Backtest, Strategy
from backtesting.lib import crossover, plot_heatmaps, resample_apply, barssince
from backtesting.test import SMA, GOOG
import yfinance as yf
import pandas as pd
import talib as ta
import seaborn as sns
import matplotlib.pyplot as plt

#IMPLEMENTATION
class CombinedRsiMacd(Strategy):
    rsi_period = 7
    rsi_upper_bound = 75
    rsi_lower_bound = 25
    fast_period = 12
    slow_period = 26
    bb_period = 20
    bb_stdev = 2
    signal_period = 9
    signal_window = 9  # Number of days within which both signals should occur

    def init(self):
        close = self.data.Close
        self.daily_rsi = self.I(ta.RSI, close, self.rsi_period)
        self.macd, self.signal, _ = self.I(ta.MACD, close, self.fast_period, self.slow_period, self.signal_period)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(ta.BBANDS, close, self.bb_period, self.bb_stdev)
        self.rsi_signal_days = []
        self.macd_signal_days = []
        self.bb_signal_days = []

    def next(self): # Daily check for buy/sell signals
        price = self.data.Close[-1]
        current_day = len(self.data.Close) - 1

        # Check for RSI signal
        if crossover(self.daily_rsi, self.rsi_lower_bound):
            self.rsi_signal_days.append(current_day)
        elif crossover(self.rsi_upper_bound,self.daily_rsi):
            self.rsi_signal_days.append(current_day)

        # Check for MACD signal
        if crossover(self.macd, self.signal):
            self.macd_signal_days.append(current_day)
        elif crossover(self.signal, self.macd):
            self.macd_signal_days.append(current_day)
            
        # Check for Bollinger Bands signal
        if price < self.bb_lower[-1]:
            self.bb_signal_days.append(current_day)
        elif price > self.bb_upper[-1]:
            self.bb_signal_days.append(current_day)

        # Check if both buy signals occurred within the signal window
        if self.rsi_signal_days and self.macd_signal_days:
            for rsi_day in self.rsi_signal_days:
                for macd_day in self.macd_signal_days:
                    for bb_day in self.bb_signal_days:
                        if max(rsi_day, macd_day, bb_day) - min(rsi_day, macd_day, bb_day) <= self.signal_window:
                            # Check if both MACD line and signal line are negative
                            if self.macd[-1] < 0 and self.signal[-1] < 0:
                                self.buy(
                                    #size=0.5,
                                    sl=0.95*price
                                    )
                                self.rsi_signal_days = []
                                self.macd_signal_days = []
                                self.bb_signal_days = []
                                return

        # Check if both sell signals occurred within the signal window
        if self.rsi_signal_days and self.macd_signal_days:
            for rsi_day in self.rsi_signal_days:
                for macd_day in self.macd_signal_days:
                    for bb_day in self.bb_signal_days:
                        if max(rsi_day, macd_day, bb_day) - min(rsi_day, macd_day, bb_day) <= self.signal_window:
                            if self.position.is_long:
                                self.position.close()
                            self.rsi_signal_days = []
                            self.macd_signal_days = []
                            self.bb_signal_days = []
                            return         

#BACKTESTING
#1) get financial data from yfinance
ticker = 'MSFT' 
stock = yf.download(ticker, start='2023-01-01', end='2024-12-31')[
    ['Open', 'High', 'Low', 'Close', 'Volume']]
# reshape multi-index columns
stock.columns = stock.columns.droplevel(1) 

bt = Backtest(stock, CombinedRsiMacd,
              cash=10000, commission=.002,
              exclusive_orders=True)

#2) choose output option
output = bt.run()
"""
output, heatmap = bt.optimize(
    rsi_period=range(7, 28),
    rsi_upper_bound=range(75, 90, 5),
    rsi_lower_bound=range(20, 30, 5),
    #maximize = 'Sharpe Ratio',
    #maximize = optim_func,
    constraint=lambda p: p.rsi_upper_bound > p.rsi_lower_bound,
    #max_tries = 100
    return_heatmap=True
)
"""

#3) heatmap
"""
# show heatmap table
print(heatmap) 
"""
"""
# plot heatmap graph
hm = heatmap.groupby(['rsi_period', 'rsi_upper_bound', 'rsi_lower_bound']).mean().unstack()
sns.heatmap(hm, cmap = 'viridis')
plt.show()
print(hm)
"""
#plot_heatmaps(heatmap, agg='mean')

#4) print result
#print the optimized parameters
print(output._strategy)
print(output._trades)

print(output)
bt.plot(filename='backtest_result.html')