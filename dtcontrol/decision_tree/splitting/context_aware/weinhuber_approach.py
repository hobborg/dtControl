from dtcontrol.decision_tree.splitting.context_aware.context_aware_split import ContextAwareSplit
from dtcontrol.decision_tree.splitting.context_aware.context_aware_splitting_strategy import \
    ContextAwareSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.Parser.predicate_parser import PredicateParser
import numpy as np
import sympy as sp
from copy import deepcopy


class WeinhuberApproachSplittingStrategy(ContextAwareSplittingStrategy):
    def __init__(self, start_predicate=True, alternative_splitting_strategy=None):
        super().__init__()
        self.start_predicate = start_predicate
        self.alternative_splitting_strategy = alternative_splitting_strategy

    def get_parent_nodes(self, currentNode, parent_nbr, path=[]):

        """
        :param currentNode: currentNode being looked at
        :param parent_nbr: number of parent nodes to return later
        :param path: list containing the path to the current node
        :returns: list of path from root to node, containing only the last parent_nbr parents
        """

        # Standard Depth first search
        path_copy = path.copy()
        path_copy.append(currentNode)
        if self.current_Node in currentNode.children:
            for node in path:
                if node.split is None:
                    path_copy.remove(node)
            return path_copy[-parent_nbr:]
        elif not currentNode.children:
            return None
        else:
            for node in currentNode.children:
                result = self.get_parent_nodes(node, parent_nbr, path_copy)
                if result:
                    return result
            return None

    def print_parents(self, split_list):

        # Printing the nearest k splits
        print("\n----------------------------")
        if split_list:
            for i in split_list:
                print("Parent Split: ", i.split.print_dot())
        else:
            print("No parent splits yet")
        print("----------------------------")

    def find_split(self, dataset, impurity_measure):

        """
        :param dataset: the subset of data at the current split
        :param impurity_measure: the impurity measure to determine the quality of a potential split
        :returns: a split object
        """

        # gets nearest k splits of self.current_node
        k = 20
        tmp = self.get_parent_nodes(self.root, k)
        # self.print_parents(tmp)
        splits = {}

        if self.start_predicate == True:
            predicate_list = PredicateParser().get_predicate()
            self.start_predicate = []
            for single_predicate in predicate_list:
                variables, predicate, relation, interval = single_predicate
                self.start_predicate.append(WeinhuberApproachSplit(variables, predicate, relation, interval))

            for single_split in self.start_predicate:
                single_split.result = self.calculate_best_result_for_predicate(dataset, single_split, impurity_measure)
                splits[single_split] = impurity_measure.calculate_impurity(dataset, single_split)

            if not splits:
                return None
            return min(splits.keys(), key=splits.get)

        #### Begin of alternative splitting strategy
        if self.alternative_splitting_strategy:
            return self.alternative_splitting_strategy.find_split(dataset, impurity_measure)

    def calculate_best_result_for_predicate(self, dataset, split, impurity_measure):
        x_numeric = dataset.get_numeric_x()
        possible_values_inside_interval = {}
        for i in range(x_numeric.shape[0]):
            subs_list = []
            features = x_numeric[i, :]
            copy_split = deepcopy(split)
            for k in range(len(features)):
                subs_list.append(("x_" + str(k), features[k]))
            tmp_result = copy_split.predicate.subs(subs_list)
            copy_split.result = tmp_result.evalf()
            possible_values_inside_interval[copy_split.result] = impurity_measure.calculate_impurity(dataset, copy_split)

        return min(possible_values_inside_interval.keys(), key=possible_values_inside_interval.get)


class WeinhuberApproachSplit(ContextAwareSplit):

    def predict(self, features):
        subs_list = []

        for i in range(len(features[0, :])):
            subs_list.append(("x_" + str(i), features[0, i]))
        result = self.predicate.subs(subs_list)
        result = result.evalf()
        if self.relation == "<=":
            check = result <= self.result
        elif self.relation == ">=":
            check = result >= self.result
        elif self.relation == "!=":
            check = result != self.result
        elif self.relation == ">":
            check = result > self.result
        elif self.relation == "<":
            check = result < self.result
        else:
            check = result == self.result

        if check:
            return 0
        else:
            return 1

    def get_masks(self, dataset):
        data = dataset.get_numeric_x()
        mask = []
        for i in range(np.shape(dataset.get_numeric_x())[0]):
            tmp1 = self.predict(np.array([data[i, :]]))
            if tmp1 == 0:
                mask.append(True)
            else:
                mask.append(False)
        mask = np.array(mask)
        return [mask, ~mask]

    def print_dot(self, variables=None, category_names=None):
        return sp.pretty(self.predicate) + " " + self.relation + " " + str(self.result)

    def print_c(self):
        return self.print_dot()

    def print_vhdl(self):
        return self.print_dot()
