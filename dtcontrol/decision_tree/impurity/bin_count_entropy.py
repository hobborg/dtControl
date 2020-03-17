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
        label_counts = np.bincount(flattened_labels)[1:]
        if np.any(label_counts == len(y)):
            return 0
        label_counts = label_counts[label_counts != 0].astype('float')
        label_counts /= np.sum(label_counts)  # TODO MJA: with this directly or entropy
        # return 1 / np.mean(label_counts)
        return sum(-prob * np.log2(prob) for prob in label_counts)

        # label_counts *= label_counts + 0.5
        # order = np.argsort(label_counts)
        # total = len(label_counts) * (len(label_counts) + 1) / 2
        # weighted = np.array([(i / total) * label_counts[order[i]] for i in range(len(label_counts))])
        # return 1 / np.mean(weighted)

        # return 1 / np.sum(label_counts[label_counts != 0] ** 2)

        # return 1 / np.mean(label_counts ** 6)

        # label_counts *= label_counts + 0.5
        # label_counts *= label_counts + 0.5
        # return 1 / np.mean(label_counts)

    @staticmethod
    def calculate_entropy(y):
        num_labels = len(y)
        unique = np.unique(y)
        probabilities = [len(y[y == label]) / num_labels for label in unique]
        return sum(-prob * np.log2(prob) for prob in probabilities)

    def get_oc1_name(self):
        return None
