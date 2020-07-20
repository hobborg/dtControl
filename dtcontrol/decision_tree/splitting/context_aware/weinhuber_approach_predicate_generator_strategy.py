from dtcontrol.decision_tree.splitting.context_aware.context_aware_splitting_strategy import \
    ContextAwareSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.predicate_parser import PredicateParser
from copy import deepcopy
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from itertools import product
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
import re
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_exceptions import WeinhuberGeneratorException
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_exceptions import WeinhuberPredicateParserException


class WeinhuberApproachPredicateGeneratorStrategy(ContextAwareSplittingStrategy):

    def __init__(self, domain_knowledge=None, determinizer=LabelPowersetDeterminizer(), debug=False):
        super().__init__()
        self.domain_knowledge = PredicateParser.get_domain_knowledge(debug=debug) if domain_knowledge is None else domain_knowledge
        self.determinizer = determinizer
        self.root = None
        self.current_node = None
        self.first_run = True

        # Storing the units of the current dataset (create inside domain knowledge file: #UNITS ...)
        self.dataset_units = None

        # logger
        self.logger = WeinhuberApproachLogger("WeinhuberApproachPredicateGenerator_logger", debug)
        self.debug = debug

        # Tree edit distances predicates will be stored here:
        self.recently_added_predicates_imp = []
        """
        Attributes used for the console output. 
        List containing Tuple: [(expr, impurity)]
        """
        self.domain_knowledge_imp = []
        self.computed_predicates_imp = []

    def process_domain_knowledge(self):
        """
        Function to pre-process the domain knowledge, given by the user inside the file:
        dtcontrol/decision_tree/splitting/context_aware/input_data/input_domain_knowledge.txt


        Since the domain knowledge should already be determined and given at the startup time by the user, this function only needs to be
        applied once at the first run of the program.

        Procedure:
            0. Domain knowledge gets parsed by dtcontrol/decision_tree/splitting/context_aware/predicate_parser.py
            1. Iterate over every domain knowledge expression
                1.1 If there are coefs used: Create every possible combination and add them to the domain knowledge
            2. Update self.domain_knowledge

        """

        if self.first_run:
            # Checking whether additional units were also given
            if isinstance(self.domain_knowledge[0], list):
                self.dataset_units = self.domain_knowledge[0]
                self.domain_knowledge = self.domain_knowledge[1:]

            new_domain_knowledge = []
            term_collection = []
            for expression in self.domain_knowledge:
                fixed_coefs = {}
                # Checking if domain knowledge is containing finite sets with fixed coefs
                for coef in expression.coef_interval:
                    if isinstance(expression.coef_interval[coef], sp.FiniteSet):
                        fixed_coefs[coef] = list(expression.coef_interval[coef].args)
                    else:
                        self.logger.root_logger.critical(
                            "Invalid interval inside domain knowledge expression found! Currently only Finite Sets are supported.")
                        raise WeinhuberGeneratorException(
                            "While processing the domain knowledge an invalid state was reached. Check logger or comments for more information.")

                # Creating all combinations
                if fixed_coefs:
                    # unzipping
                    coef, val = zip(*fixed_coefs.items())
                    # calculation all combinations and zipping back together
                    combinations = [list(zip(coef, nbr)) for nbr in product(*val)]

                    for comb in combinations:
                        # Create new Weinhuber Split obj
                        new_split = WeinhuberApproachSplit(expression.column_interval, {}, expression.term.subs(comb), expression.relation)
                        # Checking whether this expression is already represented
                        for t in term_collection:
                            if new_split.term.equals(t):
                                break
                        else:
                            new_domain_knowledge.append(new_split)
                            term_collection.append(new_split.term)
                else:
                    new_domain_knowledge.append(expression)
            self.domain_knowledge = new_domain_knowledge

    def print_dataset_specs(self, dataset):
        """
        Function to print interesting specifications about the current dataset.
        :param dataset: the subset of data at the current split
        :returns: None.
        """
        x_numeric = dataset.get_numeric_x()

        # Access metadata
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

    def print_domain_knowledge(self):
        """
        Function to print domain knowledge expressions.
        Uses only self.domain_knowledge_imp
        :returns: None
        """

        domain_knowledge = self.domain_knowledge_imp
        if len(domain_knowledge) > 0:
            print(
                "------------------------------------------------------------------------------------------------------------------------------------------\n"
                "\t\t\t\t\t\t DOMAIN KNOWLEDGE\n"
                "------------------------------------------------------------------------------------------------------------------------------------------\n"
                "INDEX\t|\tIMPURITY\t|\tEXPRESSION\n"
                "------------------------------------------------------------------------------------------------------------------------------------------")
            for i in range(len(domain_knowledge)):
                predicate = domain_knowledge[i][0].print_dot().replace("\\n", "")
                print("{}\t\t|\t{}\t\t|\t{}".format(i, round(domain_knowledge[i][1], ndigits=3), predicate))

    def print_recently_added_predicates(self):
        """
        Function to print recently added predicates.
        Uses only self.recently_added_predicates_imp
        :returns: None
        """

        recently_added_predicates = self.recently_added_predicates_imp
        if len(recently_added_predicates) > 0:
            print(
                "------------------------------------------------------------------------------------------------------------------------------------------\n"
                "\t\t\t\t\t\t RECENTLY ADDED PREDICATES°\n"
                "------------------------------------------------------------------------------------------------------------------------------------------\n"
                "INDEX\t|\tIMPURITY\t|\tDISTANCE°°\t|\tEXPRESSION\n"
                "------------------------------------------------------------------------------------------------------------------------------------------")
            for i in range(len(recently_added_predicates)):
                index = len(self.domain_knowledge) + len(self.computed_predicates_imp) + i
                impurity = round(recently_added_predicates[i][1], ndigits=3)
                expr = recently_added_predicates[i][0].print_dot().replace("\\n", "")
                tree_distances = [recently_added_predicates[i][0].tree_edit_distance(j) for j in self.domain_knowledge]
                print("{}\t\t|\t{}\t\t|\t\t{}\t\t|\t{}".format(index, impurity, min(tree_distances), expr))
            print(
                "------------------------------------------------------------------------------------------------------------------------------------------\n"
                "(°) Predicates obtained by user, as well as one alternative Axis Aligned predicate and one Linear predicate.\n"
                "(°°) Smallest tree editing distance compared with every expression from domain knowledge.")

    def print_alternative_predicates(self):
        """
        Function to print alternative splits.
        Uses only self.computed_predicates_imp
        :returns: None

        CAUTION:
            self.computed_predicates_imp, contains predicates obtained by user as well as one alternative axis aligned predicate
            and one logreg!
        """

        computed_predicates = self.computed_predicates_imp
        if len(computed_predicates) > 0:
            print(
                "------------------------------------------------------------------------------------------------------------------------------------------\n"
                "\t\t\t\t\t\t COMPUTED PREDICATES°\n"
                "------------------------------------------------------------------------------------------------------------------------------------------\n"
                "INDEX\t|\tIMPURITY\t|\tDISTANCE°°\t|\tEXPRESSION\n"
                "------------------------------------------------------------------------------------------------------------------------------------------")
            for i in range(len(computed_predicates)):
                index = len(self.domain_knowledge) + i
                impurity = round(computed_predicates[i][1], ndigits=3)
                expr = computed_predicates[i][0].print_dot().replace("\\n", "")
                tree_distances = [computed_predicates[i][0].tree_edit_distance(j) for j in self.domain_knowledge]
                print("{}\t\t|\t{}\t\t|\t\t{}\t\t|\t{}".format(index, impurity, min(tree_distances), expr))
            print(
                "------------------------------------------------------------------------------------------------------------------------------------------\n"
                "(°) Predicates obtained by user, as well as one alternative Axis Aligned predicate and one Linear predicate.\n"
                "(°°) Smallest tree editing distance compared with every expression from domain knowledge.")

    def user_input_handler(self, dataset, impurity_measure):
        """
        Function to handle the user input via console.
        :returns: Integer. (index of predicate which should be returned.)
        """

        print("\nSTARTING INTERACTIVE SHELL. PLEASE ENTER YOUR COMMANDS. TYPE '/help' FOR HELP.\n")

        for input_line in sys.stdin:
            input_line = input_line.strip()
            if input_line == "/help":
                print(
                    "------------------------------------------------------------------------------------------------------------------------------------------\n"
                    "\t\t\t\t\t\t HELP WINDOW\n"
                    "------------------------------------------------------------------------------------------------------------------------------------------\n"
                    "/help\t\t\t\t\t\t\t\t\t\t\t\t|\t display help window\n"
                    "/use <Index>\t\t\t\t\t\t\t\t\t\t|\t select predicate at index to be returned\n"
                    "/add <Expression>\t\t\t\t\t\t\t\t\t|\t add an expression\n"
                    "/distance <TreeEditDistance> <Index>\t\t\t\t|\t compute and add all expressions within given <TreeEditDistance> of predicate at <Index>. Will show the 5 best results.\n"
                    "/distance <TreeEditDistance> <NbrResults> <Index>\t|\t compute and add all expressions within given <TreeEditDistance> of predicate at <Index>. Will show the <NbrResult> best results.\n"
                    "/refresh\t\t\t\t\t\t\t\t\t\t\t|\t will refresh the console output\n"
                    "/exit\t\t\t\t\t\t\t\t\t\t\t\t|\t to exit\n"
                    "------------------------------------------------------------------------------------------------------------------------------------------")
            elif input_line == "/exit" or input_line == ":q" or input_line == ":q!" or input_line == ":quit":
                sys.exit(999999)
            elif re.match("/use \d+", input_line):
                # Use predicate on index x
                return int(input_line.split("/use ")[1])
                pass
            elif input_line.startswith("/add "):
                user_input = input_line.split("/add ")[1]
                pred = PredicateParser.parse_single_predicate(user_input, "GeneratorPredicate", self.debug)
                self.recently_added_predicates_imp.append((pred, impurity_measure.calculate_impurity(dataset, pred)))

                self.print_domain_knowledge()
                self.print_alternative_predicates()
                self.print_recently_added_predicates()
            elif re.match("/distance \d+ \d+ \d+", input_line):
                # create new splits out of given split within tree edit distance of given number
                pass
            elif re.match("/distance \d+ \d+", input_line):
                # create new splits out of given split within tree edit distance of given number
                pass

            elif input_line == "/refresh":
                # prints everything again
                self.print_domain_knowledge()
                self.print_alternative_predicates()
                self.print_recently_added_predicates()
                print("\nSTARTING INTERACTIVE SHELL. PLEASE ENTER YOUR COMMANDS. TYPE '/help' FOR HELP.\n")
            else:
                print("Unknown command. Type '/help' for help.")

    def find_split(self, dataset, impurity_measure):
        # TODO: try every predicate within a tree edit distance of 5
        # TODO: also parse in units with # unit unit
        # TODO: linear classifier with respect of units
        # (TODO: Function in split obj which creates list of all possible combinations of a split.)
        # TODO: Domain knowledge expressions should only be allowed to have finite set coefs or should it ?
        # TODO: Check the other exceptions

        """
        additional predicates given before startup are stored in dtcontrol/decision_tree/splitting/context_aware/input_data/input_predicates.txt
        domain knowledge is stored inside dtcontrol/decision_tree/splitting/context_aware/input_data/input_domain_knowledge.txt

        Procedure:
            (1.) Print dataset specs
            2. Process domain knowledge
            (2.1) Print domain knowledge
            3. Create alternative splits/predicates
                3.1 create axis aligned split
                3.2 create logreg split
                3.3 create user given splits if there are any given
            4. Start user_input_handler()
            5. Returned split chosen by user via user_input_handler()
        """
        self.recently_added_predicates_imp = []
        self.print_dataset_specs(dataset)
        self.process_domain_knowledge()

        """
        self.domain_knowledge_imp
        Sorted list containing domain knowledge given by user.
        Format:
            - List containing Tuple: [(domain_expression, impurity)]
        """
        domain_knowledge_imp = [(expr, impurity_measure.calculate_impurity(dataset, expr)) for expr in deepcopy(self.domain_knowledge)]
        domain_knowledge_imp.sort(key=lambda x: x[1])
        self.domain_knowledge_imp = domain_knowledge_imp

        self.print_domain_knowledge()

        """
        self.computed_predicates_imp
        Sorted list containing all alternative splits.
        Format:
            - List containing Tuple: [(alternative_split, impurity)]
        """
        computed_predicates_imp = []

        # Get the axis aligned split for current dataset
        axis_split = AxisAlignedSplittingStrategy()
        axis_split.priority = 1
        axis_split = self.predicate_converted(axis_split.find_split(dataset, impurity_measure))
        computed_predicates_imp.append((axis_split, impurity_measure.calculate_impurity(dataset, axis_split)))

        # Get the linear classifier split for current dataset
        logreg_split = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
        logreg_split.priority = 1
        logreg_split = self.predicate_converted(logreg_split.find_split(dataset, impurity_measure))
        computed_predicates_imp.append((logreg_split, impurity_measure.calculate_impurity(dataset, logreg_split)))

        """
        Process all other given user predicates.
        (User given splits are stored inside dtcontrol/decision_tree/splitting/context_aware/input_data/input_predicates.txt)
        Important: If there are no user given splits --> Predicate Parser will raise an Exception
        """
        try:
            weinhub = WeinhuberApproachSplittingStrategy()
            weinhub.priority = 1
            weinhub.root = self.root
            weinhub.current_node = self.current_node
            user_given_splits = weinhub.get_all_splits(dataset, impurity_measure)
            computed_predicates_imp.extend(user_given_splits.items())
        except WeinhuberPredicateParserException:
            pass

        computed_predicates_imp.sort(key=lambda x: x[1])
        self.computed_predicates_imp = computed_predicates_imp

        self.print_alternative_predicates()
        self.print_recently_added_predicates()

        # TODO: Delete this statement
        print(self.dataset_units)
        # handle_user_input
        return_index = self.user_input_handler(dataset, impurity_measure)

        # mapping of return index to split obj
        if return_index < len(self.domain_knowledge_imp):
            return_split = self.domain_knowledge_imp[return_index][0]
        elif return_index < len(self.domain_knowledge_imp) + len(self.computed_predicates_imp):
            return_split = self.computed_predicates_imp[return_index - len(self.domain_knowledge_imp)][0]
        else:
            return_split = \
                self.recently_added_predicates_imp[return_index - len(self.domain_knowledge_imp) - len(self.computed_predicates_imp)][0]

        self.logger.root_logger.info("Returned split: {}".format(str(return_split)))
        return return_split

    def predicate_converted(self, predicate):
        """
        Function to convert an axis_aligned or logreg split into an weinhuber approach split
        :param predicate: Axis Aligned or Logreg Split
        :returns: WeinhuberApproachSplit Object representing the initial predicate.

        CAUTION:
        Only supported conversion types are Axis Aligned Splits and Linear Splits to WeinhuberApproachSplit !
        """

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
            self.logger.root_logger.critical(
                "Invalid state while converting the predicates reached. Only supported conversion types are Axis Aligned Splits and Linear Splits.")
            raise WeinhuberGeneratorException(
                "Only supported conversion types are Axis Aligned Splits and Linear Splits. Check logger or comments for more information.")
