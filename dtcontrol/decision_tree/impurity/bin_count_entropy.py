import sys

import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# matplotlib.use('TkAgg')
from scipy.interpolate import CubicSpline

from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
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
    def scaling_function(x):
        return -x * np.log2(x)
        # return 1 - x**5
        # return 1 - 2.0238 * np.power(x, 3) - 0.916667 * np.power(x, 2) - 0.20714 * x + 0.101
        # return 1 - 2 * (1 - 1 / (x + 1))
        # return 1/x
        # return 1 - x * (x + .5)

    @staticmethod
    def calculate_avg_bincount(y):
        def plot(counts):
            plt.figure()
            plt.bar(range(1, len(counts) + 1), counts)
            plt.show()

        flattened_labels = y.flatten()
        # remove -1 as we use it only as a filler
        flattened_labels = flattened_labels[flattened_labels != -1]
        label_counts = np.bincount(flattened_labels)[1:]
        if np.any(label_counts == len(y)):
            return 0
        label_counts = label_counts[label_counts != 0].astype('float')
        label_counts = label_counts / len(y)
        # probs = label_counts / len(flattened_labels)
        scaled = AvgBinCount.scaling_function(label_counts)
        # return sum(scaled)
        return sum(scaled)

    def get_oc1_name(self):
        return None
