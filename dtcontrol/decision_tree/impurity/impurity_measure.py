from abc import ABC, abstractmethod

class ImpurityMeasure(ABC):
    @abstractmethod
    def calculate_impurity(self, x, y, mask):
        """
        :param x: the training data at the current node
        :param y: the determinized labels
        :param mask: the mask representing the split
        :returns: the calculated impurity
        """
        pass
