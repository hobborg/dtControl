import pickle
import random
import math
from tqdm import tqdm

from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset
# from dd import cudd as _bdd
from dd import autoref as _bdd  # TODO: Might use cudd


class BDD:
    """
    Standard BDD classifier, using the dd python bindings for cudd (because sylvan was broken when I tried, 17.10.19)
    """

    def __init__(self):
        self.name = 'BDD'
        self.bdd = _bdd.BDD()
        self.bdd.configure(reordering=False)
        self.bb_table = dict()
        self.name2node = dict()
        self.result = None

    @staticmethod
    def is_applicable(dataset):
        return True
        # TODO: Add support for multi sets

    def get_stats(self):
        return {"nodes": len(self.result)}

    def predict(self, dataset):
        # TODO
        # check that everything in X_train is predicted correctly
        # predict_state tell us the allowed actions for one state
        # Iterate over whole dataset and use it
        pass

    def predict_state(self, row, X_vars, Y_vars):
        # Get bit_repr of all states vars
        state_bit_values = dict()
        for i in range(0, len(X_vars)):
            var_name = X_vars[i]
            value = row[i]
            num_bits, precision_multiplier, signed = self.bb_table[var_name]
            if signed and value < 0:
                state_bit_values[var_name + str(num_bits - 1)] = 1
                value = value * -1
                num_bits -= 1  # do not consider the most significant bit anymore
            value = math.floor(value * precision_multiplier)  # use the decimal approach (described below)
            for i in range(0, num_bits):
                if value - math.pow(2, i) >= 0:
                    state_bit_values[var_name + str(i)] = True
                    value -= math.pow(2, i)
                else:
                    state_bit_values[var_name + str(i)] = False

        allowed_actions = set()
        # try all combinations for Y_vars, remember those that return true
        # TODO: This is too much work right now.

    def check_result(self, state_bit_values, node):
        # Base cases
        if node == self.bdd.false:
            return False
        if node == self.bdd.true:
            return True
        # State variable: Read value and continue accordingly
        if node.var in state_bit_values.keys():
            if state_bit_values[node.var]:
                return self.check_result(state_bit_values, node.low if node.negated else node.high)
            else:
                return self.check_result(state_bit_values, node.high if node.negated else node.low)
        # # Action variable: Return all possible combinations
        # if node.var not in state_bit_values.keys():
        #     if_one = self.check_result(state_bit_values, node.low if node.negated else node.high)
        #     if_zero = self.check_result(state_bit_values, node.high if node.negated else node.low)
        #     if if_one is None and if_zero is None:
        #         return None
        #
        #     if if_one == []:
        #         result = [f"{node.var}=1"]
        #     else:
        #         result = list(itertools.product([f"{node.var}=1"], if_one))
        #     if if_zero == []:
        #         result += [f"{node.var}=0"]
        #     else:
        #         result += list(itertools.product([f"{node.var}=0"], if_one))
        #     return result

    def save(self, filename):
        # TODO: Does this work?
        with open(filename, 'wb') as outfile:
            pickle.dump(self, outfile)

    # TODO: Determinize first and then BDD; need to compare to this as well
    # TODO: check whether there is some cool cudd stuff that we can utilize
    def fit(self, dataset):
        # fill bb_table, the almighty table that contains the semantics and number of bits for all vars
        self.add_to_bb_table(dataset.X_metadata)
        self.add_to_bb_table(dataset.Y_metadata)
        # initialize bdd and name2node based on bb_table
        for var in self.bb_table.keys():
            for i in range(0, self.bb_table[var][0]):
                blasted_name = var + str(i)
                self.bdd.declare(blasted_name)
                self.name2node[blasted_name] = self.bdd.var(blasted_name)
        self.reorder_randomly()

        # For each state: construct the sub_result_state for the x's
        # Then construct subresult_sa_pair as OR_{action in allowed_actions} sub_result_state AND action
        # Then or this with the whole result
        row_num = -1
        total = len(dataset.X_train)
        for row in tqdm(dataset.X_train):
            row_num += 1
            # This assumes that the variables in X_train are in the same order as X_vars
            sub_result_state = self.make_sub_result_state(row, dataset.X_metadata["variables"])

            sub_result_nondet_initialized = False  # need this to initalize sub_result_sa
            multi = isinstance(dataset, MultiOutputDataset)
            # for every nondeterministic choice
            for i in range(0, len(dataset.Y_train[row_num]) if not multi else len(dataset.Y_train[0][row_num])):
                for j in range(0, len(dataset.Y_metadata["variables"])):
                    action_to_add = dataset.Y_train[row_num][i] if not multi else dataset.Y_train[j][row_num][i]
                    if action_to_add == -1:
                        continue  # -1 does not represent a playable action

                    # and all the actions (or the single action if not multi output) to sub_result_state
                    if j == 0:
                        sub_result_action = self.bdd.apply('and', sub_result_state,
                                                           self.bdd_for(dataset.index_to_value[action_to_add],
                                                                        dataset.Y_metadata["variables"][j]))
                    else:
                        sub_result_action = self.bdd.apply('and', sub_result_action,
                                                           self.bdd_for(dataset.index_to_value[action_to_add],
                                                                        dataset.Y_metadata["variables"][j]))

                # Now sub_result_action represents the and of all actions for a single nondet choice and the state
                if not sub_result_nondet_initialized:
                    sub_result_nondet = sub_result_action
                    sub_result_nondet_initialized = True
                else:
                    sub_result_nondet = self.bdd.apply('or', sub_result_nondet, sub_result_action)

            if row_num == 0:
                self.result = sub_result_nondet
            else:
                self.result = self.bdd.apply('or', self.result, sub_result_nondet)

        # collect garbage and reorder heuristics
        print("Before collecting garbage: result %s, BDD %s" % (len(self.result), len(self.bdd)))
        self.bdd.collect_garbage()
        print("After: result %s, BDD %s" % (len(self.result), len(self.bdd)))

        # reorder with dd until convergence
        i = 0
        while True:
            print(str(i) + ": result %s, BDD %s" % (len(self.result), len(self.bdd)))
            i += 1
            bdd_size = len(self.bdd)
            _bdd.reorder(self.bdd)
            if bdd_size == len(self.bdd):
                print("Reordering did not change size, local optimum BDD computed.")
                break

    """
    Returns a dict of the form
    varname -> num_bits, precision_multiplier, signed
    num_bits is how many bits we use to represent the var
    we use stepsize of the var (from metadata) to decide how precise to save a number
    Then we compute precision_multiplier based on that.
    Example: step size 0.08; then precision multiplier is 100, and we cut off anything beyond two decimals
    In general, precision_multiplier is 10^{-floor(log_10 (step size))}
    if signed, we always use the most significant bit (highest index, namely num_bits-1) to represent the sign
        (not 2 complement or anything fancy for negative numbers, 0 exists twice but should always be positive)
        
    semantics is:
    number to this special binary format:
    If signed, most significant bit gives sign and is ignored for number; else all bits are for number
    multiply number by precision_multiplier and cut everything after the comma (floor)
    represent this multiplied integer as bits.
    special binary format to number:
    If signed, most significant bit gives sign and is ignored for number, else all bits are for number
    get integer represented by bits
    divide by precision_multiplier to get actual number (up to necessary precision)
    """

    def add_to_bb_table(self, metadata):
        for i in range(0, len(metadata["variables"])):
            name = metadata["variables"][i]
            signed = True if metadata["min"][i] < 0 else False
            # this is what we multiply with to be precise up to step size; if step size > 1, we make it 1
            if metadata["step_size"][i] >= 1:
                precision_multiplier = 1
            else:
                precision_multiplier = pow(10, - math.floor(math.log(metadata["step_size"][i], 10)))
            largest_number = max(math.fabs(metadata["min"][i]), math.fabs(metadata["max"][i]))
            if largest_number == 0 or precision_multiplier == 0:  # catch some weird corner cases
                num_bits = 1 + (1 if signed else 0)
            else:  # Need the 1+ in the beginning, off-by-1 error. Try it for 8 and 10, you will see.
                num_bits = 1 + int(math.log(largest_number * precision_multiplier, 2) + (1 if signed else 0))
            self.bb_table[metadata["variables"][i]] = (num_bits, precision_multiplier, signed)

    # This assumes that the variables in X_train are in the same order as X_vars
    def make_sub_result_state(self, row, X_vars):
        for i in range(0, len(X_vars)):
            sub_result = self.bdd_for(row[i], X_vars[i]) if i == 0 else \
                self.bdd.apply('and', sub_result, self.bdd_for(row[i], X_vars[i]))
        return sub_result

    def bdd_for(self, value, varname):
        num_bits, precision_multiplier, signed = self.bb_table[varname]
        remainder = math.floor(value * precision_multiplier)  # transform to our special binary format

        # go over value in reverse order, set bits in BDD
        for i in reversed(range(0, num_bits)):
            bit_varname = varname + str(i)
            # handle corner case signed: then most significant bit (num_bits-1) is treated separately
            if signed and i == num_bits - 1:
                sub_result = self.name2node[bit_varname] if value < 0 else self.bdd.apply('not',
                                                                                          self.name2node[bit_varname])
                remainder = remainder * -1 if remainder < 0 else remainder
                continue
            # check whether the i-th bit is set by subtracting 2^{its exponent}

            if remainder - pow(2, i) >= 0:
                remainder -= pow(2, i)
                # if first bit, initialize subres; else 'and' subres and new thing
                sub_result = self.name2node[bit_varname] if i == num_bits - 1 \
                    else self.bdd.apply('and', sub_result, self.name2node[bit_varname])
            else:  # Same as above, but with a not in front of the node
                sub_result = self.bdd.apply('not', self.name2node[bit_varname]) if i == num_bits - 1 \
                    else self.bdd.apply('and', sub_result, self.bdd.apply('not', self.name2node[bit_varname]))

        if remainder != 0:
            raise Exception(f"Fatal error: Bitblasting variable {varname} did not succeed with value {value}.")

        return sub_result

    # This seems such a bad way, but all others break somehow...
    def reorder_randomly(self):
        my_order = dict()
        all_names = []
        for name in self.name2node.keys():
            all_names += [name]

        for i in range(0, len(all_names)):
            c = random.choice(all_names)
            my_order[c] = i
            all_names.remove(c)

        _bdd.reorder(self.bdd, my_order)
        # print("OrderStart:")
        # for item in sorted(self.bdd.vars):
        #    print("%s: %s" % (item, self.bdd.vars[item]))

    def export_dot(self, file=None):
        pass

    def export_c(self, file=None):
        # TODO
        # Use the ITE code from old notebook; using functions for all is not nice code, but that's why it's auto generated.
        # Anyway we should compare only the compiled versions.
        pass

    def export_vhdl(self, file=None):
        pass


#ds = SingleOutputDataset("../dumps/cruise-small-latest.dump")
#ds = MultiOutputDataset("../XYdatasets/10rooms.scs")
# ds = SingleOutputDataset("../XYdatasets/cartpole.scs")
# ds.load_if_necessary()
# bdd_classifier = BDD()
# bdd_classifier.fit(ds)
