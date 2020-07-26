from copy import deepcopy

from dtcontrol.decision_tree.splitting.context_aware.context_aware_splitting_strategy import \
    ContextAwareSplittingStrategy
from dtcontrol.decision_tree.splitting.context_aware.predicate_parser import PredicateParser
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_exceptions import WeinhuberPredicateParserException, \
    WeinhuberStrategyException
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_logger import WeinhuberApproachLogger
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy, AxisAlignedSplit
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
        self.alternative_strategies = self.setup_alternative_strategies()

        # Reference to weinhuber approach splitting strategy, to get all possible splits
        self.weinhub_strat = self.setup_weinhub_strat()

    def setup_alternative_strategies(self):
        """
        Function to setup the alternative splitting Strategies.
        --> Sets up Axis Aligned, Linear Classifier and if units are given Linear with respect of units.

        (Units can be given at the first line inside dtcontrol/decision_tree/splitting/context_aware/input_data/input_domain_knowledge.txt)
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

    def setup_weinhub_strat(self):
        """
        Function to setup an weinhuber approach splitting strategy instance.
        """
        weinhub = WeinhuberApproachSplittingStrategy(user_given_splits=[], debug=self.debug)
        weinhub.priority = 1
        weinhub.optimized_tree_check_version = False
        weinhub.curve_fitting_method = "optimized"
        return weinhub

    def get_all_weinhub_splits(self, starting_predicates, dataset, impurity_measure):
        """
        Function to get all possible fitted instances of one predicate.
        :param starting_predicates: List of predicates to be processed.
        :param dataset: the subset of data at the current 'situation'
        :param impurity_measure: impurity measure to use.
        :returns: Dict containing all fitted instances. (key: split value: impurity)

        e.g:
        starting_predicate: c_0*x_0+c_1*x_1+c_2*x_2+c_3*x_3 <= c_4

        returns: {  -0.70769*x_0 - 0.011934*x_1 - 0.38391*x_2 + 0.32438*x_3 + 1.222 <= 0  <= 0: 1.6,
                    -0.10073*x_0 + 0.00080492*x_1 + 0.5956*x_2 - 0.22309*x_3 - 0.96975 <= 0 <= 0: 1.3219280948873622,
                    0.6178*x_0 - 0.0033169*x_1 - 0.0099337*x_2 + 0.35789*x_3 - 2.4716 <= 0: inf,
                    0.19595*x_0 + 0.0047356*x_1 - 0.48916*x_2 - 0.57777*x_3 + 1.2301 <= 0 <= 0: 1.8529325012980808,
                    -0.27807*x_0 + 0.0071843*x_1 + 0.16831*x_2 + 0.16076*x_3 - 1.4741 <= 0 <= 0: 1.8529325012980808,
                    0.6178*x_0 - 0.0033169*x_1 - 0.0099337*x_2 + 0.35789*x_3 - 2.4716 <= 0: inf}

        """
        self.weinhub_strat.first_run = True
        self.weinhub_strat.user_given_splits = starting_predicates
        return self.weinhub_strat.get_all_splits(dataset, impurity_measure)

    def print_dataset_specs(self, dataset):
        """
        CAUTION!: It is not recommended to use this function alone. Use it via console_output()

        Function to print interesting specifications about the current dataset.
        :param dataset: the subset of data at the current split
        :returns: None. --> Console output
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
        CAUTION!: It is not recommended to use this function alone. Use it via console_output()

        Function to print standard_alt_predicates_imp.
        Uses only self.standard_alt_predicates_imp
        :returns: None -> Console Output
        """

        if len(self.standard_alt_predicates_imp) > 0:
            table = []
            created_by_index = -1
            for member in self.standard_alt_predicates_imp:
                if isinstance(member[0], WeinhuberApproachSplit):
                    for parent in self.standard_predicates:
                        if parent.id == member[0].id:
                            created_by_index = self.standard_predicates.index(parent)
                            break
                elif isinstance(member[0], AxisAlignedSplit):
                    created_by_index = "Axis Aligned"
                else:
                    created_by_index = "Linear"

                table.append(
                    [self.standard_alt_predicates_imp.index(member), round(member[1], ndigits=3), member[0].print_dot().replace("\\n", ""),
                     created_by_index])

            print("\n\t\t\t STANDARD AND ALTERNATIVE PREDICATES°\n" + tabulate(
                table,
                ["INDEX", "IMPURITY", "EXPRESSION", "PARENT ID"],
                tablefmt="psql") + "\n(°) Contains predicates obtained by user at startup, as well as one alternative Axis Aligned predicate and one or two Linear.")
        else:
            print("\nNo standard and alternative predicates.")

    def print_recently_added_predicates(self):
        """
        CAUTION!: It is not recommended to use this function alone. Use it via console_output()

        Function to print recently added predicates.
        Uses only self.recently_added_predicates_imp
        :returns: None -> Console Output
        """

        if len(self.recently_added_predicates_imp) > 0:
            table = []
            created_by_index = -1
            for member in self.recently_added_predicates_imp:
                for parent in self.recently_added_predicates:
                    if parent.id == member[0].id:
                        created_by_index = self.recently_added_predicates.index((parent)) + len(self.standard_predicates)
                        break
                table.append(
                    [self.recently_added_predicates_imp.index(member) + len(self.standard_alt_predicates_imp), round(member[1], ndigits=3),
                     member[0].print_dot().replace("\\n", ""), created_by_index])

            print("\n\t\t\t RECENTLY ADDED PREDICATES\n" + tabulate(
                table,
                ["INDEX", "IMPURITY", "EXPRESSION", "PARENT ID"],
                tablefmt="psql"))
        else:
            print("\nNo recently added predicates.")

    def user_input_handler(self, dataset, impurity_measure):
        """
        Function to handle the user input via console.
        :param dataset: only used for console output (dataset infos) and to get all splits (via weinhuber approach strat)
        :param impurity_measure: only used to get all splits (via weinhuber approach strat)
        :returns: Integer. (index of predicate which should be returned.)

        """

        for input_line in sys.stdin:
            input_line = input_line.strip()
            if input_line == "/help":
                # display help window
                print("\n" + tabulate([["/help", "display help window"],
                                       ["/use <Index>", "select predicate at index to be returned. ('use and keep table')"],
                                       ["/use_empty <Index>",
                                        "select predicate at index to be returned. Works only on recently added table. ('use and empty table')"],
                                       ["/add <Expression>", "add an expression. (to 'recently added predicates' table)"],
                                       ["/add_standard <Expression>", "add an expression to standard and alternative predicates"],
                                       ["/del <PARENT ID>", "delete predicate with <PARENT ID>"],
                                       ["/del_all_recent", "clear recently_added_predicates list"],
                                       ["/del_all_standard", "clear standard and alternative predicates list"],
                                       ["/refresh", "refresh the console output"],
                                       ["/exit", "to exit"]],
                                      tablefmt="psql") + "\n")
            elif input_line == "/exit":
                # exit the program
                sys.exit(187)
            elif re.match("/use \d+", input_line):
                # select predicate at index to be returned. ('use and keep table')

                index = int(input_line.split("/use ")[1])
                # Index out of range check
                if index < 0 or index >= (len(self.standard_alt_predicates_imp) + len(self.recently_added_predicates_imp)):
                    print("Invalid index.")
                else:
                    users_choice = self.index_predicate_mapping(index)
                    if users_choice[1] < np.inf or self.user_double_check_inf(users_choice):
                        return users_choice[0]
                    else:
                        self.console_output(dataset)
            elif re.match("/use_empty \d+", input_line):
                # select predicate at index to be returned. Works only on recently added table. ('use and empty table')
                index = int(input_line.split("/use_empty ")[1])
                if index < len(self.standard_alt_predicates_imp):
                    print("Invalid index. /use_empty is only available on recently_added_predicates.")
                else:
                    users_choice = self.index_predicate_mapping(index)
                    if users_choice[1] < np.inf or self.user_double_check_inf(users_choice):
                        pred = users_choice[0]
                        for i in self.recently_added_predicates:
                            if i.id != pred.id:
                                self.recently_added_predicates.remove(i)
                        return pred
                    else:
                        self.console_output(dataset)
            elif input_line.startswith("/add "):
                # add an expression (to recently added predicates table)
                user_input = input_line.split("/add ")[1]
                try:
                    parsed_input = PredicateParser.parse_single_predicate(user_input, self.logger, self.debug)
                except WeinhuberPredicateParserException:
                    print("Invalid predicate entered. Please check logger or comments for more information.")
                else:
                    # Duplicate check
                    for pred in self.recently_added_predicates:
                        if pred.helper_equal(parsed_input):
                            print("ADDING FAILED: duplicate found.")
                            self.logger.root_logger.info("User tried to add a duplicate predicate to 'recently_added_predicates'.")
                            break
                    else:
                        try:
                            all_pred = self.get_all_weinhub_splits([parsed_input], dataset, impurity_measure)
                        except WeinhuberStrategyException:
                            print("Invalid predicate parsed. Please check logger or comments for more information.")
                        else:
                            # add input to recently added predicates collection
                            self.recently_added_predicates.append(parsed_input)

                            # add all fitted instances to recently_added_predicates_imp
                            self.recently_added_predicates_imp.extend(list(all_pred.items()))
                            self.recently_added_predicates_imp.sort(key=lambda x: x[1])
                            # refresh console output
                            self.console_output(dataset)
            elif input_line.startswith("/add_standard "):
                # add an expression to standard and alternative predicates
                user_input = input_line.split("/add_standard ")[1]
                try:
                    parsed_input = PredicateParser.parse_single_predicate(user_input, self.logger, self.debug)
                except WeinhuberPredicateParserException:
                    print("Invalid predicate entered. Please check logger or comments for more information.")
                else:
                    # Duplicate check
                    for pred in self.standard_predicates:
                        if pred.helper_equal(parsed_input):
                            print("ADDING FAILED: duplicate found.")
                            self.logger.root_logger.info("User tried to add a duplicate predicate to 'standard_predicates'.")
                            break
                    else:
                        try:
                            all_pred = self.get_all_weinhub_splits([parsed_input], dataset, impurity_measure)
                        except WeinhuberStrategyException:
                            print("Invalid predicate parsed. Please check logger or comments for more information.")
                        else:
                            # add input to standard predicates collection
                            self.standard_predicates.append(parsed_input)

                            # add all fitted instances to
                            self.standard_alt_predicates_imp.extend(list(all_pred.items()))
                            self.standard_alt_predicates_imp.sort(key=lambda x: x[1])
                            # refresh console output
                            self.console_output(dataset)
            elif input_line == "/del_all_recent":
                # clear recently_added_predicates list
                self.recently_added_predicates = []
                self.recently_added_predicates_imp = []
                self.console_output(dataset)
            elif input_line == "/del_all_standard":
                # clear standard and alternative predicates list
                self.standard_predicates = []
                self.standard_alt_predicates_imp = []
                self.console_output(dataset)
            elif re.match("/del \d+", input_line):
                # select predicate VIA ID to be deleted
                del_id = int(input_line.split("/del ")[1])
                if self.user_double_check_del():
                    if del_id < 0:
                        print("Invalid Id.")
                    elif del_id < len(self.standard_predicates):
                        real_parent_id = self.standard_predicates[del_id].id
                        del self.standard_predicates[del_id]
                        new_collection = []
                        for single_pred in self.standard_alt_predicates_imp:
                            if not (isinstance(single_pred[0], WeinhuberApproachSplit) and single_pred[0].id == real_parent_id):
                                new_collection.append(single_pred)
                        self.standard_alt_predicates_imp = new_collection

                    elif del_id < len(self.standard_predicates) + len(self.recently_added_predicates):
                        real_parent_id = self.recently_added_predicates[del_id - len(self.standard_predicates)].id
                        del self.recently_added_predicates[del_id - len(self.standard_predicates)]
                        new_collection = []
                        for single_pred in self.recently_added_predicates_imp:
                            if not (isinstance(single_pred[0], WeinhuberApproachSplit) and single_pred[0].id == real_parent_id):
                                new_collection.append(single_pred)
                        self.recently_added_predicates_imp = new_collection
                    else:
                        print("Invalid Id.")
                self.console_output(dataset)
            elif input_line == "/collection":
                # display the collections of predicates
                self.print_predicate_collections()
            elif input_line == "/refresh":
                # refresh the console output --> prints everything again
                self.console_output(dataset)
            else:
                print("Unknown command. Type '/help' for help.")

    def print_predicate_collections(self):
        """
        Function to give a visual representation of the predicates collection.
        """
        header = ["ID", "TERM", "COLUMN INTERVAL", "COEF INTERVAL"]

        # Print standard and alternative collection
        table_standard = [[i, str(self.standard_predicates[i].term) + " " + self.standard_predicates[i].relation + " 0",
                           self.standard_predicates[i].column_interval, self.standard_predicates[i].coef_interval] for i in
                          range(len(self.standard_predicates))]
        print("\n\t\t\t\t\t\tSTANDARD PREDICATES\n" + tabulate(table_standard, header, tablefmt="psql") + "\n")

        # Print standard and alternative collection
        table_recently_added = [[i + len(self.standard_predicates),
                                 str(self.recently_added_predicates[i].term) + " " + self.recently_added_predicates[i].relation + " 0",
                                 self.recently_added_predicates[i].column_interval, self.recently_added_predicates[i].coef_interval] for i
                                in
                                range(len(self.recently_added_predicates))]
        # Print recently added collection
        print("\n\t\t\t\t\t\tRECENTLY ADDED PREDICATES\n" + tabulate(table_recently_added, header, tablefmt="psql") + "\n")

    def user_double_check_del(self):
        """
        Function to double check whether user really wants to delete a predicate.
        :returns: Bool
        """
        print("Are you sure, you want to delete that predicate? Remember that you will delete the predicate from the collection."
              "\nPlease enter y/n")
        for input_line in sys.stdin:
            input_line = input_line.strip()
            if input_line == "y" or input_line == "yes":
                return True
            elif input_line == "n" or input_line == "no":
                return False
            else:
                print("Unkown command. Please enter y/n")

    def user_double_check_inf(self, users_choice):
        """
        Function to double check whether user really wants to return a split with impurity inf
        :param users_choice: (Predicate, Impurity)
        :returns: Bool
        """
        user_split, imp = users_choice
        if imp < np.inf:
            return True
        else:
            # ARE YOU SURE - loop
            print("Are you sure, that you want to return a split with impurity of INFINITY ?\nPlease enter y/n")
            for input_line in sys.stdin:
                input_line = input_line.strip()
                if input_line == "y" or input_line == "yes":
                    return True
                elif input_line == "n" or input_line == "no":
                    return False
                else:
                    print("Unkown command. Please enter y/n")

    def process_standard_alt_predicates(self, dataset, impurity_measure):
        """
        Function to setup standard_alt_predicates_imp for future usage.
        :param dataset: the subset of data at the current 'situation'
        :param impurity_measure: impurity measure to use
        :returns: None. --> Sets up self.standard_alt_predicates_imp

        self.standard_alt_predicates_imp
        --> List containing Tuple: [(Predicate, impurity)]

        Contains the 'fitted' instances of its corresponding predicate collection --> (self.standard_predicates)
        AND alternative_strategies predicates

        Procedure:
            1. All predicates inside self.standard_predicates get fit and checked
            2. Add additional alternative splitting strategies:
                2.1 Axis Aligned
                2.2 Linear Basic
                2.3 If Units available: Linear with Unit respect
            3. Sort self.standard_alt_predicates_imp
        """
        all_predicates = self.get_all_weinhub_splits(self.standard_predicates, dataset, impurity_measure)
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
        :param dataset: the subset of data at the current 'situation'
        :param impurity_measure: impurity measure to use
        :returns: None. --> Sets up self.recently_added_predicates_imp

        self.recently_added_predicates_imp
        --> List containing Tuple: [(Predicate, impurity)]

        contains predicates added by user via user_input_handler() --> '/add <Predicate>'

        Procedure:
            1. All predicates inside self.recently_added_predicates get fit and checked
            2. Sort self.standard_alt_predicates_imp
        """
        all_predicates = self.get_all_weinhub_splits(self.recently_added_predicates, dataset, impurity_measure)
        self.recently_added_predicates_imp = list(all_predicates.items())
        self.recently_added_predicates_imp.sort(key=lambda x: x[1])

    def find_split(self, dataset, impurity_measure):

        """
        :param dataset: the subset of data at the current split
        :param impurity_measure: impurity measure to use
        :returns: split object

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
        return_split = self.user_input_handler(dataset, impurity_measure)

        self.logger.root_logger.info("Returned split: {}".format(str(return_split)))
        return return_split

    def index_predicate_mapping(self, index):
        """
        Function to map an index to the corresponding predicate.
        Double checks if user want to return split with impurity of inf.
        :param index: Integer. Index of predicate as displayed in the console output.
        :returns: Split Object at index
        """
        if index < len(self.standard_alt_predicates_imp):
            return self.standard_alt_predicates_imp[index]
        else:
            return self.recently_added_predicates_imp[index - len(self.standard_alt_predicates_imp)]

    def console_output(self, dataset):
        """
        Function to print out the visual representation to the console.
        :param dataset: the subset of data at the current 'situation'
        :returns: None --> Console output
        """

        self.print_dataset_specs(dataset)
        self.print_standard_alt_predicates()
        self.print_recently_added_predicates()
        print("\nSTARTING INTERACTIVE SHELL. PLEASE ENTER YOUR COMMANDS. TYPE '/help' FOR HELP.\n")
