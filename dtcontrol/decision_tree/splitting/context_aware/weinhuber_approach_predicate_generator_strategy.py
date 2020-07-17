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
import sys
import numpy as np


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

        """
        process domain knowledge and create all combinations
        domain knowledge is stored inside dtcontrol/decision_tree/splitting/context_aware/input_data/input_domain_knowledge.txt
        """
        x_numeric = dataset.get_numeric_x()
        print("\nSTARTING INTERACTIVE SHELL ...\n\n\n")
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

        # PRINTING DATASET INFORMATION
        x_meta = dataset.x_metadata
        y_meta = dataset.y_metadata

        print(
            "------------------------------------------------------------------------------------------------------------------------------------------\n"
            "\t\t\t\t\t\t FEATURE SPECIFICATION\n"
            "------------------------------------------------------------------------------------------------------------------------------------------\n"
            "Column\t|\t\tNAME\t\t|\t\tMIN\t\t|\t\tMAX\t\t|\t\tAVG\t\t|\tMEDIAN\t|\tSTEP SIZE\n"
            "------------------------------------------------------------------------------------------------------------------------------------------")

        median = np.median(x_numeric, axis=0)
        for i in range(x_numeric.shape[1]):
            print("x_{}\t\t\t{}\t\t\t\t{}\t\t\t\t{}\t\t\t\t{}\t\t\t\t{}\t\t\t{}".format(i, x_meta.get('variables')[i], x_meta.get('min')[i],
                                                                                        x_meta.get('max')[i],
                                                                                        (x_meta.get('min')[i] + x_meta.get('max')[i]) / 2,
                                                                                        median[i],
                                                                                        x_meta.get('step_size')[i]))

        print(
            "------------------------------------------------------------------------------------------------------------------------------------------\n"
            "\t\t\t\t\t\t LABEL SPECIFICATION\n"
            "------------------------------------------------------------------------------------------------------------------------------------------\n"
            "\t\tNAME\t\t|\t\tMIN\t\t|\t\tMAX\t\t|\tSTEP SIZE\n"
            "------------------------------------------------------------------------------------------------------------------------------------------")
        for i in range(len(y_meta.get('variables'))):
            print("{}\t\t\t\t{}\t\t\t\t{}\t\t\t\t{}".format(y_meta.get('variables')[i], y_meta.get('min')[i], y_meta.get('max')[i],
                                                            y_meta.get('step_size')[i]))

        domain_knowledge_imp = [(expr, impurity_measure.calculate_impurity(dataset, expr)) for expr in self.domain_knowledge]
        domain_knowledge_imp.sort(key=lambda x: x[1])

        # PRINTING DOMAIN KNOWLEDGE
        print(
            "------------------------------------------------------------------------------------------------------------------------------------------\n"
            "\t\t\t\t\t\t DOMAIN KNOWLEDGE\n"
            "------------------------------------------------------------------------------------------------------------------------------------------\n"
            "INDEX\t|\tIMPURITY\t|\tEXPRESSION\n"
            "------------------------------------------------------------------------------------------------------------------------------------------")
        for i in range(len(domain_knowledge_imp)):
            predicate = domain_knowledge_imp[i][0].print_dot().replace("\\n", "")
            print("{}\t\t|\t{}\t\t|\t{}".format(i, round(domain_knowledge_imp[i][1], ndigits=3), predicate))

        computed_splits_imp = []

        # Get the axis aligned split for current dataset
        axis_split = AxisAlignedSplittingStrategy()
        axis_split.priority = 1
        axis_split = self.predicate_converted(axis_split.find_split(dataset, impurity_measure))
        computed_splits_imp.append((axis_split, impurity_measure.calculate_impurity(dataset, axis_split)))

        # Get the linear classifier split for current dataset
        logreg_split = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
        logreg_split.priority = 1
        logreg_split = self.predicate_converted(logreg_split.find_split(dataset, impurity_measure))
        computed_splits_imp.append((logreg_split, impurity_measure.calculate_impurity(dataset, logreg_split)))

        """
        Get all user given splits for current dataset.
        User given splits are stored inside dtcontrol/decision_tree/splitting/context_aware/input_data/input_predicates.txt
        """

        weinhub = WeinhuberApproachSplittingStrategy()
        weinhub.priority = 1
        weinhub.root = self.root
        weinhub.current_node = self.current_node
        user_given_splits = weinhub.get_all_splits(dataset, impurity_measure)

        computed_splits_imp.extend(user_given_splits.items())
        computed_splits_imp.sort(key=lambda x: x[1])

        print(
            "------------------------------------------------------------------------------------------------------------------------------------------\n"
            "\t\t\t\t\t\t COMPUTED PREDICATES\n"
            "------------------------------------------------------------------------------------------------------------------------------------------\n"
            "INDEX\t|\tIMPURITY\t|\tDISTANCE°\t|\tEXPRESSION\n"
            "------------------------------------------------------------------------------------------------------------------------------------------")
        for i in range(len(computed_splits_imp)):
            index = len(domain_knowledge_imp) + i
            impurity = round(computed_splits_imp[i][1], ndigits=3)
            expr = computed_splits_imp[i][0].print_dot().replace("\\n", "")
            tree_distances = [computed_splits_imp[i][0].tree_edit_distance(j) for j in self.domain_knowledge]
            print("{}\t\t|\t{}\t\t|\t\t{}\t\t|\t{}".format(index, impurity, min(tree_distances), expr))
        print(
            "------------------------------------------------------------------------------------------------------------------------------------------\n"
            "(° Smallest tree editing distance compared with every expression from domain knowledge.)")


        # TODO: try every predicate within a tree edit distance of 5
        # TODO: also parse in units with # unit unit
        # TODO: linear classifier with respect of units

        sys.exit(187)

    @staticmethod
    def predicate_converted(predicate):
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
