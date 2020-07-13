from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit
import re
import sympy as sp
from sympy.core.function import AppliedUndef
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_exceptions import WeinhuberPredicateParserException
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_logger import WeinhuberApproachLogger


class PredicateParser:

    @classmethod
    def get_predicate(cls, debug=False, input_file_path=r"dtcontrol/decision_tree/splitting/context_aware/input_data/input_predicates.txt"):
        """
        Function to parse predicates obtained from user (stored in input_file_path)
        :param input_file_path: path with file containing user predicates (in every line one predicate)
        :returns: List of WeinhuberApproachSplit Objects

        e.g.
        Input_line:  c_1 * x_1 - c_2 + x_2 - c_3  <= 0; x_2 in {1,2,3}; c_1 in (-inf, inf); c_2 in {1,2,3}; c_3 in {5, 10, 32, 40}
        Output: WeinhuberApproachSplit Object with:

        column_interval     =       {x_1:(-Inf,Inf), x_2:{1,2,3}}                           --> Key: Sympy Symbol Value: Sympy Interval
        coef_interval       =       {c_1:(-Inf,Inf), c_2:{1,2,3}, c_3:{5,10,32,40}          --> Key: Sympy Symbol Value: Sympy Interval
        term                =       c_1 * x_1 - c_2 + x_2 - c_3                             --> sympy expression
        relation            =       '<='                                                    --> String

        Every symbol without a specific defined Interval will be assigned to the interval: (-Inf, Inf)

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
        # Logger Init
        logger = WeinhuberApproachLogger("PredicateParser_logger", debug)
        logger.root_logger.info("Starting Predciate Parser.")

        # Opening and checking the input file
        try:
            with open(input_file_path, "r") as file:
                input_line = [predicate.rstrip() for predicate in file]
        except FileNotFoundError:
            logger.root_logger.critical("Aborting: input file with user predicate(s) not found. Please check input file/path.")
            raise WeinhuberPredicateParserException()

        # Edge Case user input == ""
        if not input_line:
            logger.root_logger.critical("Aborting: input file with user predicates is empty. Please check file.")
            raise WeinhuberPredicateParserException()
        else:
            logger.root_logger.info(
                "Reading input file containing predicate(s) given by user. Found {} predicate(s).".format(len(input_line)))

        # Currently supported types of relations
        supported_relation = ["<=", ">=", "<", ">", "="]

        # output list containing all parsed predicates
        output = []
        for single_predicate in input_line:
            logger.root_logger.info("Processing user predicate {} / {}.".format(input_line.index(single_predicate) + 1, len(input_line)))
            for relation in supported_relation:
                if relation in single_predicate:
                    # Deleting additional semi colon at the end
                    if single_predicate[-1] == ";":
                        single_predicate = single_predicate[:-1]
                    try:
                        # Cutting the input into separate strings. The first one should contain the term. The rest should be intervals
                        split_pred = single_predicate.split(";")
                        split_term = split_pred[0].split(relation)
                        term = sp.sympify(split_term[0] + "-(" + split_term[1] + ")")
                    except Exception:
                        logger.root_logger.critical(
                            "Aborting: one predicate does not have a valid structure. Invalid predicate: {}. Please check for typos and read the comments inside predicate_parser.py. For more information take a look at the sympy library (https://docs.sympy.org/latest/tutorial/basic_operations.html#converting-strings-to-sympy-expressions).".format(
                                str(single_predicate)))
                        raise WeinhuberPredicateParserException()

                    all_interval_defs = {}
                    column_interval = {}
                    coef_interval = {}

                    # Parsing all additional given intervals and storing them inside --> all_interval_defs
                    try:
                        for i in range(1, len(split_pred)):
                            split_coef_definition = split_pred[i].split("in", 1)
                            interval = cls.parse_user_interval(split_coef_definition[1], debug)
                            symbol = sp.sympify(split_coef_definition[0])
                            all_interval_defs[symbol] = interval
                    except Exception:
                        logger.root_logger.critical(
                            "Aborting: one predicate does not have a valid structure. Invalid predicate: {}. Please check for typos and read the comments inside predicate_parser.py. For more information take a look at the sympy library (https://docs.sympy.org/latest/tutorial/basic_operations.html#converting-strings-to-sympy-expressions).".format(
                                str(single_predicate)))
                        raise WeinhuberPredicateParserException()

                    """
                    ----------------    !!!!!!!!!!!!!!!!    C A U T I O N    !!!!!!!!!!!!!!!!   ----------------
                    |                  COLUMN REFERENCING ONLY WITH VARIABLES OF STRUCTURE: x_i                |
                    |                  COEFS ONLY WITH VARIABLES OF STRUCTURE: c_j                             |
                    --------------------------------------------------------------------------------------------
                    """
                    # Iterating over every symbol/variable and deciding whether it is a column reference or a coef
                    infinity = sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)
                    for var in term.free_symbols:
                        # Type: x_i -> column reference
                        if re.match(r"x_\d+", str(var)):
                            if not all_interval_defs.__contains__(var):
                                column_interval[var] = infinity
                            else:
                                column_interval[var] = all_interval_defs[var]
                                all_interval_defs.__delitem__(var)
                        # Type: c_i --> coef
                        elif re.match(r"c_\d+", str(var)):
                            if not all_interval_defs.__contains__(var):
                                coef_interval[var] = infinity
                            else:
                                # CHECKING: coefs are only allowed to have 2 kinds of intervals: FiniteSet or (-Inf,Inf)
                                check_interval = all_interval_defs[var]
                                all_interval_defs.__delitem__(var)
                                if isinstance(check_interval, sp.FiniteSet) or check_interval == infinity:
                                    coef_interval[var] = check_interval
                                else:
                                    # coef interval is not FiniteSet or (-Inf,Inf)
                                    logger.root_logger.critical(
                                        "Aborting: invalid interval for a coefficient declared. Only finite or (-Inf,Inf) allowed. Coefficient: {} with invalid interval: {} from predicate: {}".format(
                                            str(var), str(check_interval), str(single_predicate)))
                                    raise WeinhuberPredicateParserException()
                        else:
                            logger.root_logger.critical(
                                "Aborting: one symbol inside one predicate does not have a valid structure. Column refs only with x_i. Coefs only with c_i. Invalid symbol: {} inside predicate {}".format(
                                    str(var), str(single_predicate)))
                            raise WeinhuberPredicateParserException()

                    # Checking if every interval-Definition, actually occurs in in the term.
                    # e.g. x_0 <= c_0; c_5 in {1}  --> c_5 doesn't even occur in the term.
                    if all_interval_defs:
                        logger.root_logger.critical(
                            "Aborting: invalid symbol in interval definition without symbol usage in the term found. Invalid symbol(s): {} inside predicate: {}".format(
                                str(all_interval_defs), str(single_predicate)))
                        raise WeinhuberPredicateParserException()

                    # Hidden edge cases which may occured:

                    # Hidden edge case1: Undefined functions.
                    # e.g. f(x) * c1 * x_3 >= 1 <--> f(x) is an undefined function.
                    if term.atoms(AppliedUndef):
                        logger.root_logger.critical(
                            "Aborting: one predicate contains an undefined function. Undefined function: {}. Invalid predicate: {}".format(
                                str(term.atoms(AppliedUndef)), str(single_predicate)))
                        raise WeinhuberPredicateParserException()
                    # Hidden edge case2: No symbols to reference columns used.
                    # e.g. c_0 >= 1; c_0 in {5,7}
                    elif not column_interval:
                        logger.root_logger.critical(
                            "Aborting: one predicate does not contain variables to reference columns. Invalid predicate: ".format(
                                str(single_predicate)))
                        raise WeinhuberPredicateParserException()
                    # Hidden edge case3: Term evaluates to zero.
                    # e.g. 3-1.5*2 <= 0
                    elif term == 0 or term.evalf() == 0:
                        logger.root_logger.critical(
                            "Aborting: one predicate does evaluate to zero. Invalid predicate: ".format(str(single_predicate)))
                        raise WeinhuberPredicateParserException()
                    # Hidden edge case4: Invalid states for important key variables reached.
                    elif not split_pred or not term or not column_interval:
                        logger.root_logger.critical("Aborting: one predicate does not have a valid structure. Invalid predicate: ".format(
                            str(single_predicate)))
                        raise WeinhuberPredicateParserException()

                    parsed_predicate = WeinhuberApproachSplit(column_interval, coef_interval, term, relation, debug)
                    logger.root_logger.info(
                        "Parsed predicate {} / {} successfully. Result: {}".format(input_line.index(single_predicate) + 1,
                                                                                   len(input_line), str(parsed_predicate)))
                    output.append(parsed_predicate)
                    break

        logger.root_logger.info("Finished processing of user predicate. Shutting down Predicate Parser")
        return output

    @classmethod
    def parse_user_interval(cls, user_input, debug = False):
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
        # Logger init
        logger = WeinhuberApproachLogger("PredicateParser_UserInterval_logger", debug)

        logger.root_logger.info("User interval started processing: {}".format(user_input))

        # simplest special case:
        if user_input == "$i":
            return sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)

        # super basic beginning and end char check of whole input
        if not user_input.strip():
            logger.root_logger.critical("Aborting: no interval found.")
            raise WeinhuberPredicateParserException()
        elif user_input.strip()[0] is not "{" and user_input.strip()[0] is not "(" and user_input.strip()[0] is not "[":
            logger.root_logger.critical("Aborting: interval starts with an invalid char. Invalid interval: {}".format(user_input))
            raise WeinhuberPredicateParserException()
        elif user_input.strip()[-1] is not "}" and user_input.strip()[-1] is not ")" and user_input.strip()[
            -1] is not "]":
            logger.root_logger.critical("Aborting: interval ends with an invalid char. Invalid interval: {}".format(user_input))
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
                            logger.root_logger.critical("Aborting: invalid member found. Invalid interval: {}".format(user_input))
                            raise WeinhuberPredicateParserException()
                        if tmp == sp.nan:
                            logger.root_logger.critical("Aborting: invalid NaN member found. Invalid interval: {}".format(user_input))
                            raise WeinhuberPredicateParserException()
                        elif tmp == sp.S.Infinity or tmp == sp.S.NegativeInfinity:
                            logger.root_logger.critical("Aborting: infinity is an invalid member. Invalid interval: {}".format(user_input))
                            raise WeinhuberPredicateParserException()
                        elif isinstance(tmp, sp.Number):
                            checked_members.append(tmp)
                        else:
                            logger.root_logger.critical(
                                "Aborting: Invalid member found in finite interval. Invalid member: {} Invalid interval: {}".format(
                                    str(tmp), user_input))
                            raise WeinhuberPredicateParserException()
                    # Edge case: if no member is valid --> empty set will be returned.
                    out = sp.FiniteSet(*checked_members)
                    if out == sp.EmptySet:
                        logger.root_logger.critical("Aborting: Invalid empty interval found. Invalid interval: {}".format(user_input))
                        raise WeinhuberPredicateParserException()
                    else:
                        interval_list.append(out)
                else:
                    # Interval starts with { but does not end with }
                    logger.root_logger.critical("Aborting: Invalid char at end of interval found. Invalid interval: {}".format(user_input))
                    raise WeinhuberPredicateParserException()
            elif interval[0] == "(" or interval[0] == "[":
                # normal intervals of structure (1,2] etc

                # Checking of first char
                if interval[0] == "(":
                    left_open = True
                elif interval[0] == "[":
                    left_open = False
                else:
                    logger.root_logger.critical("Aborting: interval starts with an invalid char. Invalid interval: {}".format(user_input))
                    raise WeinhuberPredicateParserException()
                # Checking boundaries of interval
                tmp = interval[1:-1].split(",")
                if len(tmp) > 2:
                    logger.root_logger.critical("Aborting: too many numbers inside an interval. Invalid interval: {}".format(user_input))
                    raise WeinhuberPredicateParserException()
                try:
                    a = sp.sympify(tmp[0]).evalf()
                    b = sp.sympify(tmp[1]).evalf()
                    if a == sp.nan or b == sp.nan:
                        logger.root_logger.critical(
                            "Aborting: invalid NaN interval boundary found. Invalid interval: {}".format(user_input))
                        raise WeinhuberPredicateParserException()
                except Exception:
                    logger.root_logger.critical("Aborting: Invalid member found inside interval. Invalid interval: {}".format(user_input))
                    raise WeinhuberPredicateParserException()
                else:
                    if isinstance(a, sp.Number) and isinstance(b, sp.Number):
                        # Checking of last char
                        if interval[-1] == ")":
                            right_open = True

                        elif interval[-1] == "]":
                            right_open = False
                        else:
                            logger.root_logger.critical(
                                "Aborting: interval ends with an invalid char. Invalid interval: {}".format(user_input))
                            raise WeinhuberPredicateParserException()
                        out = sp.Interval(a, b, right_open=right_open, left_open=left_open)
                        if out == sp.EmptySet:
                            logger.root_logger.critical("Aborting: Invalid empty interval found. Invalid interval: {}".format(user_input))
                            raise WeinhuberPredicateParserException()
                        else:
                            interval_list.append(out)
                    else:
                        logger.root_logger.critical(
                            "Aborting: Invalid member found inside interval. Invalid interval: {}".format(user_input))
                        raise WeinhuberPredicateParserException()
            else:
                logger.root_logger.critical("Aborting: Invalid char found inside interval. Invalid interval: {}".format(user_input))
                raise WeinhuberPredicateParserException()

        # Union
        final_interval = interval_list[0]

        # union with all other intervals
        if len(interval_list) > 1:
            for item in interval_list:
                final_interval = sp.Union(final_interval, item)
        logger.root_logger.info("Finished processing user interval: {}. Result: {}.".format(user_input, str(final_interval)))
        return final_interval
