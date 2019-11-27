from abc import ABC, abstractmethod

class Split(ABC):
    """
    Determines if a single instance lies on the left or the right of this split
    :param features: the features of the instance
    :returns: -1 if the instance lies on the left and 1 if the instance lies on the right
    """

    @abstractmethod
    def predict(self, features):
        pass
