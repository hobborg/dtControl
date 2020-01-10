import numpy as np

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class MaxMinority(ImpurityMeasure):
    def calculate_impurity(self, x, y, mask):
        left = self.calculate_minority(y[mask])
        right = self.calculate_minority(y[~mask])
        return max(left, right)

    @staticmethod
    def calculate_minority(y):
        label = np.bincount(y).argmax()
        return len(y[y != label])
