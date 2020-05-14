from dtcontrol.decision_tree.splitting.context_aware.context_aware_split import ContextAwareSplit
from dtcontrol.decision_tree.splitting.context_aware.context_aware_splitting_strategy import \
    ContextAwareSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.Parser.predicate_parser import PredicateParser
import numpy as np
import sympy as sp


class WeinhuberApproachSplittingStrategy(ContextAwareSplittingStrategy):
    def __init__(self, start_predicate=-1, alternative_splitting_strategy=None):
        super().__init__()
        self.start_predicate = start_predicate
        self.alternative_splitting_strategy = alternative_splitting_strategy

    def get_parent_nodes(self, currentNode, parent_nbr, path=[]):

        """
        :param currentNode: currentNode beeing looked at
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

        # path.append(currentNode)
        # if currentNode == self.current_Node:
        #     for node in path:
        #         if node.split is None:
        #             path.remove(node)
        #     return path[-parent_nbr:]
        # elif not currentNode.children:
        #     return None
        # else:
        #     for node in currentNode.children:
        #         result = self.get_parent_nodes(node, parent_nbr, path)
        #         if result:
        #             return result
        #     return None

    def find_split(self, dataset, impurity_measure):

        """
        :param dataset: the subset of data at the current split
        :param impurity_measure: the impurity measure to determine the quality of a potential split
        :returns: a split object
        """

        tmp = self.get_parent_nodes(self.root, 20)
        print("#########")
        if tmp:
            for i in tmp:
                print(i.split.print_dot())
        print("#########")

        if self.start_predicate == -1:
            variables, predicate, relation = PredicateParser().get_predicate()
            self.start_predicate = WeinhuberApproachSplit(variables, predicate, relation)
            print("RETURN VALUE: ", self.start_predicate.print_dot())
            return self.start_predicate

        #### Begin of alternative splitting strategy
        if self.alternative_splitting_strategy:
            print("RETURN VALUE: ",
                  self.alternative_splitting_strategy.find_split(dataset, impurity_measure).print_dot())
            return self.alternative_splitting_strategy.find_split(dataset, impurity_measure)


class WeinhuberApproachSplit(ContextAwareSplit):

    def predict(self, features):
        subs_list = []

        for i in range(len(features[0, :])):
            subs_list.append(("x_" + str(i), features[0, i]))
        result = self.predicate.subs(subs_list)

        if self.relation == "<=":
            check = result <= 0
        elif self.relation == ">=":
            check = result >= 0
        elif self.relation == "!=":
            check = result != 0
        elif self.relation == ">":
            check = result > 0
        elif self.relation == "<":
            check = result < 0
        else:
            check = result == 0

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
        return sp.pretty(self.predicate) + " " + self.relation + " " + "0"

    def print_c(self):
        return self.print_dot()

    def print_vhdl(self):
        return self.print_dot()

# TODO: Display pow
# expr = "x_1**2"
# sp.pprint(sp.sympify(expr))
