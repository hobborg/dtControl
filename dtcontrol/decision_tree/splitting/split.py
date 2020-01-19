from abc import ABC, abstractmethod

import numpy as np

class Split(ABC):
    @abstractmethod
    def predict(self, features):
        """
        Determines the child index of the split for one particular instance.
        :param features: the features of the instance
        :returns: the child index (0/1 for a binary split)
        """
        pass

    def split(self, dataset):
        """
        Splits the dataset into subsets.
        :param dataset: the dataset to be split
        :return: a list of the subsets
        """
        return [dataset.from_mask(mask) for mask in self.get_masks(dataset)]

    @abstractmethod
    def get_masks(self, dataset):
        """
        Returns the masks specifying this split.
        :param dataset: the dataset to be split
        :return: a list of the masks corresponding to each subset after the split
        """

    @abstractmethod
    def print_dot(self):
        pass

    @abstractmethod
    def print_c(self):
        pass

    @abstractmethod
    def print_vhdl(self):
        pass

class LinearSplit(ABC):  # TODO MJA: in eigene klasse stecken
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
