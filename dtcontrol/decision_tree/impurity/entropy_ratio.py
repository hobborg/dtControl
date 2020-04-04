import sys

import numpy as np

from dtcontrol.decision_tree.impurity.deterministic_impurity_measure import DeterministicImpurityMeasure

class EntropyRatio(DeterministicImpurityMeasure):
    def calculate_impurity(self, dataset, split):
        y = self.determinizer.determinize(dataset)
        if any(len(y[mask]) == 0 for mask in split.get_masks(dataset)) or \
                len(split.get_masks(dataset)) == 1:
            return sys.maxsize

        split_entropy = self.calculate_split_entropy(dataset, y, split)
        split_info = self.calculate_split_info(dataset, y, split)
        return split_entropy / split_info

    @staticmethod
    def calculate_split_entropy(dataset, y, split):
        entropy = 0
        for mask in split.get_masks(dataset):
            subset = y[mask]
            entropy += (len(subset) / len(y)) * EntropyRatio.calculate_entropy(subset)
        assert entropy >= 0
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
            info -= (len(subset) / len(y)) * np.log2((len(subset) / len(y)))
        assert info > 0
        return info

    def get_oc1_name(self):
        return None
