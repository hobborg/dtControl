import logging

import math
import random
import sys

import numpy
# from dd import cudd as _bdd # TODO: use cudd?
from dd import autoref as _bdd
logging.getLogger("dd").setLevel(logging.CRITICAL)
from tqdm import tqdm

from dtcontrol.benchmark_suite_classifier import BenchmarkSuiteClassifier
from dtcontrol.pre_processing.norm_pre_processor import NormPreProcessor
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer



class BDD(BenchmarkSuiteClassifier):
    """
    Standard BDD classifier, using the dd python bindings for cudd I guess (because sylvan was broken when I tried, 17.10.19)
    """
    """
    Bitblasting Semantics:
    bitblasting works by using metadata:
    val_blasted = (val - min) / step_size ; used when making a subresult
    num_bits = ld((max-min)/step_size) ; used in generating the vars in the beginning of fit
    """

    # all_or_unique_label: 0 tries to or all the allowed actions, 1 gives a unique label to every combination and saves that
    # label_pre_processor: determinizes the dataset before giving to BDD
    # name_suffix: Appended to the name to make unique
    def __init__(self, all_or_unique_label, label_pre_processor=None, name_suffix=None):
        self.name = f"BDD_{'actOR' if all_or_unique_label == 0 else 'UL'}" + ("_prepro" if label_pre_processor != None else "") + (str(name_suffix) if name_suffix != None else "")
        self.bdd = _bdd.BDD()
        self.bdd.configure(reordering=False)
        self.name2node = dict()
        self.result = None
        self.all_or_unique_label = all_or_unique_label
        self.x_metadata = dict()
        self.act_metadata = dict()
        self.label_pre_processor = label_pre_processor

    def is_applicable(self, dataset):
        return True

    def get_stats(self):
        return {"nodes": len(self.result)}

    # TODO: check whether there is some cool cudd stuff that we can utilize
    def fit(self, dataset):
        if self.label_pre_processor is not None:
            dataset = self.label_pre_processor.preprocess(dataset)
        self.x_metadata = dataset.x_metadata
        if "variables" not in self.x_metadata.keys():
            self.x_metadata["variables"] = [f"x{i}" for i in range(0, len(dataset.x[0]))]
        # generate blasted vars for state vars, add them to BDD 
        self.blast_vars(self.x_metadata)
        print("Blasted state vars")

        # Add blasted vars for actions; two cases: Or-ing all allowed actions (0) or unique labels (1)
        # (Stuff like minnorm comes by modifying dataset before)
        if self.all_or_unique_label == 0:
            self.act_metadata["variables"] = ["actOR"]
            self.act_metadata["max_outer"] = [numpy.amax(dataset.get_single_labels())]
            self.act_metadata["min_outer"] = [0]
            self.act_metadata["step_size"] = [1]
        elif self.all_or_unique_label == 1:
            self.act_metadata["variables"] = ['actUL']
            self.act_metadata["max_outer"] = [max(dataset.get_unique_labels())]
            self.act_metadata["min_outer"] = [0]
            self.act_metadata["step_size"] = [1]
        else:
            logging.error("Invalid value for all_or_unique_label, namely" + str(self.all_or_unique_label))
            sys.exit()
        self.blast_vars(self.act_metadata)

        print("Blasted act vars")


        # Random starting order
        self.reorder_randomly()

        print("Reordered")

        # Finally construct the BDD
        row_num = -1
        logging.info("Loading data and constructing BDD...")
        for row in tqdm(dataset.x):
            row_num += 1
            # AND all state vars
            row_result = self.make_sub_result_state(row, self.x_metadata)

            # Add the actions to BDD
            if self.all_or_unique_label == 0:
                for a in range(0, len(dataset.get_single_labels()[row_num])):
                    if dataset.get_single_labels()[row_num][a] == -1:
                        break  # end of sensible actions
                    single_act_result = self.bdd_for(dataset.get_single_labels()[row_num][a], self.act_metadata, 0)
                    act_result = single_act_result if a == 0 else self.bdd.apply('or', act_result, single_act_result)
            elif self.all_or_unique_label == 1:
                # Unique label
                act_result = self.bdd_for(dataset.get_unique_labels()[row_num], self.act_metadata, 0)
            else:
                logging.error("Invalid value for all_or_unique_label, namely" + str(self.all_or_unique_label))
                sys.exit()

            row_result = self.bdd.apply('and', row_result, act_result)
            # Add row_result to whole offset (OR)
            self.result = row_result if row_num == 0 else self.bdd.apply('or', self.result, row_result)

        # collect garbage and reorder heuristics
        # print("Before collecting garbage: offset %s, BDD %s" % (len(self.offset), len(self.bdd)))
        self.bdd.collect_garbage()
        # print("After: offset %s, BDD %s" % (len(self.offset), len(self.bdd)))

        # reorder with dd until convergence
        i = 0
        while True:
            # print(str(i) + ": offset %s, BDD %s" % (len(self.offset), len(self.bdd)))
            i += 1
            bdd_size = len(self.bdd)
            _bdd.reorder(self.bdd)
            if bdd_size == len(self.bdd):
                # print("Reordering did not change size, local optimum BDD computed.")
                break

        # print("Final: offset %s, BDD %s" % (len(self.offset), len(self.bdd)))

    ################### Helper methods for fit #####################

    # generate blasted vars for vars, add them to BDD 
    # Usual means that we take num_bits = ceil( ld( (max-min)/step_size ) )
    def blast_vars(self, metadata):
        print("Blast-vars-helper running now")
        for i in range(0, len(metadata["variables"])):
            #num_bits = ceil( ld( (max-min)/step_size ) )
            #print("Name: " + metadata["variables"][i])
            #print("max: " + str(metadata["max"][i]))
            #print("min: " + str(metadata["min"][i]))
            #print("stepsize: " + str(metadata["step_size"][i]))
            if metadata["max_outer"][i] - metadata["min_outer"][i] == 0:
                num_bits = 0 # catch corner case of useless vars, e.g. in cruise
            else:
                num_bits = 1 + int(math.log(((metadata["max_outer"][i] - metadata["min_outer"][i]) / metadata["step_size"][i]), 2))
            for j in range(0, num_bits):
                blasted_name = metadata["variables"][i] + f"_{j}"
                self.bdd.declare(blasted_name)
                self.name2node[blasted_name] = self.bdd.var(blasted_name)

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

    # Returns BDD for setting all the state-variables in row (AND)
    def make_sub_result_state(self, row, x_metadata):
        for i in range(0, len(x_metadata["variables"])):
            var_result = self.bdd_for(row[i], x_metadata, i)
            sub_result = var_result if i == 0 else self.bdd.apply('and', sub_result, var_result)
        return sub_result

    # Returns bdd for setting a single variable to value (AND)
    # Use metadata to figure out which bits to set to 0 and which to 1
    def bdd_for(self, value, metadata, i):
        varname = metadata["variables"][i]
        min_val = metadata["min_outer"][i]
        max_val = metadata["max_outer"][i]
        step_size = metadata["step_size"][i]

        if max_val - min_val == 0:
            return self.bdd.true # catch corner case of useless vars, e.g. in cruise
        num_bits = 1 + int(math.log(((max_val-min_val) / step_size), 2))
        label = int(round((value - min_val) / step_size))

        # go over label in reverse order, set bits in BDD
        for i in reversed(range(0, num_bits)):
            bit_varname = varname + f"_{i}"
            if label - pow(2, i) >= 0:
                label -= pow(2, i)
                bit_result = self.name2node[bit_varname]
            else:
                bit_result = self.bdd.apply('not', self.name2node[bit_varname])
            var_result = bit_result if i == num_bits - 1 else self.bdd.apply('and', var_result, bit_result)
        if label != 0:
            raise Exception(
                f"Fatal error: Bitblasting variable {varname} did not succeed with remaining label {label} for value {value}.")
        return var_result

    ################ Reading the BDD ##############
    def predict(self, dataset, actual_values=True):
        if actual_values == True:
            raise Exception("Predict with actual_values==True not supported by BDD")
        if self.checkValid(dataset):
            return dataset.get_single_labels()  # TODO: this doesn't work for multi-output

    def checkValid(self, dataset):
        return True  # TODO: NOT CHECKING VALIDITY RIGHT NOW
        if self.label_pre_processor is not None:
            dataset = self.label_pre_processor.preprocess(dataset)
        row_num = -1
        sols = [x for x in self.bdd.pick_iter(self.offset)]

        # We can check containment of dataset in sols; other way round is more difficult, so additionally we check that they have same number of solutions
        num_dataset_sols = len(dataset.x) if self.all_or_unique_label == 1 else sum(
            [sum([1 for x in dataset.get_single_labels()[i] if x != -1]) for i in
             range(0, len(dataset.get_single_labels()))])
        if not len(sols) == num_dataset_sols:
            raise Exception(f"BDD has {len(sols)} solutions, but dataset has {num_dataset_sols}")

        # If number of rows is equal, just need to check that every row is contained in sols
        for row in tqdm(dataset.x):
            row_num += 1
            allowed_actions = dataset.get_single_labels()[row_num] if self.all_or_unique_label == 0 else [
                dataset.get_unique_labels()[row_num]]
            for act in allowed_actions:
                if act == -1:
                    continue
                if self.get_bit_values(row, act) in sols:
                    continue
                else:
                    action_str = f"allowed action {act} of {allowed_actions} (all or)" if self.all_or_unique_label == 0 else "allowed unique label {act}"
                    raise Exception(f"Row {row} with {action_str} is not contained in BDD sols")
        return True

    # TODO: we could use this also when constructing the BDD, but that changes structure and I don't want to refactor right now. However, this way I copy pasted a lot of code.
    def get_bit_values(self, row, act):
        bit_values = dict()

        # bit_values for the state vars
        for i in range(0, len(row)):
            varname = self.x_metadata["variables"][i]
            min_val = self.x_metadata["min_outer"][i]
            max_val = self.x_metadata["max_outer"][i]
            step_size = self.x_metadata["step_size"][i]
            num_bits = 1 + int(math.log(((max_val - min_val) / step_size), 2))
            label = int(round((row[i] - min_val) / step_size))

            # go over label in reverse order, set bits in offset table
            for i in reversed(range(0, num_bits)):
                bit_varname = varname + f"_{i}"
                if label - pow(2, i) >= 0:
                    label -= pow(2, i)
                    bit_values[bit_varname] = 1
                else:
                    bit_values[bit_varname] = 0
            if label != 0:
                raise Exception(
                    f"Fatal error: Bitblasting variable {varname} did not succeed with remaining label {label} for value {row[i]}.")

        # bit_values for the action (too lazy to avoid duplicating); also note that this only works for SingleOutputDatasets
        varname = self.act_metadata["variables"][0]
        min_val = self.act_metadata["min_outer"][0]
        max_val = self.act_metadata["max_outer"][0]
        step_size = self.act_metadata["step_size"][0]
        num_bits = 1 + int(math.log(((max_val - min_val) / step_size), 2))
        label = int(round((act - min_val) / step_size))

        # go over label in reverse order, set bits in offset table
        for i in reversed(range(0, num_bits)):
            bit_varname = varname + f"_{i}"
            if label - pow(2, i) >= 0:
                label -= pow(2, i)
                bit_values[bit_varname] = 1
            else:
                bit_values[bit_varname] = 0
        if label != 0:
            raise Exception(
                f"Fatal error: Bitblasting variable {varname} did not succeed with remaining label {label} for value {act}.")

        return bit_values

    def save(self, file):
        pass

    def print_dot(self, x_metadata, y_metadata):
        return "Not supported"

    def print_c(self):
        return self.result.to_expr()

    def print_pdf(self, filename):
        self.bdd.dump(filename, filetype='pdf')

# ds = SingleOutputDataset("../dumps/cruise-small-latest.dump")
# ds = MultiOutputDataset("../examples/10rooms.scs")
# ds = SingleOutputDataset("../examples/cartpole.scs")
# ds.load_if_necessary()
# bdd_classifier = BDD(0)
# bdd_classifier.fit(ds)
# bdd_classifier.checkValid(ds)
# print("Everything is valid!")
