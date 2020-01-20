from abc import ABC

import numpy as np

from dtcontrol.decision_tree.splitting.split import Split

class LinearSplit(Split, ABC):
    """
    Represents a linear split of the form wTx + b <= 0.
    """

    def __init__(self, coefficients, intercept):
        self.coefficients = coefficients
        self.intercept = intercept

    @staticmethod
    def map_numeric_coefficients_back(numeric_coefficients, dataset):
        dim = dataset.x.shape[1]
        new_coefficients = [0] * dim
        for i in range(numeric_coefficients):
            new_coefficients[dataset.map_numeric_feature_back(i)] = numeric_coefficients[i]
        return np.array(new_coefficients)

    def get_masks(self, dataset):
        mask = np.dot(dataset.x, self.coefficients) + self.intercept <= 0
        return [mask, ~mask]

    def predict(self, features):
        return 0 if np.dot(features, self.coefficients) + self.intercept <= 0 else 1

    def print_dot(self):
        return self.get_hyperplane_str(rounded=True, newlines=True)

    def print_c(self):
        return self.get_hyperplane_str()

    def print_vhdl(self):
        hyperplane = self.get_hyperplane_str()
        hyperplane.replace('[', '')
        hyperplane.replace(']', '')
        return hyperplane

    def get_hyperplane_str(self, rounded=False, newlines=False):  # TODO MJA: remove 0s
        line = []
        for i in range(len(self.coefficients)):
            line.append(f"{round(self.coefficients[i], 6) if rounded else self.coefficients[i]}*x[{i}]")
        line.append(f"{round(self.intercept, 6) if rounded else self.intercept}")
        joiner = "\\n+" if newlines else "+"
        hyperplane = joiner.join(line) + " <= 0"
        return hyperplane.replace('+-', '-')
