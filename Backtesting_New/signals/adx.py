

def eval_adx(strategy):
        if strategy.adx[-1] > strategy.adx_threshold:
            if strategy.plus_di[-1] > strategy.minus_di[-1]:
                return 1  # Strong upward trend
            else:
                return -1  # Strong downward trend
        else:
            return 0  # Weak trend