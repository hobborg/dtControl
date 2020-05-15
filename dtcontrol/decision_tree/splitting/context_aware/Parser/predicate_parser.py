from sympy import *
from sympy.parsing.latex import parse_latex, LaTeXParsingError
import re


# Requirements:
# pip3 install antlr4-python3-runtime'<4.8'

# SAMPLE INPUTS:
# LatexInput: "\frac {1 + \sqrt {\a}} {\b}"
# SympyInput: "(10+x_1)*123*x_4 = 0"
#             "11*x_2-32 <= 0" "11*x_2-30.5 - sqrt(2) <= 0" "11*x_2-30- sqrt(2)**2 <= 0" "11*x_2-28.86 <= pi" "11*x_2-28.86 > pi"


class PredicateParser():

    def get_predicate(self):
        """
        Predicate Parser for the user input.
        :variable user_input: String obtained from file: input_predicates.txt
        :returns: a sympy expression (to later use as predicate)
        """

        with open("dtcontrol/decision_tree/splitting/context_aware/Parser/input_predicates.txt", "r") as file:
            predicates = [predicate.rstrip() for predicate in file]

        relation_list = ["<=", ">=", "!=", "<", ">", "="]
        output = []
        for single_predicate in predicates:
            for sign in relation_list:
                if sign in single_predicate:
                    split_pred = single_predicate.split(sign)
                    left_formula = simplify(sympify(split_pred[0]))
                    interval = self.get_interval(split_pred[1].strip())
                    variables = re.findall("x_(\d+)", split_pred[0])
                    output.append((variables, left_formula, sign, interval))
                    break
        return output

    def get_interval(self, user_input):
        """
        Predicate Parser for the interval result.
        :variable user_input: Interval as string
        :returns: a sympy expression (to later use as predicate)

        Option 1: user_input = $i
        --> Just use the value to obtain the best impurity

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
        --> Union of sets with ∪


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

        if user_input == "$i":
            return user_input

        interval_list = []

        user_input = user_input.split("∪")
        user_input = [x.strip() for x in user_input]
        for interval in user_input:
            # FINITE_INTERVAL
            if (interval[0] == "{") & (interval[-1] == "}"):
                members = interval[1:-1].split(",")
                interval_list.append(FiniteSet(*members))
                continue

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
        if len(interval_list) > 1:
            for item in interval_list:
                final_interval = Union(final_interval, item)

        return final_interval

# relation_list = ["<=", ">=", "!=", "<", ">", "="]
# output = []
# for single_predicate in predicates:
#     for sign in relation_list:
#         if sign in single_predicate:
#             split_pred = single_predicate.split(sign)
#             left_formula = split_pred[0]
#             right_formula = split_pred[1]
#             expression = simplify(sympify(left_formula) - sympify(right_formula))
#             variables = re.findall("x_(\d+)", single_predicate)
#             output.append((variables, expression, sign))
#             break
# return output
