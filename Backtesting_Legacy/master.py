from backtesting import Backtest, Strategy
from backtesting.lib import crossover, cross, resample_apply
import yfinance as yf
import pandas as pd
import numpy as np
import talib as ta
import datetime as dt
from math_func import Math


class WeightedStrat(Strategy):
    # Define parameters and weights for each signal 
    rsi_daily_days = 14
    rsi_upper_bound = 70
    rsi_lower_bound = 30
    fast_period = 12
    slow_period = 26
    signal_period = 9
    bb_period = 20
    bb_stdev = 2.1
    ema5_period = 5 
    ema10_period = 10
    ema20_period = 20
    adx_period = 14
    
    stoch_k_period = 14
    stoch_d_period = 3
    stoch_upper_bound = 75
    stoch_lower_bound = 25
    
    volume_avg_period = 20
    volume_avg_period_short = 10
    
    signal_window = 5
    signal_window_short = 3
    
    # Assignment of weights to each signal
    # 1-RSI
    rsi_daily_weight_buy = 0.5
    rsi_daily_weight_sell = 0.25
    rsi_weekly_weight = 0
    # 2-MACD
    macd_daily_weight = 0.5
    macd_weekly_weight = 0.25
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
    
    # 7-Kstick
    kstick_weight = 0.25
    # 8-Stochastic
    stoch_weight = 0.25
    
    buy_threshold = 1.0  # Threshold for executing buy orders
    sell_threshold = -1.0  # Threshold for executing sell orders
    adx_threshold = 25
    volume_ratio_threshold = 1.25
    Volume_ratio_threshold_high = 1.75
    

    def init(self):
        close = self.data.Close
        #print(len(close))
        # Calculate daily indicators
        self.rsi_daily = self.I(ta.RSI, close, self.rsi_daily_days)
        self.macd, self.signal, _ = self.I(ta.MACD, close, self.fast_period, self.slow_period, self.signal_period)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(ta.BBANDS, close, self.bb_period, self.bb_stdev)
        self.bb_width = self.I(self.calc_bb_width)
        self.ema5 = self.I(ta.EMA, close, self.ema5_period)
        self.ema10 = self.I(ta.EMA, close, self.ema10_period)
        self.ema20 = self.I(ta.EMA, close, self.ema20_period)
        self.ema60 = self.I(ta.EMA, close, 60)
        self.ema120 = self.I(ta.EMA, close, 120)
        self.adx = self.I(ta.ADX, self.data.High, self.data.Low, close, self.adx_period)
        self.plus_di = self.I(ta.PLUS_DI, self.data.High, self.data.Low, close, self.adx_period)  # Initialize +DI
        self.minus_di = self.I(ta.MINUS_DI, self.data.High, self.data.Low, close, self.adx_period)  # Initialize -DI
        self.stoch_k, self.stoch_d = self.I(
            ta.STOCH, self.data.High, self.data.Low, close, 
            fastk_period=self.stoch_k_period, slowk_period=self.stoch_d_period, slowk_matype=0,
            slowd_period=self.stoch_d_period, slowd_matype=0
            )
        
        # Calculate weekly indicators
        self.rsi_weekly = resample_apply('W-FRI', ta.RSI, close, self.rsi_daily_days)
        self.macd_weekly, self.signal_weekly, _ = resample_apply('W-FRI', ta.MACD, close, self.fast_period, self.slow_period, self.signal_period)
        
        # Initialize signal storage
        self.signals = {
            'rsi_daily': [],
            'rsi_weekly': [],
            'macd_daily': [],
            'macd_weekly': [],
            'bb': [],
            'ema_cross': [],
            'adx': [],
            'price_mmt': [],
            'kstick': [],
            'stoch': [],
            'buy': [],
            'sell': []
        }
        
        # Register self-defined indicator for plotting
        data_length = len(self.data.Close)
        self.signal_values = {
            'rsi_daily': np.full(data_length, np.nan),
            'rsi_weekly': np.full(data_length, np.nan),
            'macd_daily': np.full(data_length, np.nan),
            'macd_weekly': np.full(data_length, np.nan),
            'adx': np.full(data_length, np.nan),
            'bb': np.full(data_length, np.nan),
            'price_mmt': np.full(data_length, np.nan),
            'ema_cross': np.full(data_length, np.nan),
            'kstick': np.full(data_length, np.nan),
            'stoch': np.full(data_length, np.nan),
            'buy': np.full(data_length, np.nan),
            'sell': np.full(data_length, np.nan)
        }
        self.I(lambda: self.signal_values['rsi_daily'], name='RSI Daily Signal')
        self.I(lambda: self.signal_values['rsi_weekly'], name='RSI Weekly Signal')
        self.I(lambda: self.signal_values['macd_daily'], name='MACD Signal')
        self.I(lambda: self.signal_values['macd_weekly'], name='MACD Weekly Signal')
        self.I(lambda: self.signal_values['adx'], name='ADX Signal')
        self.I(lambda: self.signal_values['bb'], name='BB Signal')
        self.I(lambda: self.signal_values['price_mmt'], name='Price Momentum Signal')
        self.I(lambda: self.signal_values['ema_cross'], name='EMA Cross Signal')
        self.I(lambda: self.signal_values['kstick'], name='Kstick Signal')
        self.I(lambda: self.signal_values['stoch'], name='Stochastic Signal')
        self.I(lambda: self.signal_values['buy'], name='Buy Signal')
        self.I(lambda: self.signal_values['sell'], name='Sell Signal')
        
        #print(len(self.data.Close))

    # CALCULATION FUNCTIONS
    def calc_bb_width(self):
        return self.bb_upper - self.bb_lower
    
    def cal_sup_res(self):
        # Calculate support and resistance levels
        support_resistance = {
            'sup': [],
            'res': []
        }
        # EMA
        if self.data.Close[-1] > self.ema5[-1]:
            support_resistance['sup'].append(self.ema5[-1])
        else:
            support_resistance['res'].append(self.ema5[-1])
        if self.data.Close[-1] > self.ema10[-1]:
            support_resistance['sup'].append(self.ema10[-1])
        else:
            support_resistance['res'].append(self.ema10[-1])
        if self.data.Close[-1] > self.ema20[-1]:
            support_resistance['sup'].append(self.ema20[-1])
        else:
            support_resistance['res'].append(self.ema20[-1])
        if self.data.Close[-1] > self.ema60[-1]:
            support_resistance['sup'].append(self.ema60[-1])
        else:
            support_resistance['res'].append(self.ema60[-1])
        # Bollinger Bands
        support_resistance['sup'].append(self.bb_lower[-1])
        support_resistance['res'].append(self.bb_upper[-1])
        if self.data.Close[-1] > self.bb_middle[-1]:
            support_resistance['sup'].append(self.bb_middle[-1]) 
        else:
            support_resistance['res'].append(self.bb_middle[-1])
            
        support_resistance['sup'] = sorted(support_resistance['sup'], reverse=True) # Sort in descending order
        support_resistance['res'] = sorted(support_resistance['res']) # Sort in ascending order
        
        return support_resistance
        
        
    # SIGNAL EVALUATION FUNCTIONS
    def eval_rsi_daily(self):
        """
        scaled_rsi = (self.rsi_daily[-1] - 50) / 10
        return Math.custom_sigmoid(scaled_rsi)
        """
        if crossover(self.rsi_daily, self.rsi_lower_bound):
            return 1 
        elif crossover(self.rsi_upper_bound, self.rsi_daily):
            return -1
        else: return 0
        
    def eval_rsi_weekly(self):
        if crossover(self.rsi_weekly, self.rsi_lower_bound):
            return 1 
        elif crossover(self.rsi_upper_bound, self.rsi_weekly):
            return -1
        else: return 0
        
    def eval_macd_daily(self):
        # 1- MACD crossover
        if (crossover(self.macd, self.signal) and
            30 < self.rsi_daily[-1] < 70 # Filter out false signals when price exhibits extreme momentum
            ):
            macd_signal_1 = 1 
        elif (crossover(self.signal, self.macd) and 
              30 < self.rsi_daily[-1] < 70 # Filter out false signals when price exhibits extreme momentum
              ):
            macd_signal_1 = -1
        else: macd_signal_1 = 0
        
        return macd_signal_1
    
    def eval_macd_weekly(self):
        # 1- MACD crossover
        deviation_threshold = 1  # Define a threshold for deviation
        if (crossover(self.macd_weekly, self.signal_weekly)
            and abs(self.macd_weekly[-1] - self.signal_weekly[-1]) > deviation_threshold
            ):
            signal_1 = 1 
        elif (crossover(self.signal_weekly, self.macd_weekly)
              and abs(self.macd_weekly[-1] - self.signal_weekly[-1]) > deviation_threshold
              ):
            signal_1 = -1
        else: signal_1 = 0
        
        return signal_1
    
    def eval_bb(self, volume, average_volume):
        # 1
        # Bollinger Band support 
        if (self.data.Close[-2] < self.data.Open[-2]  # Previous candle is red
            and self.data.Close[-2] < self.bb_lower[-2] # Previous close is below lower band
            and self.data.Close[-1] > self.data.Open[-1]  # Current candle is green
            and self.data.Close[-1] > self.bb_lower[-1] # Current close is above lower band
            #and max(self.data.Volume[-1], self.data.Volume[-2]) / average_volume > self.volume_ratio_threshold
            #and self.data.Volume[-1] > self.data.Volume[-2]
            ):
            bb_signal_1 = 1 
        # Bollinger Band resistance
        elif (self.data.Close[-2] > self.data.Open[-2]  # Previous candle is green
              and self.data.Close[-2] > self.bb_upper[-2] # Previous close is above upper band
              and self.data.Close[-1] < self.data.Open[-1]  # Current candle is red
              and self.data.Close[-1] < self.bb_upper[-1] # Current close is below upper band
              #and max(self.data.Volume[-1], self.data.Volume[-2]) / average_volume > self.volume_ratio_threshold
              #and self.data.Volume[-1] > self.data.Volume[-2]
              ):
            bb_signal_1 = -1
        else: bb_signal_1 = 0
        
        # 2
        # Bollinger Band upper breakout
        if (self.data.Close[-2] > self.bb_upper[-2]
              and self.data.Close[-1] > self.bb_upper[-1]
              and np.mean(self.data.Volume[-2:]) / average_volume > self.volume_ratio_threshold
              ):
            bb_signal_2 = 1
        # Bollinger Band lower breakout
        elif (self.data.Close[-2] < self.bb_lower[-2] 
            and self.data.Close[-1] < self.bb_lower[-1]
            and np.mean(self.data.Volume[-2:]) / average_volume > self.volume_ratio_threshold
            ):
            bb_signal_2 = -1
        else: bb_signal_2 = 0
        
        # 3
        # Extreme reversal signal - top / bottom with enlarged volume
        if (self.data.Close[-2] < self.bb_lower[-2] and
            (self.data.Close[-1] + self.data.Open[-1]) / 2 > (self.data.Close[-2] + self.data.Open[-2]) / 2 and
            max(self.data.Volume[-1], self.data.Volume[-2]) / average_volume > self.Volume_ratio_threshold_high
            ):
            bb_signal_3 = 1
        elif (self.data.Close[-2] > self.bb_upper[-2] and
            (self.data.Close[-1] + self.data.Open[-1]) / 2 < (self.data.Close[-2] + self.data.Open[-2]) / 2 and
              max(self.data.Volume[-1], self.data.Volume[-2]) / average_volume > self.Volume_ratio_threshold_high
              ):
            bb_signal_3 = -1
        else: bb_signal_3 = 0
        
        # 4
        # Bollinger Band Squeeze
        if self.bb_width[-1] < np.percentile(self.bb_width, 20):  # Bands are in the lowest 20% of their width
            if self.data.Close[-1] > self.bb_middle[-1]:
                bb_signal_4 = 1  # Potential bullish breakout
            elif self.data.Close[-1] < self.bb_middle[-1]:
                bb_signal_4 = -1  # Potential bearish breakout
        else: bb_signal_4 = 0
        
        # 5
        # Bollinger Band Expansion
        if self.bb_width[-1] > np.percentile(self.bb_width, 80):  # Bands are in the highest 20% of their width
            if self.data.Close[-1] > self.bb_middle[-1]:
                bb_signal_5 = 1  # Confirming bullish trend
            elif self.data.Close[-1] < self.bb_middle[-1]:
                bb_signal_5 = -1  # Confirming bearish trend
        else: bb_signal_5 = 0
        
        return bb_signal_1 + bb_signal_2 + bb_signal_3 + bb_signal_4 + bb_signal_5
    
    
    def eval_bb_reversal(self, price):
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
            return -1
        # Check if price has been below the middle line for 3 consecutive days and then above for 3 consecutive days
        elif sum(self.bb_middle_below_test[:3]) == 3 and sum(self.bb_middle_above_test[3:]) == 3:
            return 1
        else:
            return 0
        
    def eval_ema_cross(self, price, volume, average_volume):
        # 1- Price crossing 3 EMA lines
        if (min(self.data.Close[-2], self.data.Open[-1]) < min(self.ema5[-1], self.ema10[-1], self.ema20[-1]) and
            self.data.Close[-1] > max(self.ema5[-1], self.ema10[-1], self.ema20[-1]) and
            self.data.Close[-1] > self.data.Open[-2] and
            volume / average_volume > 1
            ):
            ema_cross_signal_1 = 1 
        elif (max(self.data.Close[-2], self.data.Open[-1]) > max(self.ema5[-1], self.ema10[-1], self.ema20[-1]) and
            self.data.Close[-1] < min(self.ema5[-1], self.ema10[-1], self.ema20[-1]) and
            self.data.Close[-1] < self.data.Open[-2] and
            volume / average_volume > 1
            ):
            ema_cross_signal_1 = -1
        else: ema_cross_signal_1 = 0
          
        # 2- 3 EMA lines crossing
        if (self.ema5[-1] > self.ema10[-1] > self.ema20[-1] and
            self.ema5[-5] < self.ema10[-5] < self.ema20[-5] 
            ):
            ema_cross_signal_2 = 1
        elif (self.ema5[-1] < self.ema10[-1] < self.ema20[-1] and
              self.ema5[-5] > self.ema10[-5] > self.ema20[-5]
              ):
            ema_cross_signal_2 = -1
        else: ema_cross_signal_2 = 0
        
        # 3- Long term crossing
        if (crossover(price, self.ema60)
            #or crossover(price, self.ema200)
            #or crossover(self.ema60, self.ema200)
            and volume / average_volume > self.volume_ratio_threshold
            ):
            ema_cross_signal_3 = 1
        elif (crossover(self.ema60, price)
              #or crossover(self.ema200, price)
              #or crossover(self.ema200, self.ema60)
              and volume / average_volume > self.volume_ratio_threshold
              ):
            ema_cross_signal_3 = -1
        else: ema_cross_signal_3 = 0
        
        # Combine short and long term signals
        return ema_cross_signal_1 + ema_cross_signal_2 + ema_cross_signal_3
    
    def eval_adx(self):
        if self.adx[-1] > self.adx_threshold:
            if self.plus_di[-1] > self.minus_di[-1]:
                return 1  # Strong upward trend
            else:
                return -1  # Strong downward trend
        else:
            return 0  # Weak trend
    
    def eval_price_mmt(self, average_volume_short):
        # Price momentum signal - 3 consecutive days of directional movement with enlarged volume
        if (self.data.Close[-1] > self.data.Open[-1] and
            self.data.Close[-3] > self.data.Open[-3] and
            self.data.Close[-1] > self.data.Close[-3] and
            self.data.Open[-1] > self.data.Open[-3] and
            max(self.data.Volume[-1], self.data.Volume[-2], self.data.Volume[-3]) / average_volume_short > self.volume_ratio_threshold
            and self.data.Close[-1] > self.bb_middle[-1]
            ):
            price_mmt_signal_1 = 1
        elif (self.data.Close[-1] < self.data.Open[-1] and
              self.data.Close[-3] < self.data.Open[-3] and
              self.data.Close[-1] < self.data.Close[-3] and
              self.data.Open[-1] < self.data.Open[-3] and
              max(self.data.Volume[-1], self.data.Volume[-2], self.data.Volume[-3]) / average_volume_short > self.volume_ratio_threshold
              and self.data.Close[-1] < self.bb_middle[-1]
              ):
            price_mmt_signal_1 = -1
        else:
            price_mmt_signal_1 = 0
        
        # Candlestick gap
        if (self.data.Close[-1] > self.data.Open[-1] and
            self.data.Low[-1] > self.data.High[-2] and
            self.data.Volume[-1] / average_volume_short > self.volume_ratio_threshold
            ):
            price_mmt_signal_2 = 1
        elif (self.data.Close[-1] < self.data.Open[-1] and
              self.data.High[-1] < self.data.Low[-2] and
              self.data.Volume[-1] / average_volume_short > self.volume_ratio_threshold
              ):
            price_mmt_signal_2 = -1
        else:
            price_mmt_signal_2 = 0
        
        return price_mmt_signal_1 + price_mmt_signal_2
    
    def eval_kstick(self, average_volume, ema5, bb_mid):
        kstick_signal = 0
        # Large Green Candle at the Bottom
        if (self.data.Close[-1] > self.data.Open[-1]   # Current candle is green
            and (self.data.Close[-1] + self.data.Open[-1]) / 2 < ema5[-1] # Price is at the bottom
            and self.data.Close[-1] / self.data.Open[-1] > 1.02 # Price increased by >2%
            and self.data.Volume[-1] / average_volume > self.Volume_ratio_threshold_high # Volume is larger than average
        ):
            kstick_signal += 1
            
        # Large Red Candle at the Top
        if (self.data.Close[-1] < self.data.Open[-1]   # Current candle is red
            and (self.data.Close[-1] + self.data.Open[-1]) / 2 > ema5[-1] # Price is at the top
            and self.data.Open[-1] / self.data.Close[-1] > 1.02 # Price decreased by >2%
            and self.data.Volume[-1] / average_volume > self.Volume_ratio_threshold_high # Volume is larger than average
        ):
            kstick_signal -= 1
            
        # Bullish Engulfing
        if (self.data.Close[-2] < self.data.Open[-2] and  # Previous candle is red
            self.data.Close[-1] > self.data.Open[-1] and  # Current candle is green
            self.data.Close[-1] > self.data.Open[-2] and  # Current close is higher than previous open
            self.data.Open[-1] < self.data.Close[-2]    # Current open is lower than previous close
            and self.data.Volume[-1] > self.data.Volume[-2]
            ):
            kstick_signal += 1

        # Bearish Engulfing
        if (self.data.Close[-2] > self.data.Open[-2] and  # Previous candle is green
            self.data.Close[-1] < self.data.Open[-1] and  # Current candle is red
            self.data.Close[-1] < self.data.Open[-2] and  # Current close is lower than previous open
            self.data.Open[-1] > self.data.Close[-2]    # Current open is higher than previous close
            and self.data.Volume[-1] > self.data.Volume[-2]
            ):
            kstick_signal -= 1

        # Hammer / Inverted Hammer
        if (self.data.Close[-1] > self.data.Open[-1] # Current candle is green
            and (self.data.High[-1] - self.data.Low[-1]) > 2 * (self.data.Close[-1] - self.data.Open[-1]) # Long shadow
            # and (self.data.Close[-1] - self.data.Low[-1]) / (.001 + self.data.High[-1] - self.data.Low[-1]) > 0.6  # Close is near the high
            # and (self.data.Open[-1] - self.data.Low[-1]) / (.001 + self.data.High[-1] - self.data.Low[-1]) > 0.6 # Open is near the high
            and self.data.Close[-1] < np.mean(self.data.Close[-3:]) # Following a downtrend
            ):  
            kstick_signal += 1

        # Hanging man / Shooting star
        if (self.data.Close[-1] < self.data.Open[-1] # Current candle is red
            and (self.data.High[-1] - self.data.Low[-1]) > 2 * (self.data.Open[-1] - self.data.Close[-1]) # Long shadow
            # and (self.data.High[-1] - self.data.Close[-1]) / (.001 + self.data.High[-1] - self.data.Low[-1]) > 0.6  # Close is near the low
            # and (self.data.High[-1] - self.data.Open[-1]) / (.001 + self.data.High[-1] - self.data.Low[-1]) > 0.6 # Open is near the low
            and self.data.Close[-1] > np.mean(self.data.Close[-3:]) # Following an uptrend
            ):  
            kstick_signal -= 1

        return kstick_signal

    def eval_stoch(self):
        # Stochastic Oscillator
        if crossover(self.stoch_k, self.stoch_d) and self.stoch_k[-1] < self.stoch_lower_bound:
            return 1
        elif crossover(self.stoch_d, self.stoch_k) and self.stoch_k[-1] > self.stoch_upper_bound:
            return -1
        else:
            return 0

    def next(self):

        price = self.data.Close[-1]
        low = self.data.Low[-1]
        high = self.data.High[-1]
        open = self.data.Open[-1]
        mid = (open + price) / 2
        volume = self.data.Volume[-1]
        current_day = len(self.data.Close) - 1

        #print(current_day)
        average_volume = np.mean(self.data.Volume[-self.volume_avg_period:])
        average_volume_short = np.mean(self.data.Volume[-self.volume_avg_period_short:])

        # Call function to evaluate signals
        rsi_daily_signal = self.eval_rsi_daily()
        rsi_weekly_signal = self.eval_rsi_weekly()
        macd_daily_signal = self.eval_macd_daily()
        macd_weekly_signal = self.eval_macd_weekly()
        bb_signal = self.eval_bb(volume, average_volume)
        #bb_reversal_signal = self.eval_bb_reversal(price)
        ema_cross_signal = self.eval_ema_cross(price, volume, average_volume)
        adx_signal = self.eval_adx()
        price_mmt_signal = self.eval_price_mmt(average_volume_short)
        kstick_signal = self.eval_kstick(average_volume, self.ema5)
        stoch_signal = self.eval_stoch()

        # Store signals in lists
        self.signals['rsi_daily'].append(rsi_daily_signal)
        self.signals['rsi_weekly'].append(rsi_weekly_signal)
        self.signals['macd_daily'].append(macd_daily_signal)
        self.signals['macd_weekly'].append(macd_weekly_signal)
        self.signals['bb'].append(bb_signal)
        self.signals['ema_cross'].append(ema_cross_signal)
        self.signals['adx'].append(adx_signal)
        self.signals['price_mmt'].append(price_mmt_signal)
        self.signals['kstick'].append(kstick_signal)
        self.signals['stoch'].append(stoch_signal)

        # Keep only the last `signal_window` signals
        if len(self.signals['rsi_daily']) > self.signal_window:
            self.signals['rsi_daily'].pop(0)
        if len(self.signals['rsi_weekly']) > self.signal_window:
            self.signals['rsi_weekly'].pop(0)
        if len(self.signals['macd_daily']) > self.signal_window:
            self.signals['macd_daily'].pop(0)
        if len(self.signals['macd_weekly']) > self.signal_window:
            self.signals['macd_weekly'].pop(0)
        if len(self.signals['bb']) > self.signal_window_short:
            self.signals['bb'].pop(0)
        if len(self.signals['ema_cross']) > self.signal_window_short:
            self.signals['ema_cross'].pop(0)
        if len(self.signals['adx']) > self.signal_window_short:
            self.signals['adx'].pop(0)
        if len(self.signals['price_mmt']) > self.signal_window_short:
            self.signals['price_mmt'].pop(0)
        if len(self.signals['kstick']) > self.signal_window_short:
            self.signals['kstick'].pop(0)
        if len(self.signals['stoch']) > self.signal_window_short:
            self.signals['stoch'].pop(0)

        # Calculate total weighted signal value over the lookback period
        buy_signal = (
            np.max(self.signals['rsi_daily']) * self.rsi_daily_weight_buy +
            np.max(self.signals['rsi_weekly']) * self.rsi_weekly_weight +
            np.max(self.signals['macd_daily']) * self.macd_daily_weight +
            np.max(self.signals['macd_weekly']) * self.macd_weekly_weight +
            np.max(self.signals['bb']) * self.bb_weight_buy +
            #bb_reversal_signal * self.bb_reversal_weight_buy +
            np.max(self.signals['ema_cross']) * self.ema_cross_weight +
            np.max(self.signals['adx']) * self.adx_weight +
            np.max(self.signals['price_mmt']) * self.price_mmt_weight +
            np.max(self.signals['kstick']) * self.kstick_weight +
            np.max(self.signals['stoch']) * self.stoch_weight
        )
        
        sell_signal = (
            np.min(self.signals['rsi_daily']) * self.rsi_daily_weight_sell +
            np.min(self.signals['rsi_weekly']) * self.rsi_weekly_weight +
            np.min(self.signals['macd_daily']) * self.macd_daily_weight +
            np.min(self.signals['macd_weekly']) * self.macd_weekly_weight +
            np.min(self.signals['bb']) * self.bb_weight_buy +
            #bb_reversal_signal * self.bb_reversal_weight_sell +
            np.min(self.signals['ema_cross']) * self.ema_cross_weight +
            np.min(self.signals['adx']) * self.adx_weight +
            np.min(self.signals['price_mmt']) * self.price_mmt_weight +
            np.min(self.signals['kstick']) * self.kstick_weight +
            np.min(self.signals['stoch']) * self.stoch_weight
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
        self.signal_values['rsi_daily'][current_day] = rsi_daily_signal
        self.signal_values['rsi_weekly'][current_day] = rsi_weekly_signal
        self.signal_values['macd_daily'][current_day] = macd_daily_signal
        self.signal_values['macd_weekly'][current_day] = macd_weekly_signal
        self.signal_values['adx'][current_day] = adx_signal
        self.signal_values['bb'][current_day] = bb_signal
        self.signal_values['price_mmt'][current_day] = price_mmt_signal
        self.signal_values['ema_cross'][current_day] = ema_cross_signal
        self.signal_values['kstick'][current_day] = kstick_signal
        self.signal_values['stoch'][current_day] = stoch_signal
        
        self.signal_values['buy'][current_day] = buy_signal
        self.signal_values['sell'][current_day] = sell_signal



# BACKTESTING
# Get financial data from yfinance
ticker = 'SPY' 
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