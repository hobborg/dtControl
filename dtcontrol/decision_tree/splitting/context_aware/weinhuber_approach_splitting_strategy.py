from dtcontrol.decision_tree.splitting.context_aware.context_aware_splitting_strategy import \
    ContextAwareSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit

import sympy as sp
import re
from copy import deepcopy


class WeinhuberApproachSplittingStrategy(ContextAwareSplittingStrategy):
    def __init__(self, predicate_structure_difference=5, predicate_dt_range=5, base_prio=None, fallback_prio=None,
                 user_given_splits=None, fallback_strategy=None):

        """
        :param fallback_strategy: splitting strategy to continue with, once weinhuber strategy doesn't work anymore
        :param user_given_splits: predicates/splits obtained by user to work with
        :param predicate_structure_difference: allowed difference in structure of predicate
        :param predicate_dt_range: range of distance to search in dt (being build)
        """
        super().__init__()

        self.fallback_strategy = fallback_strategy
        if user_given_splits is None:
            self.user_given_splits = self.parse_user_predicate()
        else:
            self.user_given_splits = user_given_splits
        self.base_prio = base_prio
        self.fallback_prio = fallback_prio
        self.predicate_structure_difference = predicate_structure_difference
        self.predicate_dt_range = predicate_dt_range

    def get_parent_nodes(self, current_node, parent_nbr, path=[]):

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
                result = self.get_parent_nodes(node, parent_nbr, path_copy)
                if result:
                    return result
            return None

    def print_parent_nodes(self, split_list):

        """
        Super simple printing function for the result of get_parent_nodes().
        :param split_list: list of path from self.root to self.current_node
        :returns: nothing. Just visual output for terminal
        """

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
        # self.print_parent_nodes(self.get_parent_nodes(self.root, k))

        """
        Iterating over every user given predicate/split and adjusting it to the current dataset,
        to achieve the 'best' impurity possible with the user given predicate/split.
        All adjusted predicate/split objects will be stored inside the dict: splits with 
        Key: split object   Value:Impurity of the split
        """

        splits = {}
        # Getting the 'best' possible split with user predicate/split
        for single_split in self.user_given_splits:
            split_copy = deepcopy(single_split)
            split_copy.result = self.calculate_best_result_for_split(dataset, split_copy, impurity_measure).evalf(6)
            splits[split_copy] = impurity_measure.calculate_impurity(dataset, split_copy)

        weinhuber_split = min(splits.keys(), key=splits.get)

        fallback_splits = {}
        # Getting the 'best' possible splits of fallback strategy
        for single_fallback_strat in self.fallback_strategy:
            split = single_fallback_strat.find_split(dataset, impurity_measure)
            fallback_splits[split] = impurity_measure.calculate_impurity(dataset, split)

        fallback_split = min(fallback_splits.keys(), key=splits.get)

        """
        Calculating return split with this rating formula based on priority.
        Formula:
                                    ,-
                                    ⎮ 0                             Prio_A = 1
        New_Impurity_A(Imp_A) =    -⎮ max_int                       Prio_A = 0
                                    ⎮ Imp_A - (Imp_A * Prio_A)      0 < Prio_A < 1 
                                    `-
                                    
        If base_prio == None && fallback_prio == None 
        return split with lowest impurity
        """

        # No priority given. Return the split (from weinhuber_split or fallback) with the lowest impurity
        if ((self.base_prio is None) and (self.fallback_prio is None)) or (
                (self.base_prio == 1) and (self.fallback_prio == 1)):
            return weinhuber_split if splits[weinhuber_split] <= fallback_splits[fallback_split] else fallback_split

        # edge case handling
        if (
                self.base_prio == 0 and self.fallback_prio == 0) or self.base_prio > 1 or self.fallback_prio > 1 or self.base_prio < 0 or self.fallback_prio < 0:
            return None

        if self.base_prio == 1:
            return weinhuber_split
        elif self.base_prio == 0:
            return fallback_split
        else:
            weinhuber_impurity = splits[weinhuber_split] - (splits[weinhuber_split] * self.base_prio)
            fallback_impurity = fallback_splits[fallback_split] - (fallback_splits[fallback_split] * self.fallback_prio)
            if weinhuber_impurity <= fallback_impurity:
                return weinhuber_split
            else:
                return fallback_split

    def calculate_best_result_for_split(self, dataset, split, impurity_measure):

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
            copy_split.result = copy_split.predicate.subs(subs_list).evalf(6)

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

    def parse_user_predicate(self):

        """
        Predicate parser for user input obtained from
        dtcontrol/decision_tree/splitting/context_aware/Parser/input_predicates.txt
        :returns: list with tuples of structure (variables, predicate, relation, interval)

        e.g.:
            11*x_1 + 2*x_2 - 11 <= (0,1) ∪ [12, 15]

            variables              =       ['1', '2'] --> list of used x variables
            predicate              =       1*x_1 + 2*x_2 - 11 --> sympy expression
            relation               =       '<='
            interval               =       Union(Interval.open(0, 1), Interval(12, 15))

        """

        with open("dtcontrol/decision_tree/splitting/context_aware/input_predicates.txt", "r") as file:
            predicates = [predicate.rstrip() for predicate in file]

        # Currently supported types of relations
        relation_list = ["<=", ">=", "!=", "<", ">", "="]

        # List containing all predicates parsed in tuple form
        output = []
        for single_predicate in predicates:
            for sign in relation_list:
                if sign in single_predicate:
                    split_pred = single_predicate.split(sign)
                    left_formula = sp.simplify(sp.sympify(split_pred[0]))

                    # Accessing the interval parser, since the intervals can also contain unions etc
                    interval = self.parse_user_interval(split_pred[1].strip())

                    # Edge case in case interval is an empty interval
                    if interval == sp.EmptySet:
                        break
                    variables = re.findall("x_(\d+)", split_pred[0])
                    output.append(WeinhuberApproachSplit(variables, left_formula, sign, interval))
                    break
        return output

    def parse_user_interval(self, user_input):
        """
        Predicate Parser for the interval.
        :variable user_input: Interval as a string
        :returns: a sympy expression (to later use in self.interval of ContextAwareSplit objects)

        Option 1: user_input = $i
        --> self.result of ContextAwareSplit will be the value to achieve the 'best' impurity

        Option 2: user_input is an interval
        Option 2.1: user_input = [a,b]
        --> Interval with closed boundary --> {x | a <= x <= b}
        Option 2.2: user_input = (a,b)
        --> Interval with open boundary --> {x | a < x < b}
        Option 2.3: user_input = (a.b]
        Option 2.4: user_input = [a,b)

        Option 3: user_input = {1,2,3,4,5}
        --> Finite set

        Option 4: user_input = [0,1) ∪ (8,9) ∪ [-oo, 1)
        --> Union of intervals


        Grammar G for an user given interval:

        G = (V, Σ, P, predicate)
        V = {predicate, combination, interval, real_interval, bracket_left, bracket_right, number, finite_interval, number_finit, num}
        Σ = {$i, (, [, ), ], R, +oo, -oo, , ∪}
        P:
        PREDICATE       -->     $i | COMBINATION
        COMBINATION     -->     INTERVAL | INTERVAL ∪ COMBINATION
        INTERVAL        -->     REAL_INTERVAL | FINITE_INTERVAL
        REAL_INTERVAL   -->     BRACKET_LEFT NUMBER , NUMBER BRACKET_RIGHT
        BRACKET_LEFT    -->     ( | [
        BRACKET_RIGHT   -->     ) | ]
        NUMBER          -->     {x | x ∊ R} | +oo | -oo
        FINITE_INTERVAL -->     {NUMBER_FINITE NUM}
        NUMBER_FINITE   -->     {x | x ∊ R}
        NUM             -->     ,NUMBER_FINITE | ,NUMBER_FINITE NUM

        """

        if user_input == '$i':
            return sp.Interval(sp.sympify("-oo"), sp.sympify("+oo"))

        # appending all intervals into this list and later union all of them
        interval_list = []

        user_input = user_input.split("∪")
        user_input = [x.strip() for x in user_input]

        for interval in user_input:
            # finite intervals like {1,2,3}
            if (interval[0] == "{") & (interval[-1] == "}"):
                members = interval[1:-1].split(",")
                interval_list.append(sp.FiniteSet(*members))
                continue

            # normal intervals
            if interval[0] == "(":
                left_open = True
            elif interval[0] == "[":
                left_open = False

            if interval[-1] == ")":
                right_open = True
                tmp = interval[1:-1].split(",")
                interval_list.append(
                    sp.Interval(sp.sympify(tmp[0]), sp.sympify(tmp[1]), right_open=right_open, left_open=left_open))
            elif interval[-1] == "]":
                right_open = False
                tmp = interval[1:-1].split(",")
                interval_list.append(
                    sp.Interval(sp.sympify(tmp[0]), sp.sympify(tmp[1]), right_open=right_open, left_open=left_open))

        final_interval = interval_list[0]

        # union with all other intervals
        if len(interval_list) > 1:
            for item in interval_list:
                final_interval = sp.Union(final_interval, item)

        return final_interval
