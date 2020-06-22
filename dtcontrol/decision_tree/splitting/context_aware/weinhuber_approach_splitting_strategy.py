from dtcontrol.decision_tree.splitting.context_aware.context_aware_splitting_strategy import \
    ContextAwareSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.predicate_parser import PredicateParser
import logging
import sympy as sp
import numpy as np
import re
from copy import deepcopy
from apted import APTED
from apted.helpers import Tree
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from itertools import product


class WeinhuberApproachSplittingStrategy(ContextAwareSplittingStrategy):
    first_run = True

    def __init__(self, user_given_splits=None, determinizer=LabelPowersetDeterminizer()):

        """
        :param user_given_splits: predicates/splits obtained by user to work with
        :param determinizer: determinizer
        """
        super().__init__()
        self.user_given_splits = PredicateParser.get_predicate() if user_given_splits is None else None
        self.determinizer = determinizer

        # Will be set inside decision_tree.py and later used inside self.get_parent_splits()
        self.root = None
        self.current_node = None

        self.logger = logging.getLogger("WeinhuberApproachSplittingStrategy_logger")
        self.logger.setLevel(logging.ERROR)

    def get_path_root_current(self, ancestor_range=0, current_node=None, path=[]):

        """
        Standard depth first search.
        (Default: starts from self.root)
        !!!!!!!! This function is always searching for self.current_node !!!!!!!!!

        :param ancestor_range: number of closest ancestor nodes to return
        :param current_node: current node being checked
        :param path: list containing ancestor path (from self.root to self.current_node)
        :returns: list of ancestor nodes from self.root to self.current_node (containing only the last ancestor_range ancestors)
        """

        if current_node is None:
            current_node = self.root

        path_copy = path.copy()
        path_copy.append(current_node)
        if self.current_node in current_node.children:
            for node in path:
                if node.split is None:
                    path_copy.remove(node)
            return path_copy[-ancestor_range:]
        elif not current_node.children:
            return None
        else:
            for node in current_node.children:
                result = self.get_path_root_current(ancestor_range=ancestor_range, current_node=node, path=path_copy)
                if result:
                    return result
            return None

    def tree_edit_distance(self, predicate1, predicate2):

        """
        Function to compute the tree edit distance between 2 predicates.
        :param predicate1: term attribute of a WeinhuberApproachSplit Object
        :param predicate2: term attribute of a WeinhuberApproachSplit Object
        :returns: Integer (tree edit distance between these 2 predicates)
        """

        def helper_formatting(tree):
            """
            Helper/Adapter function to transform tree format from sympy format to APTED format
            :param tree: term attribute of a WeinhuberApproachSplit Object
            :returns: String (formatted version of term in APTED format)

            e.g.
            Sympy format: Add(Mul(Integer(11), Symbol('x_1')), Mul(Integer(2), Symbol('x_2')), Integer(-11))
            APTED format: {Add{Mul{{Variable}{Symbol1}}Mul{{Variable}{Symbol2}}{Variable}}}
            """
            tree = sp.srepr(tree)

            # TODO: Cleanup this Regex battle
            formated_tree = re.sub("Integer\(.+?\)|Float\(.+?\)|Rational\(.+?\)", "{Variable}", tree)
            formated_tree = formated_tree.replace("(", "{").replace(")", "}").replace("{'x_", "").replace("'}", "").replace(
                ", ", "")
            formated_tree = "{" + re.sub("(Symbol\d+)", "{\\1}", formated_tree) + "}"
            return formated_tree

        tree1 = Tree.from_text(helper_formatting(predicate1))
        tree2 = Tree.from_text(helper_formatting(predicate2))

        # TERMINAL COMMAND: python -m apted -t tree1 tree2 -mv

        apted = APTED(tree1, tree2)
        ted = apted.compute_edit_distance()
        # mapping = apted.compute_edit_mapping()
        return ted

    def print_path_root_current(self, split_list):

        """
        Super simple debugging function to quickly visualize the ancestor path returned from self.get_path_root_current()
        :param split_list: ancestor path returned by get_path_root_current
        :returns: None (Just super simple visual representation for terminal)
        """

        print("\n----------------------------")
        if split_list:
            for i in split_list:
                print("Parent Split: ", i.split.print_dot())
                # self.get_tree_distance(i.split.predicate, None)

        else:
            print("No parent splits yet")
        print("----------------------------")

    def find_split(self, dataset, impurity_measure):

        """
        :param dataset: the subset of data at the current split
        :param impurity_measure: the impurity measure to determine the quality of a potential split
        :returns: a split object
        """

        # TODO: Think about incorporating tree edit distance into splitting strategy
        # (Safed for later)TREE EDIT USAGE CODE:
        # tmp = self.get_path_root_current()
        # self.print_path_root_current(tmp)
        #
        # predicate_1 = sp.sympify("-0.10073*x_0+0.00080492*x_1+0.5956*x_2-0.22309*x_3-0.96975")
        # predicate_2 = sp.sympify("-0.10073*x_0+0.00080492*x_1+0.5956*x_2-0.22309")
        # tmp = self.tree_edit_distance(predicate_1, predicate_2)

        x_numeric = dataset.get_numeric_x()
        if x_numeric.shape[1] == 0:
            return

        y = self.determinizer.determinize(dataset)
        if not self.user_given_splits:
            return

        if self.first_run:
            # Checking whether used variables in user_given_splits are actually represented in dataset
            splits_with_coefs = []
            for single_split in self.user_given_splits:
                if not single_split.check_valid_column_reference(x_numeric):
                    self.logger.warning("Aborting: one predicate uses an invalid column reference."
                                        "Invalid predicate: ", str(single_split))
                    return
            self.first_run = False

        """
        Iterating over every user given predicate/split and adjusting it to the current dataset,
        to achieve the lowest impurity possible with the user given predicate/split.
        All adjusted predicate/split objects will be stored inside a dict: 
        Key: split object   Value:Impurity of the split
        """

        # Same approach as in linear_classifier.py
        splits = {}
        for single_split in self.user_given_splits:
            # Checking if every column reference is in its Interval
            if single_split.check_data_in_column_interval(x_numeric):
                if not single_split.coef_interval:
                    split_copy = deepcopy(single_split)
                    split_copy.priority = self.priority
                    splits[split_copy] = impurity_measure.calculate_impurity(dataset, split_copy)
                else:
                    for label in np.unique(y):
                        # Creating the label mask (see linear classifier)
                        new_y = np.copy(y)
                        label_mask = (new_y == label)
                        new_y[label_mask] = 0 if single_split.relation == "=" else 1
                        new_y[~label_mask] = -1

                        """
                        Applying fit function for every possible combination of already fixed coefs
    
                        e.g.
                        Split: c_0*x_0+c_1*x_1+c_2*x_2+c_3*x_3+c_4 <= 0;c_1 in {1,2,3}; c_2 in {-1,-3}
    
                        -->         combinations = [[('c_1', 1), ('c_2', -3)], [('c_1', 1), ('c_2', -1)],
                                                    [('c_1', 2), ('c_2', -3)], [('c_1', 2), ('c_2', -1)],
                                                    [('c_1', 3), ('c_2', -3)], [('c_1', 3), ('c_2', -1)]]
    
                        --> The other coefs (c_0, c_3, c_4) still have to be determined by fit (curve_fit)
    
                        """

                        fixed_coefs = {}
                        # Checking if coef_interval is containing finite sets with fixed coefs
                        for coef in single_split.coef_interval:
                            if isinstance(single_split.coef_interval[coef], sp.FiniteSet):
                                fixed_coefs[coef] = list(single_split.coef_interval[coef].args)

                        if fixed_coefs:
                            # unzipping
                            coef, val = zip(*fixed_coefs.items())
                            # calculation all combinations and zipping back together
                            combinations = [list(zip(coef, nbr)) for nbr in product(*val)]
                        else:
                            combinations = [[]]

                        for comb in combinations:
                            split_copy = deepcopy(single_split)
                            split_copy.fit(comb, x_numeric, new_y)
                            split_copy.priority = self.priority
                            if split_copy.coef_assignment is not None:
                                splits[split_copy] = impurity_measure.calculate_impurity(dataset, split_copy)

        weinhuber_split = min(splits.keys(), key=splits.get) if splits else None
        return weinhuber_split
