from abc import ABC, abstractmethod
from dtcontrol.decision_tree.splitting.split import Split


class ContextAwareSplit(Split, ABC):
    """
    Represents an arbitrary split obtained by an user.
    Path of user input: dtcontrol/decision_tree/splitting/context_aware/input_predicates.txt
    Object is especially used inside weinhuber_approach_split.py
    """

    def __init__(self, variables, predicate, relation, interval, priority=None, hard_interval_boundary=True, offset=None):
        """
        e.g.:
            11*x_1 + 2*x_2 - 11 <= (0,1) ∪ [12, 15]

            self.variables              =       ['1', '2'] --> list of used x variables
            self.predicate              =       1*x_1 + 2*x_2 - 11 --> sympy expression
            self.relation               =       '<='
            self.interval               =       Union(Interval.open(0, 1), Interval(12, 15))
            self.hard_interval_boundary =       True
            self.offset                 =       0.5

        self.offset contains the offset of self.predicate in order to achieve the 'best' impurity.

        self.hard_interval_boundary is a boolean which gives information about the way to continue if self.offset
        doesn't fit inside the interval of self.interval.

        If self.hard_interval == True:
            self.offset is only allowed to be a value that fits inside self.interval. If all possible values for
            self.offset doesn't fit inside self.interval, then the whole split won't be used.
        If self.hard_interval == False:
            If all possible values for self.offset doesn't fit inside self.interval, then the split will be still used
            and therefore the interval will be ignored.


        For more information about the way the attributes: variables, predicate, relation or interval get
        parsed exactly, take a look inside the function parse_user_predicate() inside
        dtcontrol/decision_tree/splitting/context_aware/weinhuber_approach_splitting_strategy.py

        For more information about the way hard_interval_boundary behaves or offset is being computed, take a look inside the function
        calculate_best_result_for_split() inside
        dtcontrol/decision_tree/splitting/context_aware/weinhuber_approach_splitting_strategy.py

        """

        self.variables = variables
        self.predicate = predicate
        self.relation = relation
        self.interval = interval
        self.hard_interval_boundary = hard_interval_boundary
        self.offset = offset

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
