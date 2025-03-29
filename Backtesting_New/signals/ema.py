from backtesting.lib import crossover

def eval_ema_cross(strategy, price, volume, average_volume):
        # 1- Price crossing 3 EMA lines
        if (min(strategy.data.Close[-2], strategy.data.Open[-1]) < min(strategy.ema5[-1], strategy.ema10[-1], strategy.ema20[-1]) and
            strategy.data.Close[-1] > max(strategy.ema5[-1], strategy.ema10[-1], strategy.ema20[-1]) and
            strategy.data.Close[-1] > strategy.data.Open[-2] and
            volume / average_volume > 1
            ):
            ema_cross_signal_1 = 1 
        elif (max(strategy.data.Close[-2], strategy.data.Open[-1]) > max(strategy.ema5[-1], strategy.ema10[-1], strategy.ema20[-1]) and
            strategy.data.Close[-1] < min(strategy.ema5[-1], strategy.ema10[-1], strategy.ema20[-1]) and
            strategy.data.Close[-1] < strategy.data.Open[-2] and
            volume / average_volume > 1
            ):
            ema_cross_signal_1 = -1
        else: ema_cross_signal_1 = 0
          
        # 2- 3 EMA lines crossing
        if (strategy.ema5[-1] > strategy.ema10[-1] > strategy.ema20[-1] and
            strategy.ema5[-5] < strategy.ema10[-5] < strategy.ema20[-5] 
            ):
            ema_cross_signal_2 = 1
        elif (strategy.ema5[-1] < strategy.ema10[-1] < strategy.ema20[-1] and
              strategy.ema5[-5] > strategy.ema10[-5] > strategy.ema20[-5]
              ):
            ema_cross_signal_2 = -1
        else: ema_cross_signal_2 = 0
        
        # 3- Long term crossing
        if (crossover(price, strategy.ema60)
            #or crossover(price, strategy.ema200)
            #or crossover(strategy.ema60, strategy.ema200)
            and volume / average_volume > strategy.volume_ratio_threshold
            ):
            ema_cross_signal_3 = 1
        elif (crossover(strategy.ema60, price)
              #or crossover(strategy.ema200, price)
              #or crossover(strategy.ema200, strategy.ema60)
              and volume / average_volume > strategy.volume_ratio_threshold
              ):
            ema_cross_signal_3 = -1
        else: ema_cross_signal_3 = 0
        
        # Combine short and long term signals
        return ema_cross_signal_1 + ema_cross_signal_2 + ema_cross_signal_3