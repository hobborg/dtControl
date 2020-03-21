import sys

import numpy as np

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class NondetEntropyRatio(ImpurityMeasure):
    def calculate_impurity(self, dataset, y, split):
        if any(len(y[mask]) == 0 for mask in split.get_masks(dataset)) or \
                len(split.get_masks(dataset)) == 1:
            return sys.maxsize

        split_entropy = self.calculate_split_entropy(dataset, y, split)
        split_info = self.calculate_split_info(dataset, y, split)
        return split_entropy / split_info
        # return split_entropy

    @staticmethod
    def calculate_split_entropy(dataset, y, split):
        entropy = 0
        for mask in split.get_masks(dataset):
            subset = y[mask]
            entropy += (len(subset) / len(y)) * NondetEntropyRatio.calculate_entropy(subset)
        assert entropy >= 0
        return entropy

    @staticmethod
    def calculate_entropy(y):
        flattened_labels = y.flatten()
        # remove -1 as we use it only as a filler
        flattened_labels = flattened_labels[flattened_labels != -1]
        label_counts = np.bincount(flattened_labels)[1:]
        if np.any(label_counts == len(y)):
            return 0
        label_counts = label_counts[label_counts != 0].astype('float')
        label_counts = label_counts / len(y)
        return sum(-p * np.log2(p) for p in label_counts)

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
