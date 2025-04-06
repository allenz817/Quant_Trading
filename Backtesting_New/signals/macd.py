from backtesting import Backtest, Strategy
from backtesting.lib import crossover, resample_apply
import yfinance as yf
import talib as ta
import numpy as np
import datetime as dt    

def eval_macd_daily(strategy):
    threshold = 0.25
    # 1- MACD crossover
    if (crossover(strategy.macd, strategy.signal) and
        30 < strategy.rsi_daily[-1] < 70 # Filter out false signals when price exhibits extreme momentum
        and abs(strategy.hist[-1] - strategy.hist[-2]) > threshold
        ):
        macd_signal_1 = 1 
    elif (crossover(strategy.signal, strategy.macd) and 
            30 < strategy.rsi_daily[-1] < 70 # Filter out false signals when price exhibits extreme momentum
            and abs(strategy.hist[-1] - strategy.hist[-2]) > threshold
            ):
        macd_signal_1 = -1
    else: macd_signal_1 = 0
    
    return macd_signal_1

def eval_macd_weekly(strategy):
    # 1- MACD crossover
    deviation_threshold = 1.5  # Define a threshold for deviation
    if (crossover(strategy.macd_weekly, strategy.signal_weekly)
        and abs(strategy.macd_weekly[-1] - strategy.signal_weekly[-1]) > deviation_threshold
        ):
        signal_1 = 1 
    elif (crossover(strategy.signal_weekly, strategy.macd_weekly)
            and abs(strategy.macd_weekly[-1] - strategy.signal_weekly[-1]) > deviation_threshold
            ):
        signal_1 = -1
    else: signal_1 = 0
    
    return signal_1

# Standalone MACD Strategy class
class MACDStrategy(Strategy):
    fast_period = 12
    slow_period = 26
    signal_period = 9

    def init(self):
        # Initialize MACD indicators
        self.macd, self.signal, self.hist = self.I(
            ta.MACD, self.data.Close, self.fast_period, self.slow_period, self.signal_period
        )
        self.macd_weekly, self.signal_weekly, self.hist_weekly = resample_apply(
            'W-FRI', ta.MACD, self.data.Close, self.fast_period, self.slow_period, self.signal_period
            )
        self.rsi_daily = self.I(ta.RSI, self.data.Close, 14)

    def next(self):
        self.signal_macd_daily = eval_macd_daily(self)
        self.signal_macd_weekly = eval_macd_weekly(self)
        self.signal = self.signal_macd_daily + self.signal_macd_weekly
        if self.signal >= 1 and not self.position.is_long:
            self.buy()
        elif self.signal <= -1 and self.position.is_long:
            self.position.close()
        else:
            pass

# Main block for standalone execution
if __name__ == "__main__":
    # Fetch financial data
    ticker = 'AAPL'
    current_date = dt.datetime.now().date()
    end_date = current_date - dt.timedelta(days=1)
    stock = yf.download(ticker, start='2020-01-01', end=end_date)[['Open', 'High', 'Low', 'Close', 'Volume']]
    stock.columns = stock.columns.droplevel(1)  # Reshape multi-index columns if necessary

    # Run backtest
    bt = Backtest(stock, MACDStrategy, cash=10000, commission=0.002, exclusive_orders=True)
    output = bt.run()
    print(output)
    bt.plot(filename='backtest_result_macd.html')