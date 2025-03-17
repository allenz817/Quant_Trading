import numpy as np

class Math():
    @staticmethod
    def sigmoid(x):
        return 1 / (1 + np.exp(-x))
    
    @staticmethod
    def custom_sigmoid(x): # Scale sigmoid output to [-1, 1]
        return Math.sigmoid(x) * 2 - 1 