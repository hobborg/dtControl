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


class WeinhuberApproachSplittingStrategy(ContextAwareSplittingStrategy):
    def __init__(self, predicate_structure_difference=5, predicate_dt_range=5, user_given_splits=None,
                 determinizer=LabelPowersetDeterminizer()):

        """
        :param fallback_strategy: splitting strategy to continue with, once weinhuber strategy doesn't work anymore
        :param user_given_splits: predicates/splits obtained by user to work with
        :param predicate_structure_difference: allowed difference in structure of predicate
        :param predicate_dt_range: range of distance to search in dt (being build)
        """
        super().__init__()
        self.user_given_splits = PredicateParser.get_predicate() if user_given_splits is None else user_given_splits
        self.predicate_structure_difference = predicate_structure_difference
        self.predicate_dt_range = predicate_dt_range
        self.determinizer = determinizer

        self.logger = logging.getLogger("WeinhuberApproachSplittingStrategy_logger")
        self.logger.setLevel(logging.ERROR)

    def get_parent_splits(self, current_node, parent_nbr, path=[]):

        """
        Standard depth first search.
        Always starting from self.root.
        Always searching for current_node.

        :param current_node: current node to search
        :param parent_nbr: number of parent nodes to return later
        :param path: list containing the path to the current node
        :returns: list of path from root to node, containing only the last parent_nbr parents
        """

        path_copy = path.copy()
        path_copy.append(current_node)
        if self.current_node in current_node.children:
            for node in path:
                if node.split is None:
                    path_copy.remove(node)
            return path_copy[-parent_nbr:]
        elif not current_node.children:
            return None
        else:
            for node in current_node.children:
                result = self.get_parent_splits(node, parent_nbr, path_copy)
                if result:
                    return result
            return None

    def tree_distance_format(self, tree):

        """
        Function to transform tree format from sympy format to APTED format
        e.g.
        Sympy format: Add(Mul(Integer(11), Symbol('x_1')), Mul(Integer(2), Symbol('x_2')), Integer(-11))
        APTED format: {Add{Mul{{Variable}{Symbol1}}Mul{{Variable}{Symbol2}}{Variable}}}

        :param tree: syntax tree of sympy expression
        :returns: formatted string of tree in APTED format
        """

        formated_tree = re.sub("Integer\(.+?\)|Float\(.+?\)|Rational\(.+?\)", "{Variable}", tree)
        formated_tree = formated_tree.replace("(", "{").replace(")", "}").replace("{'x_", "").replace("'}", "").replace(
            ", ", "")
        formated_tree = "{" + re.sub("(Symbol\d+)", "{\\1}", formated_tree) + "}"

        return formated_tree

    def get_tree_distance(self, predicate1, predicate2):
        tree1 = Tree.from_text(self.tree_distance_format(sp.srepr(predicate1)))
        tree2 = Tree.from_text(self.tree_distance_format(sp.srepr(predicate2)))
        # tree2 = Tree.from_text("{Add{Mul{{Variable}{Symbol2}}{Variable}}}")

        # TERMINAL COMMAND: python -m apted -t tree1 tree2 -mv

        apted = APTED(tree1, tree2)
        ted = apted.compute_edit_distance()
        mapping = apted.compute_edit_mapping()
        # print("Comparing: \nTree1: ",self.tree_distance_format(sp.srepr(predicate1)))
        # print("Tree2: {Add{Mul{{Variable}{Symbol2}}{Variable}}}")
        # print("Distance: ", ted)
        return ted

    def print_parent_nodes(self, split_list):

        """
        Super simple printing function for the return of get_parent_splits().
        :param split_list: list of path from self.root to self.current_node
        :returns: nothing. Just visual output for terminal
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

        # Checking whether used variables in user_given_splits are actually represented in dataset
        for single_split in self.user_given_splits:
            if not single_split.check_valid_column_reference(dataset):
                self.logger.warning("Aborting: one predicate uses an invalid column reference."
                                    "Invalid predicate: ", str(single_split))
                return

        """
        Iterating over every user given predicate/split and adjusting it to the current dataset,
        to achieve the lowest impurity possible with the user given predicate/split.
        All adjusted predicate/split objects will be stored inside a dict: 
        Key: split object   Value:Impurity of the split
        """

        splits = {}
        for single_split in self.user_given_splits:
            split_copy = deepcopy(single_split)
            split_copy.fit(dataset)

            if single_split.is_applicable(dataset):
                split_copy.priority = self.priority
                splits[split_copy] = impurity_measure.calculate_impurity(dataset, split_copy)

        weinhuber_split = min(splits.keys(), key=splits.get) if splits else None

        return weinhuber_split
