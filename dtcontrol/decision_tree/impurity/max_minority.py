import sys

import numpy as np

from dtcontrol.decision_tree.impurity.deterministic_impurity_measure import DeterministicImpurityMeasure

class MaxMinority(DeterministicImpurityMeasure):
    def calculate_impurity(self, dataset, split):
        if len(split.get_masks(dataset)) == 1:
            return sys.maxsize
        minorities = []
        for mask in split.get_masks(dataset):
            subset_labels = self.determinizer.determinize(dataset.from_mask_optimized(mask))
            if len(subset_labels) == 0:
                return sys.maxsize
            minorities.append(self.calculate_minority(subset_labels))
        return max(minorities)

    @staticmethod
    def calculate_minority(y):
        label = np.bincount(y).argmax()
        return len(y[y != label])

    def get_oc1_name(self):
        return 'maxminority'
