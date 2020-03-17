import sys

import numpy as np

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class ProbabilisticEntropy(ImpurityMeasure):
    def calculate_impurity(self, dataset, y, split):
        if len(split.get_masks(dataset)) == 1:
            return sys.maxsize
        impurity = 0
        for mask in split.get_masks(dataset):
            subset = y[mask, :]
            if len(subset) == 0:
                return sys.maxsize
            impurity += (len(subset) / len(y)) * self.calculate_prob_entropy(subset)
        return impurity

    @staticmethod
    def calculate_prob_entropy(y):
        means = np.mean(y, axis=0)
        means = means[means != 0]
        assert abs(sum(means) - 1) < 1e-10
        return sum(-prob * np.log2(prob) for prob in means)

    def get_oc1_name(self):
        return None
