

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