from abc import ABC, abstractmethod
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy


class ContextAwareSplittingStrategy(SplittingStrategy, ABC):
    """
    Represents a splitting strategy especially used inside weinhuber_approach.py
    (dtcontrol/decision_tree/splitting/context_aware/weinhuber_approach.py)

    """

    def __init__(self):
        """
        self.root contains a reference to the root node of the current DT to access the DT while it is being build
        self.current_node contains a reference to the current_node which is beeing
        """
        self.root = None
        self.current_node = None

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
        self.current_node = current_Node
