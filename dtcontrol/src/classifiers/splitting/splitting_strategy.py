from abc import ABC, abstractmethod

class SplittingStrategy(ABC):
    @abstractmethod
    def find_split(self, X_train, y, impurity_measure):
        """
        :param X_train: the training data
        :param y: the determinized labels
        :param impurity_measure: the impurity measure to determine the quality of a potential split
        :returns: a mask representing the split, as well as a split object
        """
        pass
