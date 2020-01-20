import sys

import numpy as np

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class MaxMinority(ImpurityMeasure):
    def calculate_impurity(self, dataset, y, split):
        minorities = []
        for mask in split.get_masks(dataset):
            subset = y[mask]
            if len(subset) == 0:
                return sys.maxsize
            minorities.append(self.calculate_minority(subset))
        return max(minorities)

    @staticmethod
    def calculate_minority(y):
        label = np.bincount(y).argmax()
        return len(y[y != label])
