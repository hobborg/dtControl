import sys

import numpy as np

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class Entropy(ImpurityMeasure):
    def calculate_impurity(self, x, y, mask):
        left = y[mask]
        right = y[~mask]
        if len(left) == 0 or len(right) == 0:
            return sys.maxsize
        num_labels = len(y)
        return (len(left) / num_labels) * self.calculate_entropy(left) + \
               (len(right) / num_labels) * self.calculate_entropy(right)

    @staticmethod
    def calculate_entropy(y):
        num_labels = len(y)
        unique = np.unique(y)
        probabilities = [len(y[y == label]) / num_labels for label in unique]
        return sum(-prob * np.log2(prob) for prob in probabilities)
