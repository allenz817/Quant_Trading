from backtesting.lib import crossover

def eval_stoch(self):
        # Stochastic Oscillator
        if crossover(self.stoch_k, self.stoch_d) and self.stoch_k[-1] < self.stoch_lower_bound:
            return 1
        elif crossover(self.stoch_d, self.stoch_k) and self.stoch_k[-1] > self.stoch_upper_bound:
            return -1
        else:
            return 0