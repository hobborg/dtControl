import tkinter as tk
from tkinter import simpledialog
import numpy as np
import re


class PredicateParser():
    def __init__(self):
        ROOT = tk.Tk()
        ROOT.withdraw()



    def get_predicate(self):
        # TODO add help dialog
        # TODO parse the arguments for later usage inside find_split()
        # TODO Check whether the parsed argument makes sense

        user_input = simpledialog.askstring(title="dtcontrol", prompt="Is there a predicate to start with?")

        # Edge case if user just presses 'ok' without entering a valid predicate
        if user_input == "":
            return None

        return self.parse_input(user_input)

    def parse_input(self, user_input):
        # input string: 0*x_0+0*x_1+10*x_2+0*x_3-32 <= 0
        # TODO: allow input strings where not every x_ is given
        # return split coefficient tupel (classifier.coef[0] , classifier.intercept_[0]) -> ([ 0.  0. 10.  0.], [-32.])


        const_list = re.split("\*x_\d+| <= 0",user_input)[:-1]
        const_list = [float(x) for x in const_list]


        # !!!!!!!!!! WARNING: CURRENTLY JUST FOR LINEAR SPLITTING !!!!!!!!!!!!!!!!!!!!!
        # return Tupel (classifier.coef[0] , classifier.intercept_[0])
        if not const_list:
            return None
        else:
            print(np.array(const_list[:-1]), np.array(const_list[-1:]))
            return np.array(const_list[:-1]), np.array(const_list[-1:])

