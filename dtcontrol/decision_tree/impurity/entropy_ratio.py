import sys

import numpy as np

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class EntropyRatio(ImpurityMeasure):
    def calculate_impurity(self, dataset, y, split):
        split_entropy = self.calculate_split_entropy(dataset, y, split)
        if split_entropy == sys.maxsize:
            return sys.maxsize
        split_info = self.calculate_split_info(dataset, y, split)
        if split_info == 0:
            return sys.maxsize
        return split_entropy / split_info

    @staticmethod
    def calculate_split_entropy(dataset, y, split):
        entropy = 0
        for mask in split.get_masks(dataset):
            subset = y[mask]
            if len(subset) == 0:
                return sys.maxsize
            entropy += (len(subset) / len(y)) * EntropyRatio.calculate_entropy(subset)
        return entropy

    @staticmethod
    def calculate_entropy(y):
        num_labels = len(y)
        unique = np.unique(y)
        probabilities = [len(y[y == label]) / num_labels for label in unique]
        return sum(-prob * np.log2(prob) for prob in probabilities)

    @staticmethod
    def calculate_split_info(dataset, y, split):
        info = 0
        for mask in split.get_masks(dataset):
            subset = y[mask]
            if len(subset) == 0:
                return 0
            info -= (len(subset) / len(y)) * np.log2((len(subset) / len(y)))
        return info
