import sys

import numpy as np

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class GiniIndex(ImpurityMeasure):
    def calculate_impurity(self, dataset, y, split):
        if len(split.get_masks(dataset)) == 1:
            return sys.maxsize
        impurity = 0
        for mask in split.get_masks(dataset):
            subset = y[mask]
            if len(subset) == 0:
                return sys.maxsize
            impurity += (len(subset) / len(y)) * self.calculate_gini_index(subset)
        return impurity

    @staticmethod
    def calculate_gini_index(y):
        num_labels = len(y)
        unique = np.unique(y)
        probabilities = [len(y[y == label]) / num_labels for label in unique]
        return 1 - sum(prob * prob for prob in probabilities)

    def get_oc1_name(self):
        return 'gini_index'
