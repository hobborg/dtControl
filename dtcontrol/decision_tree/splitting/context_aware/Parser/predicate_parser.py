import tkinter as tk
from tkinter import simpledialog
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

    def __init__(self):
        ROOT = tk.Tk()
        ROOT.withdraw()

    def get_predicate(self):

        """
        Predicate Parser for the user input.
        :variable user_input: String obtained from user.
        :returns: a sympy expression (to later use as predicate)
        """

        user_input = simpledialog.askstring(title="dtcontrol", prompt="Is there a predicate to start with?")

        # TODO: Catch edge cases

        relation_list = ["<=", ">=", "!=", "<", ">", "="]
        for sign in relation_list:
            if sign in user_input:
                foo = user_input.split(sign)
                left_formula = foo[0]
                right_formula = foo[1]
                expression = simplify(sympify(left_formula) - sympify(right_formula))
                variables = re.findall("x_(\d+)", user_input)
                try:
                    # return parse_latex(user_input)
                    return variables, expression, sign
                except:
                    raise Exception(
                        "Predicat can't be parsed.\nPlease try giving the predicat in a valid sympy format.")

# TESTING

# foo = PredicateParser().get_predicate()
# pprint(foo)
#
# vars = {}
# for i in range(1001):
#     vars["x_"+str(i)] = Symbol("x_"+str(i))
#     vars["y_" + str(i)] = Symbol("y_" + str(i))
# print(vars)
#
# foo1 = sympify("(x_1+32 )* x_2")
# print(foo1)
# print(expand(foo1))
