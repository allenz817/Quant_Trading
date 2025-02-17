from backtesting import Backtest, Strategy
from backtesting.lib import crossover, plot_heatmaps, resample_apply, barssince
from backtesting.test import SMA, GOOG
import yfinance as yf
import pandas as pd
import talib as ta
import seaborn as sns
import matplotlib.pyplot as plt

#IMPLEMENTATION
class SmaCross(Strategy):
    n1 = 10
    n2 = 20

    def init(self):
        close = self.data.Close
        self.sma1 = self.I(SMA, close, self.n1)
        self.sma2 = self.I(SMA, close, self.n2)

    def next(self):
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.sell()

class RsiIndicator(Strategy):
    rsi_period = 7
    rsi_upper_bound = 75
    rsi_lower_bound = 25
    
    def init(self):
        close = self.data.Close
        self.daily_rsi = self.I(ta.RSI, close, self.rsi_period)
        #self.weekly_rsi = resample_apply('W-FRI', ta.RSI, close, self.rsi_period)
        #self.position_size = 0.5
    
    def next(self):
        price = self.data.Close[-1]
        if crossover(self.rsi_lower_bound, self.daily_rsi):
        #    and self.weekly_rsi[-1] < self.rsi_lower_bound):
        #   and barssince(crossover(self.rsi_lower_bound, self.daily_rsi)) == 3:
            """
            if self.position.is_short:
                self.position.close()
            self.buy()
            """
            self.buy(
            #    size = self.position_size,
                sl=0.95*price,
            #    tp=1.2*price
                )
        elif crossover(self.daily_rsi, self.rsi_upper_bound):
        #      and self.weekly_rsi[-1] > self.rsi_upper_bound):
            #"""
            if self.position.is_long:
                self.position.close()
            #self.sell()
            #"""
            #self.position.close()
    
    """
    def plot(self, ax):
        ax.plot(self.data.index, self.rsi, label='RSI')
        ax.axhline(self.rsi_upper_bound, linestyle='--', color='red', label='RSI Upper Bound')
        ax.axhline(self.rsi_lower_bound, linestyle='--', color='green', label='RSI Lower Bound')
        ax.legend()
    """

class MACDIndicator(Strategy):
    fast_period = 12
    slow_period = 26
    signal_period = 9

    def init(self):
        close = self.data.Close
        self.macd, self.signal, _ = self.I(ta.MACD, close, self.fast_period, self.slow_period, self.signal_period)

    def next(self):
        if crossover(self.macd, self.signal):
            self.buy()
        elif crossover(self.signal, self.macd):
            self.position.close()

class BollingerBands(Strategy):
    n = 20
    n_stdev = 3.0

    def init(self):
        close = self.data.Close
        self.sma = self.I(SMA, close, self.n)
        self.std = self.I(ta.STDDEV, close, self.n)
        self.lower = self.sma - self.n_stdev * self.std
        self.upper = self.sma + self.n_stdev * self.std

    def next(self):
        price = self.data.Close[-1]
        if price < self.lower:
            self.buy()
        elif price > self.upper:
            self.position.close()
            
            

def optim_func(series):
    if series['# Trades'] < 10:
        return -1
    return series['Equity Final [$]'] / series['Exposure Time [%]']


#BACKTESTING

#1) get financial data from yfinance
ticker = '1801.HK' 
stock = yf.download(ticker, start='2022-01-01', end='2024-12-31')[
    ['Open', 'High', 'Low', 'Close', 'Volume']]
# reshape multi-index columns
stock.columns = stock.columns.droplevel(1) 

bt = Backtest(stock, RsiIndicator,
              cash=10000, commission=.002,
              exclusive_orders=True)

#2) choose output option
#output = bt.run()
#"""
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
#"""

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
print(output._trades.to_string())

print(output)
bt.plot(filename='plots/backtest_result.html')