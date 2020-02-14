from abc import ABC, abstractmethod

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
    def print_dot(self, variables=None, category_names=None):
        pass

    @abstractmethod
    def print_c(self):
        pass

    @abstractmethod
    def print_vhdl(self):
        pass
