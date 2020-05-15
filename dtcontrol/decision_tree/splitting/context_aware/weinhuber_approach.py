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

    def get_parent_nodes(self, current_node, parent_nbr, path=[]):

        """
        :param current_node: current node to search
        :param parent_nbr: number of parent nodes to return later
        :param path: list containing the path to the current node
        :returns: list of path from root to node, containing only the last parent_nbr parents
        """

        # standard depth first search
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
        self.print_parents(tmp)
        splits = {}

        if self.start_predicate == True:
            predicate_list = PredicateParser().get_predicate()
            self.start_predicate = []

            # Adding all the predicates from input_predicates.txt to the list: self.start_predicate
            for single_predicate in predicate_list:
                variables, predicate, relation, interval = single_predicate
                self.start_predicate.append(WeinhuberApproachSplit(variables, predicate, relation, interval))

            # Adding the result to all predicates of the list: self.start_predicate
            for single_split in self.start_predicate:
                single_split.result = self.calculate_best_result_for_predicate(dataset, single_split, impurity_measure)

                # Adding all these predicates from self.start_predicate to a dict with:
                # Key:Splitobject   Value:Impurity of the split
                splits[single_split] = impurity_measure.calculate_impurity(dataset, single_split)

            # Edge case no start_predicates --> no split objects inside splits dict
            if not splits:
                return None

            # Returning the split with the lowest impurity
            return min(splits.keys(), key=splits.get)

        #### Begin of alternative splitting strategy
        if self.alternative_splitting_strategy:
            return self.alternative_splitting_strategy.find_split(dataset, impurity_measure)

    def calculate_best_result_for_predicate(self, dataset, split, impurity_measure):

        """
        :param dataset: the subset of data at the current split
        :param split: split to compute the best result for
        :param impurity_measure: the impurity measure to determine the quality of a potential split
        :returns: best value for split.result
        """

        x_numeric = dataset.get_numeric_x()
        possible_values_inside_interval = {}
        possible_values_outside_interval = {}

        # iterating over every row from dataset
        for i in range(x_numeric.shape[0]):
            subs_list = []
            features = x_numeric[i, :]
            copy_split = deepcopy(split)
            for k in range(len(features)):
                subs_list.append(("x_" + str(k), features[k]))

            # calculating the result for that specific row
            tmp_result = copy_split.predicate.subs(subs_list)
            copy_split.result = tmp_result.evalf()

            # evaluating where to store this split object (for more information look at documentation of hard_interval_boundary)
            # Key: result   Value: Impurity of that result
            if copy_split.interval.contains(copy_split.result):
                possible_values_inside_interval[copy_split.result] = impurity_measure.calculate_impurity(dataset,
                                                                                                         copy_split)
            else:
                possible_values_outside_interval[copy_split.result] = impurity_measure.calculate_impurity(dataset,
                                                                                                          copy_split)

            # return result with (best) result with result inside the interval
            if possible_values_inside_interval:
                return min(possible_values_inside_interval.keys(), key=possible_values_inside_interval.get)
            else:
                # If no possible result fits inside the interval (for more information look at documentation of hard_interval_boundary)
                if copy_split.hard_interval_boundary:
                    supremum = copy_split.interval.sup
                    infimum = copy_split.interval.inf

                    # Important note: (-oo,+oo) would be impossible at this place --> only one infinity sign would reach this state
                    if supremum == sp.sympify("+oo"):
                        return infimum
                    elif infimum == sp.sympify("-oo"):
                        return supremum
                    else:
                        return (infimum + supremum) / 2
                else:
                    return min(possible_values_outside_interval.keys(), key=possible_values_outside_interval.get)


class WeinhuberApproachSplit(ContextAwareSplit):

    def predict(self, features):
        subs_list = []

        # Iterating over every possible value and creating a substitution list
        for i in range(len(features[0, :])):
            subs_list.append(("x_" + str(i), features[0, i]))
        result = self.predicate.subs(subs_list)
        result = result.evalf()

        # Checking the result
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

        # Using the predict function and iterating over row
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
