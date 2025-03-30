from backtesting.lib import crossover
 
def eval_rsi_daily(strategy):
    """
    scaled_rsi = (self.rsi_daily[-1] - 50) / 10
    return Math.custom_sigmoid(scaled_rsi)
    """
    if (crossover(strategy.rsi_daily, strategy.rsi_lower_bound)
        and all(price < strategy.rsi_lower_bound for price in strategy.data.Close[-3:-3])
    ):
        return 1 
    elif (crossover(strategy.rsi_upper_bound, strategy.rsi_daily)
          and all(price > strategy.rsi_upper_bound for price in strategy.data.Close[-3:-3])
    ):
        return -1
    else: return 0
    
def eval_rsi_weekly(strategy):
    if crossover(strategy.rsi_weekly, strategy.rsi_lower_bound):
        return 1 
    elif crossover(strategy.rsi_upper_bound, strategy.rsi_weekly):
        return -1
    else: return 0