from backtesting import Backtest, Strategy
from backtesting.lib import crossover, cross, resample_apply
import yfinance as yf
import pandas as pd
import numpy as np
import talib as ta

class WeightedStrat(Strategy):
    # Define parameters and weights for each signal
    rsi_daily_days = 7
    rsi_upper_bound = 80
    rsi_lower_bound = 25
    fast_period = 12
    slow_period = 26
    signal_period = 9
    bb_period = 20
    bb_stdev = 2
    ema5_period = 5 
    ema10_period = 10
    ema20_period = 20
    volume_avg_period = 20
    volume_avg_period_short = 10
    adx_period = 14
    
    signal_window = 9
    signal_window_short = 5
    
    # Assignment of weights (4 indicators)
    # 1-RSI
    rsi_daily_weight_buy = 0.5
    rsi_daily_weight_sell = 0.25
    rsi_weekly_weight = 0
    # 2-MACD
    macd_weight = 0.5
    # 3-Bollinger Bands
    bb_weight_buy = 0.5
    bb_weight_sell = 0.25
    bb_reversal_weight_buy = 0
    bb_reversal_weight_sell = 0.25
    # 4-EMA Cross - crossing between and among price and EMA lines
    ema_cross_weight = 0.5
    # 5-ADX
    adx_weight = 0.25
    # 6-Price Momentum
    price_mmt_weight = 0.25
    # 7-Extreme Reversal
    extreme_reversal_weight = 0.25
    
    buy_threshold = 1.0  # Threshold for executing buy orders
    sell_threshold = -1.0  # Threshold for executing sell orders
    adx_threshold = 25
    volume_ratio_threshold = 1.5
    Volume_ratio_threshold_high = 1.75
    

    def init(self):
        close = self.data.Close
        self.rsi_daily = self.I(ta.RSI, close, self.rsi_daily_days)
        self.macd, self.signal, _ = self.I(ta.MACD, close, self.fast_period, self.slow_period, self.signal_period)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(ta.BBANDS, close, self.bb_period, self.bb_stdev)
        self.ema5 = self.I(ta.EMA, close, self.ema5_period)
        self.ema10 = self.I(ta.EMA, close, self.ema10_period)
        self.ema20 = self.I(ta.EMA, close, self.ema20_period)
        self.ema60 = self.I(ta.EMA, close, 60)
        #self.ema200 = self.I(ta.EMA, close, 200)
        self.adx = self.I(ta.ADX, self.data.High, self.data.Low, close, self.adx_period)
        self.plus_di = self.I(ta.PLUS_DI, self.data.High, self.data.Low, close, self.adx_period)  # Initialize +DI
        self.minus_di = self.I(ta.MINUS_DI, self.data.High, self.data.Low, close, self.adx_period)  # Initialize -DI
  
        """
        # Calculate weekly RSI
        weekly_close = resample_apply('W-FRI', ta.RSI, close, self.rsi_daily_days)
        self.rsi_weekly = self.I(lambda: weekly_close, name='Weekly RSI')
        """
        
        self.rsi_daily_signals = []
        self.macd_signals = []
        self.bb_signals = []
        self.ema_cross_signals = []
        self.adx_signals = []
        self.bb_middle_above_test = []  # List to store results of Bollinger Bands middle line above test
        self.bb_middle_below_test = []  # List to store results of Bollinger Bands middle line below test
        self.price_mmt_signals = []
        #self.sell_price = None
        #self.sell_day = None
        
        # Register self-defined indicator for plotting
        self.bb_signal_values = np.full(len(self.data.Close), np.nan)
        self.price_mmt_values = np.full(len(self.data.Close), np.nan)
        self.ema_cross_values = np.full(len(self.data.Close), np.nan)
        self.buy_signal_values = np.full(len(self.data.Close), np.nan)
        self.sell_signal_values = np.full(len(self.data.Close), np.nan)
        self.I(lambda: self.bb_signal_values, name='BB Signal')
        self.I(lambda: self.price_mmt_values, name='Price Momentum Signal')
        self.I(lambda: self.ema_cross_values, name='EMA Cross Signal')
        self.I(lambda: self.buy_signal_values, name='Buy Signal')
        self.I(lambda: self.sell_signal_values, name='Sell Signal')
  
    def next(self):
        price = self.data.Close[-1]
        low = self.data.Low[-1]
        high = self.data.High[-1]
        open = self.data.Open[-1]
        volume = self.data.Volume[-1]
        current_day = len(self.data.Close) - 1 # Day count starts at 34
        average_volume = np.mean(self.data.Volume[-self.volume_avg_period:])
        average_volume_short = np.mean(self.data.Volume[-self.volume_avg_period_short:])

        # Calculate weighted signals
        if crossover(self.rsi_daily, self.rsi_lower_bound):
            rsi_daily_signal = 1 
        elif crossover(self.rsi_upper_bound, self.rsi_daily):
            rsi_daily_signal = -1
        else: rsi_daily_signal = 0

        if crossover(self.macd, self.signal):
            macd_signal = 1 
        elif crossover(self.signal, self.macd):
            macd_signal = -1
        else: macd_signal = 0
        
        # BOLLINGER BANDS SIGNAL
        if (self.data.Close[-2] < self.bb_lower[-2] 
            and self.data.Close[-1] > self.bb_lower[-1]
            and volume / average_volume > self.volume_ratio_threshold
            ):
            bb_signal = 1 
        elif (self.data.Close[-2] > self.bb_upper[-2]
              and self.data.Close[-1] < self.bb_upper[-1]
              and volume / average_volume > self.volume_ratio_threshold
              ):
            bb_signal = -1
        else: bb_signal = 0
        #    bb_signal = 1 - 2 * ((price - self.bb_lower[-1]) / (self.bb_upper[-1] - self.bb_lower[-1]))
        
        
        # EMA CROSSING
        # 1- Short term crossing
        if (min(self.data.Close[-2], self.data.Open[-1]) < min(self.ema5, self.ema10, self.ema20) and
            self.data.Close[-1] > max(self.ema5, self.ema10, self.ema20) and
            self.data.Close[-1] > self.data.Open[-2] and
            volume / average_volume > self.volume_ratio_threshold
            ):
            ema_cross_signal_1 = 1 
        elif (max(self.data.Close[-2], self.data.Open[-1]) > max(self.ema5, self.ema10, self.ema20) and
            self.data.Close[-1] < min(self.ema5, self.ema10, self.ema20) and
            self.data.Close[-1] < self.data.Open[-2] and
            volume / average_volume > self.volume_ratio_threshold
            ):
            ema_cross_signal_1 = -1
        else: ema_cross_signal_1 = 0
        
        # 2- Long term crossing
        if (crossover(price, self.ema60)
            #or crossover(price, self.ema200)
            #or crossover(self.ema60, self.ema200)
            and volume / average_volume > self.volume_ratio_threshold
            ):
            ema_cross_signal_2 = 1
        elif (crossover(self.ema60, price)
              #or crossover(self.ema200, price)
              #or crossover(self.ema200, self.ema60)
              and volume / average_volume > self.volume_ratio_threshold
              ):
            ema_cross_signal_2 = -1
        else: ema_cross_signal_2 = 0
        
        # Combine short and long term signals
        ema_cross_signal = ema_cross_signal_1 + ema_cross_signal_2
        
        
        # ADX signal - strong trend
        if self.adx[-1] > self.adx_threshold:
            if self.plus_di[-1] > self.minus_di[-1]:
                adx_signal = 1  # Strong upward trend
            else:
                adx_signal = -1  # Strong downward trend
        else:
            adx_signal = 0  # Weak trend
        
        # Price momentum signal - 3 consecutive days of directional movement with enlarged volume
        if (self.data.Close[-1] > self.data.Open[-1] and
            self.data.Close[-3] > self.data.Open[-3] and
            self.data.Close[-1] > self.data.Close[-3] and
            self.data.Open[-1] > self.data.Open[-3] and
            max(self.data.Volume[-1], self.data.Volume[-2], self.data.Volume[-3]) / average_volume_short > self.volume_ratio_threshold):
            price_mmt_signal = 1
        elif (self.data.Close[-1] < self.data.Open[-1] and
              self.data.Close[-3] < self.data.Open[-3] and
              self.data.Close[-1] < self.data.Close[-3] and
              self.data.Open[-1] < self.data.Open[-3] and
              max(self.data.Volume[-1], self.data.Volume[-2], self.data.Volume[-3]) / average_volume_short > self.volume_ratio_threshold):
            price_mmt_signal = -1
        else:
            price_mmt_signal = 0

        # Extreme reversal signal - top / bottom with extra enlarged volume
        if (self.data.Close[-1] > self.data.Open[-1] and
            self.data.Close[-1] < self.ema5 and
            self.data.Volume[-1] / average_volume > self.Volume_ratio_threshold_high):
            extreme_reversal_signal = 1
        elif (self.data.Close[-1] < self.data.Open[-1] and
              self.data.Close[-1] > self.ema5 and
              self.data.Volume[-1] / average_volume > self.Volume_ratio_threshold_high):
            extreme_reversal_signal = -1
        else: extreme_reversal_signal = 0
        
        # Store signals in lists
        self.rsi_daily_signals.append(rsi_daily_signal)
        self.macd_signals.append(macd_signal)
        self.bb_signals.append(bb_signal)
        self.ema_cross_signals.append(ema_cross_signal)
        self.adx_signals.append(adx_signal)
        self.price_mmt_signals.append(price_mmt_signal)
        
        # Keep only the last `signal_window` signals
        if len(self.rsi_daily_signals) > self.signal_window:
            self.rsi_daily_signals.pop(0)
        if len(self.macd_signals) > self.signal_window:
            self.macd_signals.pop(0)
        if len(self.bb_signals) > self.signal_window_short:
            self.bb_signals.pop(0)
        if len(self.ema_cross_signals) > self.signal_window_short:
            self.ema_cross_signals.pop(0)
        if len(self.adx_signals) > self.signal_window:
            self.adx_signals.pop(0)
        if len(self.price_mmt_signals) > self.signal_window_short:
            self.price_mmt_signals.pop(0)

            
        # Check if price is above or below the middle line of Bollinger Bands
        if price > self.bb_middle[-1]:
            self.bb_middle_above_test.append(1)
            self.bb_middle_below_test.append(0)
        elif price < self.bb_middle[-1]:
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
            bb_reversal_signal * self.bb_reversal_weight_buy +
            np.max(self.ema_cross_signals) * self.ema_cross_weight +
            np.max(self.adx_signals) * self.adx_weight +
            np.max(self.price_mmt_signals) * self.price_mmt_weight +
            extreme_reversal_signal * self.extreme_reversal_weight
        )
        
        sell_signal = (
            np.min(self.rsi_daily_signals) * self.rsi_daily_weight_sell +
            np.min(self.macd_signals) * self.macd_weight +
            np.min(self.bb_signals) * self.bb_weight_buy +
            bb_reversal_signal * self.bb_reversal_weight_sell +
            np.min(self.ema_cross_signals) * self.ema_cross_weight +
            np.min(self.adx_signals) * self.adx_weight +
            np.max(self.price_mmt_signals) * self.price_mmt_weight +
            extreme_reversal_signal * self.extreme_reversal_weight
        )
        
        # Execute order if total weighted signal value exceeds the threshold
        if (sell_signal <= self.sell_threshold 
            and self.position.is_long
            ):
            self.sell_price = price
            self.sell_day = current_day
            self.position.close()
            
        if (buy_signal >= self.buy_threshold
            and not self.position.is_long
            ):
            self.buy(
                #size=0.5, 
                sl=0.95*price,
            )
   
        """
        # Check for price recovery within the recovery timeframe
        if self.sell_price is not None and self.sell_day is not None:
            if (current_day - self.sell_day <= self.recovery_window and 
                price > self.sell_price and 
                not self.position.is_long
                ):
                self.buy()
                self.sell_price = None
                self.sell_day = None
        """
        
        # Update self-defined values for plotting
        self.bb_signal_values[current_day] = bb_signal
        self.price_mmt_values[current_day] = price_mmt_signal
        self.ema_cross_values[current_day] = ema_cross_signal
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