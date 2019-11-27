from abc import ABC, abstractmethod

class SplittingStrategy(ABC):
    """
    :param X_train: the training data
    :param y: the (potentially determinized) labels
    :returns: a mask representing the split, as well as a split object
    """

    @abstractmethod
    def find_split(self, X_train, y):
        pass
