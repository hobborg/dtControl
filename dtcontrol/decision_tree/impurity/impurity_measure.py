from abc import ABC, abstractmethod

class ImpurityMeasure(ABC):
    @abstractmethod
    def calculate_impurity(self, dataset, y, split):
        """
        :param dataset: the training data at the current node
        :param y: the determinized labels
        :param split: the split object
        :returns: the calculated impurity
        """
        pass
