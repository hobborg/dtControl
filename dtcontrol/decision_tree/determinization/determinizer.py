from abc import ABC, abstractmethod

class Determinizer(ABC):
    def __init__(self):
        self.pre_determinized_labels = None
        assert not (self.is_pre_construction() and self.is_pre_split())

    @abstractmethod
    def determinize(self, dataset):
        """
        :param dataset: the dataset to be determinized
        :return: the determinized labels
        """
        pass

    @abstractmethod
    def is_pre_construction(self):
        """
        Returns true if this determinizer is only to be applied once before the whole tree building process.
        """
        pass

    @abstractmethod
    def is_pre_split(self):
        """
        Returns true if this determinizer should use the pre-split optimization (right now only MaxFreq).
        """
        pass
