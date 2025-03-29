

def cal_sup_res(strategy):
        # Calculate support and resistance levels
        support_resistance = {
            'sup': [],
            'res': []
        }
        # EMA
        if strategy.data.Close[-1] > strategy.ema5[-1]:
            support_resistance['sup'].append(strategy.ema5[-1])
        else:
            support_resistance['res'].append(strategy.ema5[-1])
        if strategy.data.Close[-1] > strategy.ema10[-1]:
            support_resistance['sup'].append(strategy.ema10[-1])
        else:
            support_resistance['res'].append(strategy.ema10[-1])
        if strategy.data.Close[-1] > strategy.ema20[-1]:
            support_resistance['sup'].append(strategy.ema20[-1])
        else:
            support_resistance['res'].append(strategy.ema20[-1])
        if strategy.data.Close[-1] > strategy.ema60[-1]:
            support_resistance['sup'].append(strategy.ema60[-1])
        else:
            support_resistance['res'].append(strategy.ema60[-1])
        # Bollinger Bands
        support_resistance['sup'].append(strategy.bb_lower[-1])
        support_resistance['res'].append(strategy.bb_upper[-1])
        if strategy.data.Close[-1] > strategy.bb_middle[-1]:
            support_resistance['sup'].append(strategy.bb_middle[-1]) 
        else:
            support_resistance['res'].append(strategy.bb_middle[-1])
            
        support_resistance['sup'] = sorted(support_resistance['sup'], reverse=True) # Sort in descending order
        support_resistance['res'] = sorted(support_resistance['res']) # Sort in ascending order
        
        return support_resistance