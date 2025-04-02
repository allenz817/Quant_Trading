from backtesting import Strategy, Backtest
import numpy as np
import datetime as dt
import yfinance as yf

# SIGNAL EVALUATION
def eval_price_mmt(strategy, average_volume_short):
        # Price momentum signal - 3 consecutive days of directional movement with enlarged volume
        if (strategy.data.Close[-1] > strategy.data.Open[-1] and
            strategy.data.Close[-3] > strategy.data.Open[-3] and
            strategy.data.Close[-1] > strategy.data.Close[-3] and
            strategy.data.Open[-1] > strategy.data.Open[-3] and
            max(strategy.data.Volume[-1], strategy.data.Volume[-2], strategy.data.Volume[-3]) / average_volume_short > strategy.volume_ratio_threshold
            and strategy.data.Close[-1] > strategy.bb_middle[-1]
            ):
            price_mmt_signal_1 = 1
        elif (strategy.data.Close[-1] < strategy.data.Open[-1] and
              strategy.data.Close[-3] < strategy.data.Open[-3] and
              strategy.data.Close[-1] < strategy.data.Close[-3] and
              strategy.data.Open[-1] < strategy.data.Open[-3] and
              max(strategy.data.Volume[-1], strategy.data.Volume[-2], strategy.data.Volume[-3]) / average_volume_short > strategy.volume_ratio_threshold
              and strategy.data.Close[-1] < strategy.bb_middle[-1]
              ):
            price_mmt_signal_1 = -1
        else:
            price_mmt_signal_1 = 0

        # Candlestick gap
        if (strategy.data.Close[-1] > strategy.data.Open[-1] and
            strategy.data.Low[-1] > strategy.data.High[-2] and
            strategy.data.Volume[-1] / average_volume_short > strategy.volume_ratio_threshold
            ):
            price_mmt_signal_2 = 1
        elif (strategy.data.Close[-1] < strategy.data.Open[-1] and
                strategy.data.High[-1] < strategy.data.Low[-2] and
                strategy.data.Volume[-1] / average_volume_short > strategy.volume_ratio_threshold
                ):
            price_mmt_signal_2 = -1
        else:
            price_mmt_signal_2 = 0
        
        return price_mmt_signal_1 + price_mmt_signal_2
    
# STANDALONE STRATEGY
class MMTStrat(Strategy):
    volume_avg_period = 20
    volume_avg_period_short = 10
    volume_ratio_threshold = 1.25
    volume_ratio_threshold_high = 1.75
    
    def init(self):
        pass
    
    def next(self):
        average_volume = np.mean(self.data.Volume[-self.volume_avg_period:])
        average_volume_short = np.mean(self.data.Volume[-self.volume_avg_period_short:])
        price_mmt_signal = eval_price_mmt(self, average_volume_short)
        
        if price_mmt_signal > 0 and not self.position.is_long:
            self.buy()
        elif price_mmt_signal < 0 and self.position.is_long:
            self.position.close()
        
# STANDALONE BACKTESTING
if __name__ == "__main__":
    # Fetch financial data
    ticker = 'SPY'
    current_date = dt.datetime.now().date()
    end_date = current_date - dt.timedelta(days=1)
    stock = yf.download(ticker, start='2020-01-01', end=end_date)[['Open', 'High', 'Low', 'Close', 'Volume']]
    stock.columns = stock.columns.droplevel(1)  # Reshape multi-index columns

    # Run backtest
    bt = Backtest(stock, MMTStrat, cash=10000, commission=0.002, exclusive_orders=True)
    output = bt.run()
    """
    output = bt.optimize(
        rsi_daily_days=range(7, 14),
        rsi_upper_bound=range(70, 90, 5),
        rsi_lower_bound=range(10, 30, 5),
        maximize = 'Sharpe Ratio',
        constraint=lambda p: p.rsi_upper_bound > p.rsi_lower_bound,
        max_tries = 1000
    )
    """
    
    print(output._strategy)
    print(output)
    bt.plot(filename='backtest_result_rsi.html')        