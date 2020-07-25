from copy import deepcopy

from dtcontrol.decision_tree.splitting.context_aware.context_aware_splitting_strategy import \
    ContextAwareSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.predicate_parser import PredicateParser
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_logger import WeinhuberApproachLogger
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from sklearn.linear_model import LogisticRegression
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_splitting_strategy import WeinhuberApproachSplittingStrategy
import sys
import numpy as np
import re
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_linear_units_classifier import \
    WeinhuberApproachLinearUnitsClassifier
from tabulate import tabulate


class WeinhuberApproachPredicateGeneratorStrategy(ContextAwareSplittingStrategy):

    def __init__(self, domain_knowledge=None, determinizer=LabelPowersetDeterminizer(), debug=False):
        super().__init__()

        """
        Current path to 'domain knowledge file' = dtcontrol/decision_tree/splitting/context_aware/input_data/input_domain_knowledge.txt
        
        dataset_units:
            Storing the units of the current dataset 
                --> given in first line inside 'domain knowledge file': #UNITS ...
                --> Is optional. If the first line doesn't contain units, dataset_units will just remain None
                
        standard_predicates:
            List of WeinhuberApproachSplit Objects given at startup inside 'domain knowledge file'
                
        """

        self.dataset_units, self.standard_predicates = PredicateParser.get_domain_knowledge(
            debug=debug) if domain_knowledge is None else domain_knowledge
        self.recently_added_predicates = []
        self.determinizer = determinizer
        self.root = None
        self.current_node = None

        # logger
        self.logger = WeinhuberApproachLogger("WeinhuberApproachPredicateGenerator_logger", debug)
        self.debug = debug

        """
        standard_predicates_imp and recently_added_predicates_imp have the same structure:
        --> List containing Tuple: [(Predicate, impurity)]
        
        Both contain the 'fitted' instances of their corresponding predicate collection
        
        standard_alt_predicates_imp:
            --> Contains all standard_predicates AND alternative_strategies predicates
        
        recently_added_predicates_imp:
            - used to store: predicates added by user via user_input_handler() --> '/add <Predicate>'
        """

        self.standard_alt_predicates_imp = []
        self.recently_added_predicates_imp = []

        # List containing alternative splitting strategies [axis, logreg, logreg_unit]
        self.alternative_strategies = self.set_up_strats()

    def set_up_strats(self):
        """
        Function to setup the alternative splitting Strategies.
        """
        # Axis Aligned
        axis = AxisAlignedSplittingStrategy()
        axis.priority = 1

        # Linear
        logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
        logreg.priority = 1

        # Linear Units (Only if there are units given)
        logreg_unit = WeinhuberApproachLinearUnitsClassifier(LogisticRegression, self.dataset_units, solver='lbfgs', penalty='none')
        logreg_unit.priority = 1

        return [axis, logreg, logreg_unit] if self.dataset_units is not None else [axis, logreg]

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

        median = np.median(x_numeric, axis=0)

        # FEATURE INFORMATION

        if x_meta.get('variables') is not None and x_meta.get('step_size') is not None:
            # Detailed meta data available
            table_feature = [["x_" + str(i), x_meta.get('variables')[i], np.min(x_numeric[:, i]),
                              np.max(x_numeric[:, i]),
                              (np.min(x_numeric[:, i]) + np.max(x_numeric[:, i])) / 2,
                              median[i],
                              x_meta.get('step_size')[i]] for i in range(x_numeric.shape[1])]

            header_feature = ["COLUMN", "NAME", "MIN", "MAX", "AVG", "MEDIAN", "STEP SIZE"]
            # Add Units if available
            if self.dataset_units is not None:
                for i in range(len(table_feature)):
                    table_feature[i].append(self.dataset_units[i])
                header_feature.append("UNIT")

            print("\n\t\t\t\t\t\t FEATURE INFORMATION\n" + tabulate(
                table_feature,
                header_feature,
                tablefmt="psql"))
        else:
            # Meta data not available
            table_feature = [["x_" + str(i), np.min(x_numeric[:, i]),
                              np.max(x_numeric[:, i]),
                              (np.min(x_numeric[:, i]) + np.max(x_numeric[:, i])) / 2,
                              median[i]] for i in range(x_numeric.shape[1])]

            header_feature = ["COLUMN", "MIN", "MAX", "AVG", "MEDIAN"]
            # Add Units if available
            if self.dataset_units is not None:
                for i in range(len(table_feature)):
                    table_feature[i].append(self.dataset_units[i])
                header_feature.append("UNIT")

            print("\n\t\t\t FEATURE SPECIFICATION\n" + tabulate(
                table_feature,
                header_feature,
                tablefmt="psql"))

        # LABEL INFORMATION

        if y_meta.get('variables') is not None and \
                y_meta.get('min') is not None and \
                y_meta.get('max') is not None and \
                y_meta.get('step_size') is not None:
            # Detailed meta data available
            table_label = [[y_meta.get('variables')[i], y_meta.get('min')[i], y_meta.get('max')[i],
                            y_meta.get('step_size')[i]] for i in range(len(y_meta.get('variables')))]
            print("\n\t\t\t LABEL SPECIFICATION\n" + tabulate(
                table_label,
                ["NAME", "MIN", "MAX", "STEP SIZE"],
                tablefmt="psql"))
        else:
            # No meta data available
            print("\nNo detailed label information available.")

    def print_standard_alt_predicates(self):
        """
        Function to print standard_alt_predicates_imp.
        Uses only self.standard_alt_predicates_imp
        :returns: None -> Console Output
        """

        if len(self.standard_alt_predicates_imp) > 0:
            table_domain = [[i, round(self.standard_alt_predicates_imp[i][1], ndigits=3),
                             self.standard_alt_predicates_imp[i][0].print_dot().replace("\\n", "")] for i in
                            range(len(self.standard_alt_predicates_imp))]

            print("\n\t\t\t STANDARD AND ALTERNATIVE PREDICATES°\n" + tabulate(
                table_domain,
                ["INDEX", "IMPURITY", "EXPRESSION"],
                tablefmt="psql") + "\n(°) Contains predicates obtained by user at startup, as well as one alternative Axis Aligned predicate and one or two Linear.")
        else:
            print("\nNo standard and alternative predicates.")

    def print_recently_added_predicates(self):
        """
        Function to print recently added predicates.
        Uses only self.recently_added_predicates_imp
        :returns: None -> Console Output
        """

        if len(self.recently_added_predicates_imp) > 0:
            table_recently_added = [
                [len(self.standard_alt_predicates_imp) + i, round(self.recently_added_predicates_imp[i][1], ndigits=3),
                 self.recently_added_predicates_imp[i][0].print_dot().replace("\\n", "")] for i in
                range(len(self.recently_added_predicates_imp))]

            print("\n\t\t\t RECENTLY ADDED PREDICATES\n" + tabulate(
                table_recently_added,
                ["INDEX", "IMPURITY", "EXPRESSION"],
                tablefmt="psql"))
        else:
            print("\nNo recently added predicates.")

    def user_input_handler(self, dataset, impurity_measure):
        """
        Function to handle the user input via console.
        :returns: Integer. (index of predicate which should be returned.)
        """

        for input_line in sys.stdin:
            input_line = input_line.strip()
            if input_line == "/help":
                print("\n" + tabulate([["/help", "display help window"],
                                       ["/use <Index>", "select predicate at index to be returned. ('use and keep table')"],
                                       ["/use_empty <Index>",
                                        "select predicate at index to be returned. Works only on recently added table. ('use and empty table')"],
                                       ["/add <Expression>", "add an expression"],
                                       ["/add_standard <Expression>", "add an expression to standard and alternative predicates"],
                                       ["/del <Index>", "select predicate at index to be deleted"],
                                       ["/del_all_recent", "clear recently_added_predicates list"],
                                       ["/del_all_standard", "clear standard and alternative predicates list"],
                                       ["/refresh", "refresh the console output"],
                                       ["/exit", "to exit"]],
                                      tablefmt="psql") + "\n")
            elif input_line == "/exit":
                sys.exit(187)
            elif re.match("/use \d+", input_line):
                # Use predicate on index x
                # TODO: Edge Case index out of range
                return int(input_line.split("/use ")[1])
            elif re.match("/use_empty \d+", input_line):
                # TODO: Edge Case index out of range
                index = int(input_line.split("/use_empty ")[1])
                if index < len(self.standard_alt_predicates_imp):
                    print("Invalid index. /use_empty is only available on recently_added_predicates.")
                else:
                    pred = self.index_predicate_mapping(index)
                    pred.coef_assignment = None
                    for i in self.recently_added_predicates:
                        if not i.helper_equal(pred):
                            self.recently_added_predicates.remove(i)
                    return index

            elif input_line.startswith("/add "):
                user_input = input_line.split("/add ")[1]
                parsed_input = PredicateParser.parse_single_predicate(user_input, self.logger, self.debug)

                # Duplicate check
                for pred in self.recently_added_predicates:
                    if pred.helper_equal(parsed_input):
                        print("ADDING FAILED: duplicate found.")
                        self.logger.root_logger.info("User tried to add a duplicate predicate to 'recently_added_predicates'.")
                        break
                else:
                    # add input to recently added predicates collection
                    self.recently_added_predicates.append(parsed_input)

                    # add all fitted instances to recently_added_predicates_imp
                    all_pred = self.weinhub_approach_strat([parsed_input], dataset, impurity_measure)
                    self.recently_added_predicates_imp.extend(list(all_pred.items()))
                    self.recently_added_predicates_imp.sort(key=lambda x: x[1])

                    self.console_output(dataset)
            elif input_line.startswith("/add_standard "):
                user_input = input_line.split("/add_standard ")[1]
                parsed_input = PredicateParser.parse_single_predicate(user_input, self.logger, self.debug)

                # Duplicate check
                for pred in self.standard_predicates:
                    if pred.helper_equal(parsed_input):
                        print("ADDING FAILED: duplicate found.")
                        self.logger.root_logger.info("User tried to add a duplicate predicate to 'standard_predicates'.")
                        break
                else:

                    # add input to standard predicates collection
                    self.standard_predicates.append(parsed_input)

                    # add all fitted instances to
                    all_pred = self.weinhub_approach_strat([parsed_input], dataset, impurity_measure)
                    self.standard_alt_predicates_imp.extend(list(all_pred.items()))
                    self.standard_alt_predicates_imp.sort(key=lambda x: x[1])

                    self.console_output(dataset)
            elif input_line == "/del_all_recent":
                self.recently_added_predicates = []
                self.recently_added_predicates_imp = []
                self.console_output(dataset)
            elif input_line == "/del_all_standard":
                self.standard_predicates = []
                self.standard_alt_predicates_imp = []
                self.console_output(dataset)
            elif re.match("/del \d+", input_line):
                # del predicate at index
                # TODO: Edge Case index out of range
                index = int(input_line.split("/del ")[1])
                pred = self.index_predicate_mapping(index)

                if not isinstance(pred, WeinhuberApproachSplit):
                    print("Invalid predicate: You can only delete user added predicates.")
                else:
                    pred.coef_assignment = None
                    # Checking in which list the predicate to delete was
                    if index < len(self.standard_alt_predicates_imp):
                        del self.standard_alt_predicates_imp[index]
                        for i in self.standard_predicates:
                            if i.helper_equal(pred):
                                self.standard_predicates.remove(i)
                    else:
                        del self.recently_added_predicates_imp[index - len(self.standard_alt_predicates_imp)]
                        for i in self.recently_added_predicates:
                            if i.helper_equal(pred):
                                self.recently_added_predicates.remove(i)
                self.console_output(dataset)
            elif input_line == "/refresh":
                # prints everything again
                self.console_output(dataset)
            else:
                print("Unknown command. Type '/help' for help.")

    def process_standard_alt_predicates(self, dataset, impurity_measure):
        """
        Function to setup standard_alt_predicates_imp for future usage.

        Procedure:
            1. All predicates inside self.standard_predicates get fit and checked
            2. Add additional alternative splitting strategies:
                2.1 Axis Aligned
                2.2 Linear Basic
                2.3 If Units available: Linear with Unit respect
            3. Sort self.standard_alt_predicates_imp
        """
        all_predicates = self.weinhub_approach_strat(self.standard_predicates, dataset, impurity_measure)
        self.standard_alt_predicates_imp = list(all_predicates.items())

        # Add the split objects from self.alternative_strategies
        for strat in self.alternative_strategies:
            pred = strat.find_split(dataset, impurity_measure)
            imp = impurity_measure.calculate_impurity(dataset, pred)
            self.standard_alt_predicates_imp.append((pred, imp))

        self.standard_alt_predicates_imp.sort(key=lambda x: x[1])

    def process_recently_added_predicates(self, dataset, impurity_measure):
        """
        Function to setup recently_added_predicates_imp for future usage.

        Procedure:
            1. All predicates inside self.recently_added_predicates get fit and checked
            2. Sort self.standard_alt_predicates_imp
        """
        all_predicates = self.weinhub_approach_strat(self.recently_added_predicates, dataset, impurity_measure)
        self.recently_added_predicates_imp = list(all_predicates.items())
        self.recently_added_predicates_imp.sort(key=lambda x: x[1])

    def find_split(self, dataset, impurity_measure):

        """
        Procedure:
            1. Process Standard and alternative predicates
            2. Process recently added predicates
            3. Print console output
            4. Start user_input_handler()
                --> possibility for user to add/del predicates
            5. Returned split chosen by user via user_input_handler()

        """

        self.process_standard_alt_predicates(dataset, impurity_measure)
        self.process_recently_added_predicates(dataset, impurity_measure)
        self.console_output(dataset)

        # handle_user_input
        index = self.user_input_handler(dataset, impurity_measure)
        return_split = self.index_predicate_mapping(index)

        self.logger.root_logger.info("Returned split: {}".format(str(return_split)))
        return return_split

    def weinhub_approach_strat(self, user_given_splits, dataset, impurity_measure):
        """
        Function to quickly instantiate a NEW instance of WeinhuberApproachSplittingStrategy.

        Background Information:
            A new instance will be created since some functionality like checking the predicates will only be done once at the first_run.
        """
        weinhub = WeinhuberApproachSplittingStrategy(user_given_splits=user_given_splits, debug=self.debug)
        weinhub.priority = 1
        weinhub.optimized_tree_check_version = False
        weinhub.curve_fitting_method = "optimized"
        return weinhub.get_all_splits(dataset, impurity_measure)

    def index_predicate_mapping(self, index):
        """
        Function to map an index to the corresponding predicate.
        :param index: Integer. Index of predicate as displayed in the console output.
        :returns: Split Object.
        """
        if index < len(self.standard_alt_predicates_imp):
            return_split = self.standard_alt_predicates_imp[index][0]
        else:
            return_split = self.recently_added_predicates_imp[index - len(self.standard_alt_predicates_imp)][0]

        return return_split

    def console_output(self, dataset):
        self.print_dataset_specs(dataset)
        self.print_standard_alt_predicates()
        self.print_recently_added_predicates()
        print("\nSTARTING INTERACTIVE SHELL. PLEASE ENTER YOUR COMMANDS. TYPE '/help' FOR HELP.\n")
