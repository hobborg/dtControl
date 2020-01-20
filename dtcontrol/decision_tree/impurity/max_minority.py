import numpy as np

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class MaxMinority(ImpurityMeasure):
    def calculate_impurity(self, dataset, y, split):
        return max([self.calculate_minority(y[mask]) for mask in split.get_masks(dataset)])

    @staticmethod
    def calculate_minority(y):
        label = np.bincount(y).argmax()
        return len(y[y != label])
