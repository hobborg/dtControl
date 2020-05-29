from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_split import WeinhuberApproachSplit
import logging
import re
import sympy as sp
from sympy.core.function import AppliedUndef


class PredicateParser:

    @classmethod
    def _logger(cls):
        logger = logging.getLogger("PredicateParser_logger")
        logger.setLevel(logging.ERROR)
        return logger

    @classmethod
    def get_predicate(cls, input_file_path=r"dtcontrol/decision_tree/splitting/context_aware/input_data/input_predicates.txt"):

        """
        Predicate parser for predicates obtained from user
        :returns: list of WeinhuberApproachSplit Objects representing all predicates obtained from the user

        e.g.
        Input:  c1 * x_3 - c2 + x_4 - c3 <= 0; x_2 in {1,2,3}; c1 in (-inf, inf); c2 in {1,2,3}; c3 in {5, 10, 32, 40}
        Output: WeinhuberApproachSplit Object with:

        column_interval     =       {x_1:(-Inf,Inf), x_2:{1,2,3}}                   --> Key: Sympy Symbol Value: Sympy Interval
        Every column reference without a specific defined Interval will be assigned to (-Inf, Inf)
        coef_interval       =       {c1:(-Inf,Inf), c2:{1,2,3}, c3:{5,10,32,40}     --> Key: Sympy Symbol Value: Sympy Interval
        term                =       c1 * x_3 - c2 + x_4 - c3                        --> sympy expression
        relation            =       '<='                                            --> String

        In case the predicate obtained from an user has following structure:
        term <= bias (with bias != 0)

        The whole predicate will be transferred to following structure:
        term - bias <= 0

        TODO: Referencing columns with direct column name
        Column Referenciation:
        - Currently only allowing x_1, x_2, ...
            --> Will be checked in find_split if x_i really references a valid column
        Coef:
        - Currently allowing "almost everything", expect already reserved expr like x_i, sqrt(2), ...

        """

        try:
            with open(input_file_path, "r") as file:
                input_line = [predicate.rstrip() for predicate in file]
        except FileNotFoundError:
            cls._logger().warning("Aborting: input file with user predicates not found.")
            return

        # Edge Case user input == ""
        if not input_line:
            cls._logger().warning("Aborting: input file with user predicates is empty.")
            return

        # Currently supported types of relations
        supported_relation = ["<=", ">=", "!=", "<", ">", "="]

        # output list containing all predicates parsed in tuple form
        output = []
        for single_predicate in input_line:
            for relation in supported_relation:
                if relation in single_predicate:
                    try:
                        split_pred = single_predicate.split(";")
                        split_term = split_pred[0].split(relation)

                        term = sp.sympify(split_term[0] + "-(" + split_term[1] + ")")
                        coef_interval = {}
                        column_interval = {}

                        for i in range(len(split_pred) - 1):
                            split_coef_definition = split_pred[i + 1].split("in", 1)
                            interval = cls.parse_user_interval(split_coef_definition[1])
                            if interval == sp.EmptySet:
                                cls._logger().warning("Aborting: one coefficient is an empty set."
                                                      "Invalid interval: ", str(interval))
                                return
                            else:
                                coef_interval[sp.sympify(split_coef_definition[0])] = interval
                        # Currently only allowing x_ for column referenciation
                        for var in term.free_symbols:
                            if re.match(r"x_\d+", str(var)):
                                if not coef_interval.__contains__(var):
                                    column_interval[var] = sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)
                                else:
                                    column_interval[var] = coef_interval[var]
                                    coef_interval.__delitem__(var)



                    except IndentationError:
                        cls._logger().warning("Aborting: one predicate does not have a valid structure."
                                              "Invalid predicate: ", str(single_predicate))
                        return
                    else:
                        # Checking valid structure of predicate
                        if term.atoms(AppliedUndef):
                            # e.g. f(x) * c1 * x_3 >= 1 --> f(x) is an undefined function
                            cls._logger().warning("Aborting: one predicate contains an undefined function."
                                                  "Undefined function: ", term.atoms(AppliedUndef), "Invalid predicate: ",
                                                  str(single_predicate))
                            return
                        elif not column_interval:
                            cls._logger().warning("Aborting: one predicate does not contain variables to reference columns."
                                                  "Invalid predicate: ", str(single_predicate))
                            return
                        elif term == 0:
                            cls._logger().warning("Aborting: one predicate does evaluate to zero"
                                                  "Invalid predicate: ", str(single_predicate))
                            return
                        elif not split_pred or not term or not column_interval:
                            cls._logger().warning("Aborting: one predicate does not have a valid structure."
                                                  "Invalid predicate: ", str(single_predicate))
                            return
                        else:
                            # Check if every value in column_interval has a valid structure of x_\d+
                            for var in column_interval:
                                if not re.match(r"x_\d+", str(var)):
                                    # Found an invalid variable
                                    cls._logger().warning("Aborting: one predicate uses an invalid variable to reference a column."
                                                          "Invalid predicate: ", str(single_predicate))

                            output.append(WeinhuberApproachSplit(column_interval, coef_interval, term, relation))
                    break

        if not output:
            cls._logger().warning("Aborting: all predicates have an invalid structure")
            return
        else:
            return output

    @classmethod
    def parse_user_interval(cls, user_input):
        """
        Predicate Parser for the interval.
        :variable user_input: Interval as a string
        :returns: a sympy expression (to later use in self.interval of ContextAwareSplit objects)
        (IN INVALID EDGE CASES THIS CLASS RETURNS AN EMPTY SET)

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
        # simplest special case:
        if user_input == "$i":
            return sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)

        # super basic beginning and end char check of whole input
        if not user_input.strip():
            cls._logger().warning("Warning: no interval found.")
            return sp.EmptySet
        elif user_input.strip()[0] is not "{" and user_input.strip()[0] is not "(" and user_input.strip()[0] is not "[":
            cls._logger().warning("Warning: interval starts with an invalid char."
                                  "Invalid interval: ", user_input)
            return sp.EmptySet
        elif user_input.strip()[-1] is not "}" and user_input.strip()[-1] is not ")" and user_input.strip()[
            -1] is not "]":
            cls._logger().warning("Warning: interval ends with an invalid char."
                                  "Invalid interval: ", user_input)
            return sp.EmptySet

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
                        tmp = sp.sympify(var).evalf()
                        if isinstance(tmp, sp.Number):
                            checked_members.append(tmp)
                        else:
                            cls._logger().warning("Warning: Invalid member found in finite interval."
                                                  "Invalid member: ", str(tmp), " Invalid interval: ", interval)
                    # Edge case: if no member is valid, just an empty set will be returned.
                    interval_list.append(sp.FiniteSet(*checked_members))
                else:
                    # Interval starts with { but does not end with }
                    cls._logger().warning("Warning: Invalid char at end of interval found."
                                          "Invalid interval: ", interval)
            elif interval[0] == "(" or interval[0] == "[":
                # normal intervals of structure (1,2] etc

                # Checking of first char
                if interval[0] == "(":
                    left_open = True
                elif interval[0] == "[":
                    left_open = False
                else:
                    cls._logger().warning("Warning: interval starts with an invalid char."
                                          "Invalid interval: ", user_input)
                    interval_list.append(sp.EmptySet)
                    continue

                # Checking boundaries of interval
                tmp = interval[1:-1].split(",")
                if len(tmp) > 2:
                    cls._logger().warning("Warning: too many numbers inside an interval."
                                          "Invalid interval: ", user_input)
                    interval_list.append(sp.EmptySet)
                    continue
                try:
                    a = sp.sympify(tmp[0]).evalf()
                    b = sp.sympify(tmp[1]).evalf()
                except Exception:
                    cls._logger().warning("Warning: Invalid member found inside interval."
                                          "Invalid interval: ", interval)
                    interval_list.append(sp.EmptySet)
                    continue
                else:
                    if isinstance(a, sp.Number) and isinstance(b, sp.Number):
                        # Checking of last char
                        if interval[-1] == ")":
                            right_open = True

                        elif interval[-1] == "]":
                            right_open = False
                        else:
                            cls._logger().warning("Warning: interval ends with an invalid char."
                                                  "Invalid interval: ", user_input)
                            interval_list.append(sp.EmptySet)
                            continue

                        interval_list.append(
                            sp.Interval(a, b, right_open=right_open,
                                        left_open=left_open))
                    else:
                        cls._logger().warning("Warning: Invalid member found inside interval."
                                              "Invalid interval: ", interval)
                        interval_list.append(sp.EmptySet)
            else:
                cls._logger().warning("Warning: Invalid char found inside interval."
                                      "Invalid interval: ", str(interval))
                interval_list.append(sp.EmptySet)

        # Union
        final_interval = interval_list[0]

        # union with all other intervals
        if len(interval_list) > 1:
            for item in interval_list:
                final_interval = sp.Union(final_interval, item)
        return final_interval
