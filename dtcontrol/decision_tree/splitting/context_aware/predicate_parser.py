from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit
import logging
import re
import sympy as sp
from sympy.core.function import AppliedUndef
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_exceptions import WeinhuberPredicateParserException


def _logger_setup():
    logger = logging.getLogger("PredicateParser_logger")
    logger.setLevel(logging.CRITICAL)

    # Uncomment following lines to create a logger file containing all messages with timestamps.
    # (Remember to change logger.setLevel(logging.DEBUG)

    # formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    # file_handler = logging.FileHandler('PredicateParser_logger.log')
    # file_handler.setFormatter(formatter)
    # file_handler.setLevel(logging.DEBUG)
    # logger.addHandler(file_handler)

    return logger


class PredicateParser:
    _logger = _logger_setup()

    @classmethod
    def get_predicate(cls, input_file_path=r"dtcontrol/decision_tree/splitting/context_aware/input_data/input_predicates.txt"):
        """
        Function to parse predicates obtained from user (stored in input_file_path)
        :param input_file_path: path with file containing user predicates (in every line one predicate)
        :returns: List of WeinhuberApproachSplit Objects

        e.g.
        Input_line:  c_1 * x_3 - c_2 + x_4 - c_3 <= 0; x_2 in {1,2,3}; c_1 in (-inf, inf); c_2 in {1,2,3}; c_3 in {5, 10, 32, 40}
        Output: WeinhuberApproachSplit Object with:

        column_interval     =       {x_1:(-Inf,Inf), x_2:{1,2,3}}                           --> Key: Sympy Symbol Value: Sympy Interval
        coef_interval       =       {c_1:(-Inf,Inf), c_2:{1,2,3}, c_3:{5,10,32,40}          --> Key: Sympy Symbol Value: Sympy Interval
        term                =       c_1 * x_3 - c_2 + x_4 - c_3                             --> sympy expression
        relation            =       '<='                                                    --> String

        EDGE CASE BEHAVIOR:
        Every column reference or coef without a specific defined Interval will be assigned this interval: (-Inf, Inf)
        Allowed interval types for columns: All (expect Empty Set)
        Allowed interval types for coef: Finite or (-Inf,Inf)

        In case the predicate obtained from the user has following structure:

        x_1     <=          5       (5 != 0)
        term    relation    bias    (with bias != 0)

        the whole predicate will be transferred to following structure:

        x_1 - 5         <=          0
        term - bias     relation    0


        ----------------    !!!!!!!!!!!!!!!!    C A U T I O N    !!!!!!!!!!!!!!!!   ----------------
        |                  COLUMN REFERENCING ONLY WITH VARIABLES OF STRUCTURE: x_i                |
        |                  COEFS ONLY WITH VARIABLES OF STRUCTURE: c_j                             |
        --------------------------------------------------------------------------------------------

        """

        try:
            with open(input_file_path, "r") as file:
                input_line = [predicate.rstrip() for predicate in file]
                cls._logger.info("Reading input file containing predicate(s) given by user. Found {} predicate(s).".format(len(input_line)))
        except FileNotFoundError:
            cls._logger.critical("Aborting: input file with user predicate(s) not found. Please check path.")
            raise WeinhuberPredicateParserException()

        # Edge Case user input == ""
        if not input_line:
            cls._logger.critical("Aborting: input file with user predicates is empty. Please check file.")
            raise WeinhuberPredicateParserException()

        # Currently supported types of relations
        supported_relation = ["<=", ">=", "<", ">", "="]

        # output list containing all predicates parsed in tuple form
        output = []
        for single_predicate in input_line:
            cls._logger.info("Processing user predicate {} / {}.".format(input_line.index(single_predicate) + 1, len(input_line)))
            for relation in supported_relation:
                if relation in single_predicate:
                    try:
                        # Deleting additional semi colon at the end
                        if single_predicate[-1] == ";":
                            single_predicate = single_predicate[:-1]
                        # Cutting the input into separate parts
                        split_pred = single_predicate.split(";")
                        split_term = split_pred[0].split(relation)
                        term = sp.sympify(split_term[0] + "-(" + split_term[1] + ")")
                        all_interval_defs = {}
                        column_interval = {}
                        coef_interval = {}

                        # Parsing all additional given intervals and storing them inside --> all_interval_defs
                        for i in range(len(split_pred) - 1):
                            split_coef_definition = split_pred[i + 1].split("in", 1)
                            interval = cls.parse_user_interval(split_coef_definition[1])
                            if interval == sp.EmptySet:
                                cls._logger.critical(
                                    "Aborting: an empty interval has been found. Invalid interval: {}".format(str(interval)))
                                raise WeinhuberPredicateParserException()
                            else:
                                all_interval_defs[sp.sympify(split_coef_definition[0])] = interval

                        """
                        ----------------    !!!!!!!!!!!!!!!!    C A U T I O N    !!!!!!!!!!!!!!!!   ----------------
                        |                  COLUMN REFERENCING ONLY WITH VARIABLES OF STRUCTURE: x_i                |
                        |                  COEFS ONLY WITH VARIABLES OF STRUCTURE: c_j                             |
                        --------------------------------------------------------------------------------------------
                        """
                        # Iterating over every symbol/variable and deciding whether it is a column reference or a coef
                        for var in term.free_symbols:
                            if re.match(r"x_\d+", str(var)):
                                if not all_interval_defs.__contains__(var):
                                    column_interval[var] = sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)
                                else:
                                    column_interval[var] = all_interval_defs[var]
                                    all_interval_defs.__delitem__(var)
                            elif re.match(r"c_\d+", str(var)):
                                if not all_interval_defs.__contains__(var):
                                    coef_interval[var] = sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)
                                else:
                                    # CHECKING: coefs are only allowed to have 2 kinds of intervals: FiniteSet or (-Inf,Inf)
                                    check_interval = all_interval_defs[var]
                                    all_interval_defs.__delitem__(var)
                                    infinity = sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)
                                    if isinstance(check_interval, sp.FiniteSet) or check_interval == infinity:
                                        coef_interval[var] = check_interval
                                    else:
                                        cls._logger.critical(
                                            "Aborting: invalid interval for a coefficient declared. Only finite or (-Inf,Inf) allowed. Coefficient: {} with invalid interval: {} from predicate: {}".format(
                                                str(var), str(check_interval), str(single_predicate)))
                                        raise WeinhuberPredicateParserException()
                            else:
                                cls._logger.critical(
                                    "Aborting: one symbol inside one predicate does not have a valid structure. Invalid symbol: {} inside predicate {}".format(
                                        str(var), str(single_predicate)))
                                raise WeinhuberPredicateParserException()
                        # Checking if every (symbol in interval)-Definition, occurs in in the term.
                        # e.g. x_0 <= c_0; c_5 in {1}  --> c_5 doesn't even occur in the term
                        if all_interval_defs:
                            cls._logger.critical(
                                "Aborting: invalid symbol in interval definition without symbol usage in the term found. Invalid symbol(s): {} inside predicate: {}".format(
                                    str(all_interval_defs), str(single_predicate)))
                            raise WeinhuberPredicateParserException()
                    except Exception:
                        cls._logger.critical(
                            "Aborting: one predicate does not have a valid structure. Invalid predicate: {}. Please check for typos and read the comments inside predicate_parser.py. For more information take a look at the sympy library (https://docs.sympy.org/latest/tutorial/basic_operations.html#converting-strings-to-sympy-expressions).".format(
                                str(single_predicate)))
                        raise WeinhuberPredicateParserException()
                    else:
                        # Checking valid structure of predicate
                        if term.atoms(AppliedUndef):
                            # e.g. f(x) * c1 * x_3 >= 1 --> f(x) is an undefined function <--- NOT ALLOWED!
                            cls._logger.critical(
                                "Aborting: one predicate contains an undefined function. Undefined function: {}. Invalid predicate: {}".format(
                                    str(term.atoms(AppliedUndef)), str(single_predicate)))
                            raise WeinhuberPredicateParserException()
                        elif not column_interval:
                            cls._logger.critical(
                                "Aborting: one predicate does not contain variables to reference columns. Invalid predicate: ".format(
                                    str(single_predicate)))
                            raise WeinhuberPredicateParserException()
                        elif term == 0 or term.evalf() == 0:
                            cls._logger.critical(
                                "Aborting: one predicate does evaluate to zero. Invalid predicate: ".format(str(single_predicate)))
                            raise WeinhuberPredicateParserException()
                        elif not split_pred or not term or not column_interval:
                            cls._logger.critical("Aborting: one predicate does not have a valid structure. Invalid predicate: ".format(
                                str(single_predicate)))
                            raise WeinhuberPredicateParserException
                        else:
                            parsed_predicate = WeinhuberApproachSplit(column_interval, coef_interval, term, relation)
                            cls._logger.info(
                                "Parsed predicate {} / {} successfully. Result: {}".format(input_line.index(single_predicate) + 1,
                                                                                           len(input_line), str(parsed_predicate)))
                            output.append(parsed_predicate)
                    break

        cls._logger.info("Finished processing of user predicate.")
        return output

    @classmethod
    def parse_user_interval(cls, user_input):
        """
        Predicate Parser for the interval.
        :variable user_input: Interval as a string
        :returns: a sympy expression (to later use in self.interval of ContextAwareSplit objects)

        Option 1: user_input = (-oo, oo) = [-oo, oo]
        --> self.offset of ContextAwareSplit will be the value to achieve the 'best' impurity

        (with a,b ∊ R)
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
        --> Union of intervals


        Grammar G for an user given interval:

        G = (V, Σ, P, predicate)
        V = {predicate, combination, interval, real_interval, bracket_left, bracket_right, number, finite_interval, number_finit, num}
        Σ = { (, [, ), ], R, +oo, -oo, ,, ∪, -Inf, Inf, -INF, INF, -inf, inf, or, Or, OR, u}
        P:
        PREDICATE       -->     INTERVAL | INTERVAL ∪ COMBINATION
        INTERVAL        -->     REAL_INTERVAL | FINITE_INTERVAL
        REAL_INTERVAL   -->     BRACKET_LEFT NUMBER , NUMBER BRACKET_RIGHT
        BRACKET_LEFT    -->     ( | [
        BRACKET_RIGHT   -->     ) | ]
        NUMBER          -->     {x | x ∊ R} | +oo | -oo
        FINITE_INTERVAL -->     {NUMBER_FINITE NUM}
        NUMBER_FINITE   -->     {x | x ∊ R}
        NUM             -->     ,NUMBER_FINITE | ,NUMBER_FINITE NUM

        """
        cls._logger.info("User interval started processing: {}".format(user_input))

        # simplest special case:
        if user_input == "$i":
            return sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)

        # super basic beginning and end char check of whole input
        if not user_input.strip():
            cls._logger.critical("Aborting: no interval found.")
            raise WeinhuberPredicateParserException()
        elif user_input.strip()[0] is not "{" and user_input.strip()[0] is not "(" and user_input.strip()[0] is not "[":
            cls._logger.critical("Aborting: interval starts with an invalid char. Invalid interval: {}".format(user_input))
            raise WeinhuberPredicateParserException()
        elif user_input.strip()[-1] is not "}" and user_input.strip()[-1] is not ")" and user_input.strip()[
            -1] is not "]":
            cls._logger.critical("Aborting: interval ends with an invalid char. Invalid interval: {}".format(user_input))
            raise WeinhuberPredicateParserException()

        user_input = user_input.lower()
        # Modify user_input and convert every union symbol/word into "∪" <-- ASCII Sign for Union not letter U
        user_input = user_input.replace("or", "∪")
        user_input = user_input.replace("u", "∪")

        # Modify user_input and convert every "Inf" to sympy supported symbol for infinity "oo"
        user_input = user_input.replace("inf", "oo")
        user_input = user_input.replace("infinity", "oo")

        # appending all intervals into this list and later union all of them
        interval_list = []

        user_input = user_input.split("∪")
        user_input = [x.strip() for x in user_input]

        # Parsing of every single interval
        for interval in user_input:
            """
            Basic idea: Evaluate/Parse every single predicate and later union them (if needed)
            Path is chosen based on first char of interval
            possible first char of an interval:
                --> {
                --> ( or [ (somehow belong to the same "family")

            """

            if interval[0] == "{":
                # finite intervals like {1,2,3}
                if interval[-1] == "}":
                    unchecked_members = interval[1:-1].split(",")
                    # Check each member whether they are valid
                    checked_members = []
                    for var in unchecked_members:
                        try:
                            tmp = sp.sympify(var).evalf()
                        except Exception:
                            cls._logger.critical("Aborting: invalid member found. Invalid interval: {}".format(user_input))
                            raise WeinhuberPredicateParserException()
                        if tmp == sp.nan:
                            cls._logger.critical("Aborting: invalid NaN member found. Invalid interval: {}".format(user_input))
                            raise WeinhuberPredicateParserException()
                        elif tmp == sp.S.Infinity or tmp == sp.S.NegativeInfinity:
                            cls._logger.critical("Aborting: infinity is an invalid member. Invalid interval: {}".format(user_input))
                            raise WeinhuberPredicateParserException()
                        elif isinstance(tmp, sp.Number):
                            checked_members.append(tmp)
                        else:
                            cls._logger.critical(
                                "Aborting: Invalid member found in finite interval. Invalid member: {} Invalid interval: {}".format(
                                    str(tmp), user_input))
                            raise WeinhuberPredicateParserException()
                    # Edge case: if no member is valid --> empty set will be returned.
                    out = sp.FiniteSet(*checked_members)
                    if out == sp.EmptySet:
                        cls._logger.critical("Aborting: Invalid empty interval found. Invalid interval: {}".format(user_input))
                        raise WeinhuberPredicateParserException()
                    else:
                        interval_list.append(out)
                else:
                    # Interval starts with { but does not end with }
                    cls._logger.critical("Aborting: Invalid char at end of interval found. Invalid interval: {}".format(user_input))
                    raise WeinhuberPredicateParserException()
            elif interval[0] == "(" or interval[0] == "[":
                # normal intervals of structure (1,2] etc

                # Checking of first char
                if interval[0] == "(":
                    left_open = True
                elif interval[0] == "[":
                    left_open = False
                else:
                    cls._logger.critical("Aborting: interval starts with an invalid char. Invalid interval: {}".format(user_input))
                    raise WeinhuberPredicateParserException()
                # Checking boundaries of interval
                tmp = interval[1:-1].split(",")
                if len(tmp) > 2:
                    cls._logger.critical("Aborting: too many numbers inside an interval. Invalid interval: {}".format(user_input))
                    raise WeinhuberPredicateParserException()
                try:
                    a = sp.sympify(tmp[0]).evalf()
                    b = sp.sympify(tmp[1]).evalf()
                    if a == sp.nan or b == sp.nan:
                        cls._logger.critical("Aborting: invalid NaN interval boundary found. Invalid interval: {}".format(user_input))
                        raise WeinhuberPredicateParserException()
                except Exception:
                    cls._logger.critical("Aborting: Invalid member found inside interval. Invalid interval: {}".format(user_input))
                    raise WeinhuberPredicateParserException()
                else:
                    if isinstance(a, sp.Number) and isinstance(b, sp.Number):
                        # Checking of last char
                        if interval[-1] == ")":
                            right_open = True

                        elif interval[-1] == "]":
                            right_open = False
                        else:
                            cls._logger.critical("Aborting: interval ends with an invalid char. Invalid interval: {}".format(user_input))
                            raise WeinhuberPredicateParserException()
                        out = sp.Interval(a, b, right_open=right_open, left_open=left_open)
                        if out == sp.EmptySet:
                            cls._logger.critical("Aborting: Invalid empty interval found. Invalid interval: {}".format(user_input))
                            raise WeinhuberPredicateParserException()
                        else:
                            interval_list.append(out)
                    else:
                        cls._logger.critical("Aborting: Invalid member found inside interval. Invalid interval: {}".format(user_input))
                        raise WeinhuberPredicateParserException()
            else:
                cls._logger.critical("Aborting: Invalid char found inside interval. Invalid interval: {}".format(user_input))
                raise WeinhuberPredicateParserException()

        # Union
        final_interval = interval_list[0]

        # union with all other intervals
        if len(interval_list) > 1:
            for item in interval_list:
                final_interval = sp.Union(final_interval, item)
        cls._logger.info("Finished processing user interval: {}. Result: {}.".format(user_input, str(final_interval)))
        return final_interval
