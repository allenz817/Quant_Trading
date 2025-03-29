import numpy as np

def eval_kstick(strategy, average_volume, ema5):
        kstick_signal = 0
        # Large Green Candle at the Bottom
        if (strategy.data.Close[-1] > strategy.data.Open[-1]   # Current candle is green
            and (strategy.data.Close[-1] + strategy.data.Open[-1]) / 2 < ema5[-1] # Price is at the bottom
            and strategy.data.Close[-1] / strategy.data.Open[-1] > 1.02 # Price increased by >2%
            and strategy.data.Volume[-1] / average_volume > strategy.Volume_ratio_threshold_high # Volume is larger than average
        ):
            kstick_signal += 1
            
        # Large Red Candle at the Top
        if (strategy.data.Close[-1] < strategy.data.Open[-1]   # Current candle is red
            and (strategy.data.Close[-1] + strategy.data.Open[-1]) / 2 > ema5[-1] # Price is at the top
            and strategy.data.Open[-1] / strategy.data.Close[-1] > 1.02 # Price decreased by >2%
            and strategy.data.Volume[-1] / average_volume > strategy.Volume_ratio_threshold_high # Volume is larger than average
        ):
            kstick_signal -= 1
            
        # Bullish Engulfing
        if (strategy.data.Close[-2] < strategy.data.Open[-2] and  # Previous candle is red
            strategy.data.Close[-1] > strategy.data.Open[-1] and  # Current candle is green
            strategy.data.Close[-1] > strategy.data.Open[-2] and  # Current close is higher than previous open
            strategy.data.Open[-1] < strategy.data.Close[-2]    # Current open is lower than previous close
            and strategy.data.Volume[-1] > strategy.data.Volume[-2]
            ):
            kstick_signal += 1

        # Bearish Engulfing
        if (strategy.data.Close[-2] > strategy.data.Open[-2] and  # Previous candle is green
            strategy.data.Close[-1] < strategy.data.Open[-1] and  # Current candle is red
            strategy.data.Close[-1] < strategy.data.Open[-2] and  # Current close is lower than previous open
            strategy.data.Open[-1] > strategy.data.Close[-2]    # Current open is higher than previous close
            and strategy.data.Volume[-1] > strategy.data.Volume[-2]
            ):
            kstick_signal -= 1

        # Hammer / Inverted Hammer
        if (strategy.data.Close[-1] > strategy.data.Open[-1] # Current candle is green
            and (strategy.data.High[-1] - strategy.data.Low[-1]) > 2 * (strategy.data.Close[-1] - strategy.data.Open[-1]) # Long shadow
            # and (strategy.data.Close[-1] - strategy.data.Low[-1]) / (.001 + strategy.data.High[-1] - strategy.data.Low[-1]) > 0.6  # Close is near the high
            # and (strategy.data.Open[-1] - strategy.data.Low[-1]) / (.001 + strategy.data.High[-1] - strategy.data.Low[-1]) > 0.6 # Open is near the high
            and strategy.data.Close[-1] < np.mean(strategy.data.Close[-3:]) # Following a downtrend
            ):  
            kstick_signal += 1

        # Hanging man / Shooting star
        if (strategy.data.Close[-1] < strategy.data.Open[-1] # Current candle is red
            and (strategy.data.High[-1] - strategy.data.Low[-1]) > 2 * (strategy.data.Open[-1] - strategy.data.Close[-1]) # Long shadow
            # and (strategy.data.High[-1] - strategy.data.Close[-1]) / (.001 + strategy.data.High[-1] - strategy.data.Low[-1]) > 0.6  # Close is near the low
            # and (strategy.data.High[-1] - strategy.data.Open[-1]) / (.001 + strategy.data.High[-1] - strategy.data.Low[-1]) > 0.6 # Open is near the low
            and strategy.data.Close[-1] > np.mean(strategy.data.Close[-3:]) # Following an uptrend
            ):  
            kstick_signal -= 1

        return kstick_signal