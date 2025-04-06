from backtesting import Backtest, Strategy
from backtesting.lib import crossover, resample_apply
import yfinance as yf
import talib as ta
import numpy as np
import datetime as dt

# SIGNAL EVALUATION
def eval_rsi_daily(self):
    """
    scaled_rsi = (self.rsi_daily[-1] - 50) / 10
    return Math.custom_sigmoid(scaled_rsi)
    """
    if (crossover(self.rsi_daily, self.rsi_lower_bound)
        and all(price < self.rsi_lower_bound for price in self.data.Close[-3:-3])
    ):
        return 1 
    elif (crossover(self.rsi_upper_bound, self.rsi_daily)
          and all(price > self.rsi_upper_bound for price in self.data.Close[-3:-3])
    ):
        return -1
    else: return 0
    
def eval_rsi_weekly(self):
    if crossover(self.rsi_weekly, self.rsi_lower_bound):
        return 1 
    elif crossover(self.rsi_upper_bound, self.rsi_weekly):
        return -1
    else: return 0

# STANDALONE STRATEGY
class RSIStrategy(Strategy):
    rsi_daily_days = 12
    rsi_lower_bound = 25
    rsi_upper_bound = 75
    
    def init(self):
        close = self.data.Close
        self.rsi_daily = self.I(ta.RSI, close, self.rsi_daily_days)
        self.rsi_weekly = resample_apply('W-FRI', ta.RSI, close, self.rsi_daily_days)
        
    def next(self):
        self.signal_rsi_daily = eval_rsi_daily(self)
        self.signal_rsi_weekly = eval_rsi_weekly(self)
        self.signal = self.signal_rsi_daily + self.signal_rsi_weekly
        if self.signal >= 1 and not self.position.is_long:
            self.buy()
        elif self.signal <= -1 and self.position.is_long:
            self.position.close()
        else:
            pass
        
# STANDALONE BACKTESTING
if __name__ == "__main__":
    # Fetch financial data
    ticker = 'SPY'
    current_date = dt.datetime.now().date()
    end_date = current_date - dt.timedelta(days=1)
    stock = yf.download(ticker, start='2020-01-01', end=end_date)[['Open', 'High', 'Low', 'Close', 'Volume']]
    stock.columns = stock.columns.droplevel(1)  # Reshape multi-index columns

    # Run backtest
    bt = Backtest(stock, RSIStrategy, cash=10000, commission=0.002, exclusive_orders=True)
    #output = bt.run()
    
    output = bt.optimize(
        rsi_daily_days=range(7, 14),
        rsi_upper_bound=range(70, 90, 5),
        rsi_lower_bound=range(10, 30, 5),
        maximize = 'Sharpe Ratio',
        constraint=lambda p: p.rsi_upper_bound > p.rsi_lower_bound,
        max_tries = 1000
    )
    
    print(output._strategy)
    print(output)
    bt.plot(filename='backtest_result_rsi.html')