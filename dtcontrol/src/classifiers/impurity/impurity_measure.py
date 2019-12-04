from abc import ABC, abstractmethod

class ImpurityMeasure(ABC):
    @abstractmethod
    def calculate_impurity(self, y, mask):
        """
        :param y: the determinized labels
        :param mask: the mask representing the split
        :returns: the calculated impurity
        """
        pass
