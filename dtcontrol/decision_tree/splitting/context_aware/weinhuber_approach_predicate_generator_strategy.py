from dtcontrol.decision_tree.splitting.context_aware.context_aware_splitting_strategy import \
    ContextAwareSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.predicate_parser import PredicateParser
from copy import deepcopy
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from itertools import product
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_exceptions import WeinhuberStrategyException
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_logger import WeinhuberApproachLogger
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplit
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from sklearn.linear_model import LogisticRegression
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_splitting_strategy import WeinhuberApproachSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit
import sympy as sp
from dtcontrol.decision_tree.splitting.linear_split import LinearSplit


class WeinhuberApproachPredicateGeneratorStrategy(ContextAwareSplittingStrategy):

    def __init__(self, domain_knowledge=None, determinizer=LabelPowersetDeterminizer(), debug=False):
        super().__init__()
        self.domain_knowledge = PredicateParser.get_predicate(
            input_file_path="dtcontrol/decision_tree/splitting/context_aware/input_data/input_domain_knowledge.txt",
            debug=debug) if domain_knowledge is None else domain_knowledge
        self.determinizer = determinizer
        self.root = None
        self.current_node = None
        self.first_run = True

        # logger
        self.logger = WeinhuberApproachLogger("WeinhuberApproachPredicateGenerator_logger", debug)

    def find_split(self, dataset, impurity_measure):

        if self.first_run:
            new_domain_knowledge = []
            term_collection = []
            for formula in self.domain_knowledge:
                fixed_coefs = {}
                # Checking if domain knowledge is containing finite sets with fixed coefs
                for coef in formula.coef_interval:
                    if isinstance(formula.coef_interval[coef], sp.FiniteSet):
                        fixed_coefs[coef] = list(formula.coef_interval[coef].args)

                # Creating all combinations
                if fixed_coefs:
                    # unzipping
                    coef, val = zip(*fixed_coefs.items())
                    # calculation all combinations and zipping back together
                    combinations = [list(zip(coef, nbr)) for nbr in product(*val)]

                    for comb in combinations:
                        formula_copy = deepcopy(formula)
                        formula_copy.coef_interval = {}
                        formula_copy.term = formula.term.subs(comb)
                        for t in term_collection:
                            if formula_copy.term.equals(t):
                                break
                        else:
                            new_domain_knowledge.append(formula_copy)
                            term_collection.append(formula_copy.term)
                else:
                    new_domain_knowledge.append(formula)
            self.domain_knowledge = new_domain_knowledge

        axis_split = AxisAlignedSplittingStrategy()
        axis_split.priority = 1
        axis_split = self.predicate_converted(axis_split.find_split(dataset, impurity_measure))

        logreg_split = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
        logreg_split.priority = 1
        logreg_split = self.predicate_converted(logreg_split.find_split(dataset, impurity_measure))

        weinhub_split = WeinhuberApproachSplittingStrategy()
        weinhub_split.priority = 1
        weinhub_split.root = self.root
        weinhub_split.current_node = self.current_node
        weinhub_split = weinhub_split.find_split(dataset, impurity_measure)

        axis_distances = [i.tree_edit_distance(axis_split) for i in self.domain_knowledge]
        logreg_distances = [i.tree_edit_distance(logreg_split) for i in self.domain_knowledge]
        weinhub_distances = [i.tree_edit_distance(weinhub_split) for i in self.domain_knowledge]

        self.print_domain_knowledge()

        # TODO: avg, min, max values for every column
        # TODO: Number to every predicate
        # TODO: try every predicate within a tree edit distance of 5
        # TODO: also parse in units with # unit unit
        # TODO: linear classifier with respect of units

        print("\n------------------------ COMPUTED PREDICATES ------------------------ \nTREE DISTANCE\t\t\t|\t\t\tPREDICATE")
        print("{}\t\t\t\t\t\t|\t\t\t{}".format(min(axis_distances), axis_split.print_dot().replace("\\n", "")))
        print("{}\t\t\t\t\t\t|\t\t\t{}".format(min(logreg_distances), logreg_split.print_dot().replace("\\n", "")))
        print("{}\t\t\t\t\t\t|\t\t\t{}".format(min(weinhub_distances), weinhub_split.print_dot().replace("\\n", "")))
        print("---------------------------------------------------------------------")

    def print_domain_knowledge(self):
        print("\n\nSTARTING INTERACTIVE SHELL ...\n\n------------------------ DOMAIN KNOWLEDGE ------------------------ ")
        for i in self.domain_knowledge:
            print(i.print_dot().replace("\\n", ""))
        print("---------------------------------------------------------------------")

    def predicate_converted(self, predicate):
        # takes an axis_aligned or logreg split and converts it to an weinhuber approach split
        infinity = sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)
        relation = "<="

        if isinstance(predicate, AxisAlignedSplit):
            symbol = sp.sympify("x_{}".format(predicate.feature))
            term = sp.sympify("x_{} - {}".format(predicate.feature, predicate.threshold))
            column_interval = {symbol: infinity}
            return WeinhuberApproachSplit(column_interval, {}, term, relation)
        elif isinstance(predicate, LinearSplit):
            colum_interval = {}
            term = ""
            for num in range(len(predicate.numeric_columns)):
                symbol = sp.sympify("x_{}".format(predicate.numeric_columns[num]))
                colum_interval[symbol] = infinity
                term += "({}) * x_{} + ".format(predicate.coefficients[num], predicate.numeric_columns[num])
            term += "(" + str(predicate.intercept) + ")"
            return WeinhuberApproachSplit(colum_interval, {}, sp.sympify(term), relation)
        else:
            # Only supported conversion types are Axis Aligned Splits and Linear Splits
            raise WeinhuberStrategyException()
