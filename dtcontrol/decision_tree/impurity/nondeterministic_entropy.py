import numpy as np

from dtcontrol.decision_tree.impurity.nondeterministic_impurity_measure import NondeterministicImpurityMeasure
from dtcontrol.decision_tree.impurity.scaled_bincount import ScaledBincount

class NondeterministicEntropy(NondeterministicImpurityMeasure):

    def __init__(self):
        self.scaled_bincount = ScaledBincount(self.scaling_function)

    @staticmethod
    def scaling_function(x):
        return 1 + x * np.log2(x)

    def calculate_impurity(self, dataset, split):
        return self.scaled_bincount.calculate_impurity(dataset, split)
