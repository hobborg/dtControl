from abc import ABC, abstractmethod

class Split(ABC):
    @abstractmethod
    def predict(self, features):
        """
        Determines if a single instance lies on the left or the right of this split
        :param features: the features of the instance
        :returns: -1 if the instance lies on the left and 1 if the instance lies on the right
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
