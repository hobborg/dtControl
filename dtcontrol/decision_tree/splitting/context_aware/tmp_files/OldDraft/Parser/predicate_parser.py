from sympy import *
import re
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_splitting_strategy import WeinhuberApproachSplit

class PredicateParser:
    """
    Requirements:
    pip3 install antlr4-python3-runtime'<4.8'
    sympy
    re
    """

    def get_predicate(self):
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

        with open("dtcontrol/decision_tree/splitting/context_aware/Parser/input_predicates.txt", "r") as file:
            predicates = [predicate.rstrip() for predicate in file]

        # Currently supported types of relations
        relation_list = ["<=", ">=", "!=", "<", ">", "="]

        # List containing all predicates parsed in tuple form
        output = []
        for single_predicate in predicates:
            for sign in relation_list:
                if sign in single_predicate:
                    split_pred = single_predicate.split(sign)
                    left_formula = simplify(sympify(split_pred[0]))

                    # Accessing the interval parser, since the intervals can also contain unions etc
                    interval = self.get_interval(split_pred[1].strip())

                    # Edge case in case interval is an empty interval
                    if interval == EmptySet:
                        break
                    variables = re.findall("x_(\d+)", split_pred[0])
                    output.append(WeinhuberApproachSplit(variables, left_formula, sign, interval))
                    break
        return output

    def get_interval(self, user_input):
        """
        Predicate Parser for the interval.
        :variable user_input: Interval as a string
        :returns: a sympy expression (to later use in self.interval of ContextAwareSplit objects)

        Option 1: user_input = $i
        --> self.offset of ContextAwareSplit will be the value to achieve the 'best' impurity

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
            return Interval(-oo, +oo)

        # appending all intervals into this list and later union all of them
        interval_list = []

        user_input = user_input.split("∪")
        user_input = [x.strip() for x in user_input]

        for interval in user_input:
            # finite intervals like {1,2,3}
            if (interval[0] == "{") & (interval[-1] == "}"):
                members = interval[1:-1].split(",")
                interval_list.append(FiniteSet(*members))
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
                    Interval(sympify(tmp[0]), sympify(tmp[1]), right_open=right_open, left_open=left_open))
            elif interval[-1] == "]":
                right_open = False
                tmp = interval[1:-1].split(",")
                interval_list.append(
                    Interval(sympify(tmp[0]), sympify(tmp[1]), right_open=right_open, left_open=left_open))

        final_interval = interval_list[0]

        # union with all other intervals
        if len(interval_list) > 1:
            for item in interval_list:
                final_interval = Union(final_interval, item)

        return final_interval
