from backtesting import Backtest, Strategy
import yfinance as yf
import datetime as dt
from strategy_weighted import WeightedStrat

# BACKTESTING
# Get financial data from yfinance
ticker = 'AAPL' 
current_date = dt.datetime.now().date()
end_date = current_date - dt.timedelta(days=1)
stock = yf.download(ticker, start='2020-01-01', end=end_date)[['Open', 'High', 'Low', 'Close', 'Volume']]
# reshape multi-index columns
stock.columns = stock.columns.droplevel(1) 

bt = Backtest(stock, WeightedStrat, cash=10000, commission=.002, exclusive_orders=True)

# Choose output option
output = bt.run()
"""
output = bt.optimize(
    # 1-RSI
    rsi_daily_weight_buy = np.arange(0, 1, 0.1),
    rsi_daily_weight_sell = np.arange(0, 1, 0.1),
    rsi_weekly_weight = np.arange(0, 1, 0.1),
    # 2-MACD
    macd_daily_weight = np.arange(0, 1, 0.1),
    macd_weekly_weight = np.arange(0, 1, 0.1),
    # 3-Bollinger Bands
    bb_weight_buy = np.arange(0, 1, 0.1),
    bb_weight_sell = np.arange(0, 1, 0.1),
    bb_reversal_weight_buy = np.arange(0, 1, 0.1),
    bb_reversal_weight_sell = np.arange(0, 1, 0.1),
    # 4-EMA Cross - crossing between and among price and EMA lines
    ema_cross_weight = np.arange(0, 1, 0.1),
    # 5-ADX
    adx_weight = np.arange(0, 1, 0.1),
    # 6-Price Momentum
    price_mmt_weight = np.arange(0, 1, 0.1),
    # 7-Kstick
    kstick_weight = np.arange(0, 1, 0.1),
    # 8-Stochastic
    stoch_weight = np.arange(0, 1, 0.1),
    maximize = 'Sharpe Ratio',
    #maximize = optim_func,
    #constraint=lambda p: p.rsi_upper_bound > p.rsi_lower_bound,
    max_tries = 1000
)
"""

# Print result
print(output._strategy)
print(output._trades)

print(output)
bt.plot(filename='backtest_result.html')