from backtesting.lib import crossover      

def eval_macd_daily(strategy):
    # 1- MACD crossover
    if (crossover(strategy.macd, strategy.signal) and
        30 < strategy.rsi_daily[-1] < 70 # Filter out false signals when price exhibits extreme momentum
        ):
        macd_signal_1 = 1 
    elif (crossover(strategy.signal, strategy.macd) and 
            30 < strategy.rsi_daily[-1] < 70 # Filter out false signals when price exhibits extreme momentum
            ):
        macd_signal_1 = -1
    else: macd_signal_1 = 0
    
    return macd_signal_1

def eval_macd_weekly(strategy):
    # 1- MACD crossover
    deviation_threshold = 1  # Define a threshold for deviation
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