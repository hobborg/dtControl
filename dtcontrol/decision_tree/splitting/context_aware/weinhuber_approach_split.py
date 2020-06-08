import warnings

from dtcontrol.decision_tree.splitting.split import Split
import numpy as np
import sympy as sp
import logging
from copy import deepcopy
from scipy.optimize import curve_fit
from scipy.optimize import OptimizeWarning


class WeinhuberApproachSplit(Split):
    """
    e.g.
    c1 * x_3 - c2 + x_4 - c3 <= 0; x_2 in {1,2,3}; c1 in (-inf, inf); c2 in {1,2,3}; c3 in {5, 10, 32, 40}

        column_interval     =       {x_1:(-Inf,Inf), x_2:{1,2,3}}                   --> Key: Sympy Symbol Value: Sympy Interval
        Every column reference without a specific defined Interval will be assigned to (-Inf, Inf)
        coef_interval       =       {c_1:(-Inf,Inf), c_2:{1,2,3}, c3:{5,10,32,40}}    --> Key: Sympy Symbol Value: Sympy Interval
        term                =       c_1 * x_3 - c_2 + x_4 - c_3                       --> sympy expression
        relation            =       '<='                                              --> String

        coef_assignment      =       {c_1:-8.23, c_2:2, c_3:40}                       --> Key: Sympy Symbol Value: Integer/Float
        coef_assignment will be determined later on after calling the fit function.
        It describes a specific assignment of all variables to a value inside their interval in order to achieve the lowest impurity.

    """

    def __init__(self, column_interval, coef_interval, term, relation, priority=1):
        self.priority = priority
        self.column_interval = column_interval
        self.coef_interval = coef_interval
        self.term = term
        self.relation = relation

        self.coef_assignment = None

        self.logger = logging.getLogger("WeinhuberApproachSplittingSplit_logger")
        self.logger.setLevel(logging.ERROR)

    def __repr__(self):
        return "WeinhuberApproachSplitObject:\ncolumn_interval: " + str(self.column_interval) + "\ncoef_interval: " + str(
            self.coef_interval) + "\nterm: " + str(self.term) + "\nrelation: " + str(self.relation) + "\ncoef_assignment: " + str(
            self.coef_assignment)

    def fit(self, given_coefs, x, y):
        """
        determines the best values for every coefficient(key) inside coef_interval(dict), within the range of their interval(value)
        :param given_coefs: Substitution list of tuples containing already determined coef values [(c_1, 2.5), ... ]
        :param x: feature columns of a dataset
        :param y: labels of a dataset
        """
        # TODO: Edge Case Handling

        if not self.coef_interval:
            return

        coefs_to_determine = list(set(self.coef_interval).difference(set([c for (c, _) in given_coefs])))
        inital_guess = [1 for coef in coefs_to_determine]

        # Values that will be calculated later on
        c = None
        self.y = None

        # adapter function representing the term (for curve_fit usage)
        def adapter_function(x, *args):
            out = []
            subs_list = deepcopy(given_coefs)

            for i in range(len(coefs_to_determine)):
                subs_list.append((coefs_to_determine[i], args[i]))

            for row_index in range(x.shape[0]):
                new_subs_list = deepcopy(subs_list)
                for column_index in range(len(x[row_index, :])):
                    new_subs_list.append(("x_" + str(column_index), x[row_index, column_index]))
                result = float(self.term.subs(new_subs_list).evalf())
                out.append(result)
            for index in range(len(out)):
                if not ((out[index] <= 0 and y[index] <= 0) or (out[index] > 0 and y[index] > 0)):
                    return np.array(out)
            self.y = out
            return np.array(out)

        # Run 1: Determining more suitable y
        with warnings.catch_warnings():
            warnings.simplefilter("error", OptimizeWarning)
            try:
                c, cov = curve_fit(adapter_function, x, y, inital_guess, absolute_sigma=True)
            except Exception:
                pass
        # Run 2: Determining coefs
        if self.y is not None:
            y = self.y
            with warnings.catch_warnings():
                warnings.simplefilter("error", OptimizeWarning)
                try:
                    c, cov = curve_fit(adapter_function, x, y, inital_guess, absolute_sigma=True)
                except Exception:
                    pass
        # Checking if curve fit was able to compute some coefs. (If not, coef_assignment will stay None)
        if c is not None:
            # Assigning these coefs to coef_assignment
            coef_assignment = {}
            for coef_index in range(len(c)):
                coef_assignment[coefs_to_determine[coef_index]] = c[coef_index]
            self.coef_assignment = coef_assignment

    def check_valid_column_reference(self, dataset):
        """
        :param dataset: the dataset to be split
        :return: boolean

        Checks every column referenciation index whether allowed or not.
            e.g.
            column_interval = {x_5:{1,2,3}}
            If the dataset got k columns with k > 5 --> True
            If the dataset only got k columns with k <= 5 --> False
        """

        allowed_var_index = dataset.get_numeric_x().shape[1] - 1
        for var in self.column_interval:
            x_index = int(str(var).split("x_")[1])
            if x_index > allowed_var_index:
                return False
            else:
                return True

    def is_applicable(self, dataset):
        """
        :param dataset: the dataset to be split
        :return: boolean

        Checks if the column intervals, contain all of the values inside a column.
            e.g.
            column_interval = {x_2:{1,3}} --> all values from the third column must be inside {1,3}
            :param dataset: the dataset to be split
            :return: boolean
        """

        x_numeric = dataset.get_numeric_x()
        for column_reference in self.column_interval:
            index = int(str(column_reference).split("x_")[1])
            interval = self.column_interval.get(column_reference)
            column = x_numeric[:, index]
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
        #
        # # fit() must be called before calling predict.
        # if self.coef_assignment is None:
        #     self.logger.warning("Aborting: coefficient assignment has to be determined first.")
        #     return

        subs_list = list(self.coef_assignment.items()) if self.coef_assignment else []

        # Iterating over every possible value and creating a substitution list
        for i in range(len(features[0, :])):
            subs_list.append(("x_" + str(i), features[0, i]))

        evaluated_predicate = self.term.subs(subs_list).evalf()
        if evaluated_predicate.free_symbols:
            return None

        # Checking the offset
        if self.relation == "<=":
            check = evaluated_predicate <= 0
        elif self.relation == ">=":
            check = evaluated_predicate >= 0
        elif self.relation == "!=":
            check = evaluated_predicate != 0
        elif self.relation == ">":
            check = evaluated_predicate > 0
        elif self.relation == "<":
            check = evaluated_predicate < 0
        else:
            check = evaluated_predicate == 0

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
        subs_list = list(self.coef_assignment.items()) if self.coef_assignment else []
        evaluated_predicate = self.term.subs(subs_list).evalf(5)
        return sp.pretty(evaluated_predicate).replace("+", "\\n+").replace("-", "\\n-") + "\\n" + self.relation + " 0"

    def print_c(self):
        return self.print_dot()

    def print_vhdl(self):
        return self.print_dot()
