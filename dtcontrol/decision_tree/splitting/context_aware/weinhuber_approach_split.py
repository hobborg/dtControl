import warnings

from dtcontrol.decision_tree.splitting.split import Split
import numpy as np
import sympy as sp
import logging
from copy import deepcopy
from scipy.optimize import curve_fit


class WeinhuberApproachSplit(Split):
    """
    e.g.
    c1 * x_3 - c2 + x_4 - c3 <= 0; x_2 in {1,2,3}; c1 in (-inf, inf); c2 in {1,2,3}; c3 in {5, 10, 32, 40}

        column_interval     =       {x_1:(-Inf,Inf), x_2:{1,2,3}}                     --> Key: Sympy Symbol Value: Sympy Interval
        Every column reference without a specific defined Interval will be assigned to (-Inf, Inf)
        coef_interval       =       {c_1:(-Inf,Inf), c_2:{1,2,3}, c3:{5,10,32,40}}    --> Key: Sympy Symbol Value: Sympy Interval
        term                =       c_1 * x_3 - c_2 + x_4 - c_3                       --> sympy expression
        relation            =       '<='                                              --> String

        coef_assignment     =       [(c_1,-8.23), (c_2,2), (c_3,40)]                  --> List containing substitution Tuples (Sympy Symbol, Value)
        It will be determined inside fit() and later used inside predict() (and get_masks())
        It describes a specific assignment of all variables to a value inside their interval in order to achieve the lowest impurity.
    """

    def __init__(self, column_interval, coef_interval, term, relation, priority=1):
        self.priority = priority
        self.column_interval = column_interval
        self.coef_interval = coef_interval
        self.term = term
        self.relation = relation

        self.coef_assignment = None

        # Helper variables only used inside fit()
        self.y = None
        self.coef_fit = None

        self.logger = logging.getLogger("WeinhuberApproachSplit_logger")
        self.logger.setLevel(logging.ERROR)

    def __repr__(self):
        return "WeinhuberApproachSplitObject:\ncolumn_interval: " + str(self.column_interval) + "\ncoef_interval: " + str(
            self.coef_interval) + "\nterm: " + str(self.term) + "\nrelation: " + str(self.relation) + "\ncoef_assignment: " + str(
            self.coef_assignment)

    def fit(self, fixed_coefs, x, y):
        """
        determines the best values for every coefficient(key) inside coef_interval(dict), within the range of their interval(value)
        :param fixed_coefs: Substitution list of tuples containing already determined coef values [(c_1, 2.5), ... ]
        :param x: feature columns of a dataset
        :param y: labels of a dataset
        """

        if not self.coef_interval:
            return

        # TODO: Think about whether this edge case should be covered or not
        # if self.coef_assignment is not None:
        #     self.logger.warning("Aborting: Split coef_assignment has already been determined.")
        #     return

        # Checking type & shape of arguments
        if not isinstance(x, np.ndarray) or not isinstance(y, np.ndarray) or x.shape[0] <= 0 or x.shape[0] != y.shape[0]:
            self.logger.warning("Aborting: invalid structure of the arguments x, y.")
            return

        coefs_to_determine = list(set(self.coef_interval))
        for (c_i, _) in fixed_coefs:
            if c_i not in self.coef_interval:
                # Checking if fixed_coefs are valid (every fixed coef must appear inside coef_interval)
                self.logger.warning("Aborting: invalid fixed_coefs member found. (Does not appear inside coef_interval)")
                return
            else:
                # Calculate coefs to determine with curve_fit
                coefs_to_determine.remove(c_i)

        if not coefs_to_determine:
            return

        inital_guess = [1 for coef in coefs_to_determine]

        # Values that will be calculated later on
        calculated_coefs = None
        self.y = None
        self.coef_fit = None

        # adapter function representing the term (for curve_fit usage)
        def adapter_function(x, *args):
            out = []
            subs_list = deepcopy(fixed_coefs)

            for i in range(len(coefs_to_determine)):
                subs_list.append((coefs_to_determine[i], args[i]))
            # TODO: Timer
            for row_index in range(x.shape[0]):
                new_subs_list = deepcopy(subs_list)
                for column_index in range(len(x[row_index, :])):
                    new_subs_list.append(("x_" + str(column_index), x[row_index, column_index]))
                result = float(self.term.subs(new_subs_list).evalf())
                out.append(result)
            ############
            for index in range(len(out)):
                # Checking the offset
                if self.relation == "<=":
                    if not ((out[index] <= 0 and y[index] <= 0) or (out[index] > 0 and y[index] > 0)):
                        return np.array(out)
                elif self.relation == ">=":
                    if not ((out[index] >= 0 and y[index] >= 0) or (out[index] < 0 and y[index] < 0)):
                        return np.array(out)
                elif self.relation == ">":
                    if not ((out[index] > 0 and y[index] > 0) or (out[index] <= 0 and y[index] <= 0)):
                        return np.array(out)
                elif self.relation == "<":
                    if not ((out[index] < 0 and y[index] < 0) or (out[index] >= 0 and y[index] >= 0)):
                        return np.array(out)
                else:
                    self.logger.warning("Aborting: invalid relation found.")
                    return

            self.y = out
            self.coef_fit = subs_list
            return np.array(out)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            try:
                calculated_coefs, cov = curve_fit(adapter_function, x, y, inital_guess)
            except Exception:
                # Even if the curve_fit fails, it may have still passed some usefull information to self.y or self.coef_fit.
                pass

        if self.y is not None and self.coef_fit is not None:
            self.coef_assignment = self.coef_fit
        elif calculated_coefs is not None:
            # Checking if curve fit was able to compute some coefs. (If not, coef_assignment will stay None)
            # Assigning these coefs to coef_assignment
            coef_assignment = []
            for coef_index in range(len(calculated_coefs)):
                coef_assignment.append((coefs_to_determine[coef_index], calculated_coefs[coef_index]))
            self.coef_assignment = coef_assignment
        # TODO: Maybe Logger Event? Failed to fit?

    def check_valid_column_reference(self, x):
        """
        :param x: the dataset to be split
        :return: boolean

        Checks every column referenciation index whether allowed or not.
            e.g.
            column_interval = {x_5:{1,2,3}}
            If the dataset got k columns with k > 5 --> True
            If the dataset got k columns with k <= 5 --> False
        """

        allowed_var_index = x.shape[1] - 1
        for var in self.column_interval:
            x_index = int(str(var).split("x_")[1])
            if x_index > allowed_var_index:
                return False
        return True

    def check_data_in_column_interval(self, x):
        """
        :param x: the dataset to be split
        :return: boolean

        Checks if the column intervals, contain all of the values inside a column.
            e.g.
            column_interval = {x_2:{1,3}} --> all values from the third column must be inside {1,3}
            :param dataset: the dataset to be split
            :return: boolean
        """

        for column_reference in self.column_interval:
            index = int(str(column_reference).split("x_")[1])
            interval = self.column_interval.get(column_reference)
            column = x[:, index]
            for val in column:
                if not interval.contains(val):
                    return False
        return True

    def predict(self, features):
        """
        Determines the child index of the split for one particular instance.
        :param features: the features of the instance
        :returns: the child index (0/1 for a binary split)
        """

        subs_list = deepcopy(self.coef_assignment) if self.coef_assignment else []

        # Iterating over every possible value and creating a substitution list
        for i in range(len(features[0, :])):
            subs_list.append(("x_" + str(i), features[0, i]))

        evaluated_predicate = self.term.subs(subs_list).evalf()
        if evaluated_predicate.free_symbols:
            return

        # Checking the offset
        if self.relation == "<=":
            check = evaluated_predicate <= 0
        elif self.relation == ">=":
            check = evaluated_predicate >= 0
        elif self.relation == ">":
            check = evaluated_predicate > 0
        elif self.relation == "<":
            check = evaluated_predicate < 0
        else:
            self.logger.warning("Aborting: invalid relation found.")
            return

        return 0 if check else 1

    def get_masks(self, dataset):
        """
        Returns the masks specifying this split.
        :param dataset: the dataset to be split
        :return: a list of the masks corresponding to each subset after the split
        """
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
        subs_list = self.coef_assignment if self.coef_assignment else []
        evaluated_predicate = sp.pretty(self.term.subs(subs_list).evalf(5))
        evaluated_predicate = evaluated_predicate.replace(" - ", "\\n-")
        return evaluated_predicate.replace(" + ", "\\n+") + " " + self.relation + " 0"

    def print_c(self):
        # TODO
        return self.print_dot()

    def print_vhdl(self):
        # TODO
        return self.print_dot()
