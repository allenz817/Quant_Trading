import numpy as np

def eval_bb(strategy, average_volume):
    # 1
    # Bollinger Band support 
    if (strategy.data.Close[-2] < strategy.data.Open[-2]  # Previous candle is red
        and strategy.data.Close[-2] < strategy.bb_lower[-2] # Previous close is below lower band
        and strategy.data.Close[-1] > strategy.data.Open[-1]  # Current candle is green
        and strategy.data.Close[-1] > strategy.bb_lower[-1] # Current close is above lower band
        #and max(strategy.data.Volume[-1], strategy.data.Volume[-2]) / average_volume > strategy.volume_ratio_threshold
        #and strategy.data.Volume[-1] > strategy.data.Volume[-2]
        ):
        bb_signal_1 = 1 
    # Bollinger Band resistance
    elif (strategy.data.Close[-2] > strategy.data.Open[-2]  # Previous candle is green
            and strategy.data.Close[-2] > strategy.bb_upper[-2] # Previous close is above upper band
            and strategy.data.Close[-1] < strategy.data.Open[-1]  # Current candle is red
            and strategy.data.Close[-1] < strategy.bb_upper[-1] # Current close is below upper band
            #and max(strategy.data.Volume[-1], strategy.data.Volume[-2]) / average_volume > strategy.volume_ratio_threshold
            #and strategy.data.Volume[-1] > strategy.data.Volume[-2]
            ):
        bb_signal_1 = -1
    else: bb_signal_1 = 0
    
    # 2
    # Bollinger Band upper breakout
    if (strategy.data.Close[-2] > strategy.bb_upper[-2]
            and strategy.data.Close[-1] > strategy.bb_upper[-1]
            and np.mean(strategy.data.Volume[-2:]) / average_volume > strategy.volume_ratio_threshold
            ):
        bb_signal_2 = 1
    # Bollinger Band lower breakout
    elif (strategy.data.Close[-2] < strategy.bb_lower[-2] 
        and strategy.data.Close[-1] < strategy.bb_lower[-1]
        and np.mean(strategy.data.Volume[-2:]) / average_volume > strategy.volume_ratio_threshold
        ):
        bb_signal_2 = -1
    else: bb_signal_2 = 0
    
    # 3
    # Extreme reversal signal - top / bottom with enlarged volume
    if (strategy.data.Close[-2] < strategy.bb_lower[-2] and
        (strategy.data.Close[-1] + strategy.data.Open[-1]) / 2 > (strategy.data.Close[-2] + strategy.data.Open[-2]) / 2 and
        max(strategy.data.Volume[-1], strategy.data.Volume[-2]) / average_volume > strategy.Volume_ratio_threshold_high
        ):
        bb_signal_3 = 1
    elif (strategy.data.Close[-2] > strategy.bb_upper[-2] and
        (strategy.data.Close[-1] + strategy.data.Open[-1]) / 2 < (strategy.data.Close[-2] + strategy.data.Open[-2]) / 2 and
            max(strategy.data.Volume[-1], strategy.data.Volume[-2]) / average_volume > strategy.Volume_ratio_threshold_high
            ):
        bb_signal_3 = -1
    else: bb_signal_3 = 0
    
    """
    # 4
    # Bollinger Band Squeeze
    if strategy.bb_width[-1] < np.percentile(strategy.bb_width, 20):  # Bands are in the lowest 20% of their width
        if strategy.data.Close[-1] > strategy.bb_middle[-1]:
            bb_signal_4 = 1  # Potential bullish breakout
        elif strategy.data.Close[-1] < strategy.bb_middle[-1]:
            bb_signal_4 = -1  # Potential bearish breakout
    else: bb_signal_4 = 0
    
    # 5
    # Bollinger Band Expansion
    if strategy.bb_width[-1] > np.percentile(strategy.bb_width, 80):  # Bands are in the highest 20% of their width
        if strategy.data.Close[-1] > strategy.bb_middle[-1]:
            bb_signal_5 = 1  # Confirming bullish trend
        elif strategy.data.Close[-1] < strategy.bb_middle[-1]:
            bb_signal_5 = -1  # Confirming bearish trend
    else: bb_signal_5 = 0
    """
    
    return (bb_signal_1 
            + bb_signal_2 
            + bb_signal_3 
            #+ bb_signal_4 
            #+ bb_signal_5
    )

"""
def eval_bb_reversal(strategy, price):
    # Check if price is above or below the middle line of Bollinger Bands
    if price > strategy.bb_middle[-1]:
        strategy.bb_middle_above_test.append(1)
        strategy.bb_middle_below_test.append(0)
    elif price < strategy.bb_middle[-1]:
        strategy.bb_middle_above_test.append(0)
        strategy.bb_middle_below_test.append(1)
    else:
        strategy.bb_middle_above_test.append(0)
        strategy.bb_middle_below_test.append(0)
    
    # Keep only the last 6 days for the Bollinger Bands middle line test
    if len(strategy.bb_middle_above_test) > 6:
        strategy.bb_middle_above_test.pop(0)
    if len(strategy.bb_middle_below_test) > 6:
        strategy.bb_middle_below_test.pop(0)
    
    # Check if price has been above the middle line for 3 consecutive days and then below for 3 consecutive days
    if sum(strategy.bb_middle_above_test[:3]) == 3 and sum(strategy.bb_middle_below_test[3:]) == 3:
        return -1
    # Check if price has been below the middle line for 3 consecutive days and then above for 3 consecutive days
    elif sum(strategy.bb_middle_below_test[:3]) == 3 and sum(strategy.bb_middle_above_test[3:]) == 3:
        return 1
    else:
        return 0
"""