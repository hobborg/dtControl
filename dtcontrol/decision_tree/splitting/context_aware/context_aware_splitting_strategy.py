from abc import ABC, abstractmethod
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy
from sympy import *

class ContextAwareSplittingStrategy(SplittingStrategy, ABC):
    def __init__(self):
        # root contains a reference to the root node the current DT
        self.root = None
        self.current_Node = None

    @abstractmethod
    def find_split(self, dataset, impurity_measure):
        """
        :param dataset: the subset of data at the current split
        :param impurity_measure: the impurity measure to determine the quality of a potential split
        :returns: a split object
        """
        pass

    def set_root(self, root):
        self.root = root

    def set_current_Node(self, current_Node):
        self.current_Node = current_Node