import sys

import numpy as np

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class AvgBinCount(ImpurityMeasure):
    def calculate_impurity(self, dataset, y, split):
        if len(split.get_masks(dataset)) == 1:
            return sys.maxsize
        impurity = 0
        for mask in split.get_masks(dataset):
            subset = y[mask, :]
            if len(subset) == 0:
                return sys.maxsize
            impurity += (len(subset) / len(y)) * self.calculate_avg_bincount(subset)
        return impurity

    @staticmethod
    def calculate_avg_bincount(y):
        flattened_labels = y.flatten()
        # remove -1 as we use it only as a filler
        flattened_labels = flattened_labels[flattened_labels != -1]
        label_counts = np.bincount(flattened_labels)[1:].astype('float')
        label_counts /= len(y)
        if np.any(label_counts == 1):
            return 0
        return 1 / np.mean(label_counts)

    def get_oc1_name(self):
        return None
