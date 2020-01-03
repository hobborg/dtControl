from abc import ABC, abstractmethod

import numpy as np

class Split(ABC):
    @abstractmethod
    def predict(self, features):
        """
        Determines if a single instance lies on the left or the right of this split.
        :param features: the features of the instance
        :returns: True if the instance lies on the left and False if the instance lies on the right
        """
        pass

    @abstractmethod
    def print_dot(self):
        pass

    @abstractmethod
    def print_c(self):
        pass

    @abstractmethod
    def print_vhdl(self):
        pass

class AxisAlignedSplit(Split):
    """
    Represents an axis aligned split of the form x[i] <= b.
    """

    def __init__(self, feature, threshold):
        self.feature = feature
        self.threshold = threshold

    def predict(self, features):
        return features[:, self.feature][0] <= self.threshold

    def print_dot(self):
        return self.print_c()

    def print_c(self):
        return f'x[{self.feature}] <= {round(self.threshold, 6)}'

    def print_vhdl(self):
        return f'x{self.feature} <= {round(self.threshold, 6)}'

class LinearSplit(ABC):
    """
    Represents a linear split of the form wTx + b <= 0.
    """

    def __init__(self, coefficients, intercept):
        self.coefficients = coefficients
        self.intercept = intercept

    def predict(self, features):
        return np.dot(features, self.coefficients) + self.intercept <= 0

    def print_dot(self):
        return self.get_hyperplane_str(rounded=True, newlines=True)

    def print_c(self):
        return self.get_hyperplane_str()

    def print_vhdl(self):
        hyperplane = self.get_hyperplane_str()
        hyperplane.replace('[', '')
        hyperplane.replace(']', '')
        return hyperplane

    def get_hyperplane_str(self, rounded=False, newlines=False):
        line = []
        for i in range(len(self.coefficients)):
            line.append(f"{round(self.coefficients[i], 6) if rounded else self.coefficients[i]}*x[{i}]")
        line.append(f"{round(self.intercept, 6) if rounded else self.intercept}")
        joiner = "\\n+" if newlines else "+"
        hyperplane = joiner.join(line) + " <= 0"
        return hyperplane.replace('+-', '-')
