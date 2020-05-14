from abc import ABC, abstractmethod
from dtcontrol.decision_tree.splitting.split import Split
from sympy import *

class ContextAwareSplit(Split, ABC):
    """
    Represents an arbitrary split with starting split given by user
    """
    def __init__(self, variables, predicate, relation, interval):
        self.variables = variables
        self.predicate = predicate
        self.relation = relation
        self.interval = interval


    @abstractmethod
    def predict(self, features):
        """
        Determines the child index of the split for one particular instance.
        :param features: the features of the instance
        :returns: the child index (0/1 for a binary split)
        """
        pass

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
