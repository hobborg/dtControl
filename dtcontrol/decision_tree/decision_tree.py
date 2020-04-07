import logging
import pickle
from collections.abc import Iterable
from functools import reduce
from typing import Sequence

import numpy as np

import dtcontrol.util as util
from dtcontrol.benchmark_suite_classifier import BenchmarkSuiteClassifier
from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.impurity.deterministic_impurity_measure import DeterministicImpurityMeasure
from dtcontrol.decision_tree.impurity.nondeterministic_impurity_measure import NondeterministicImpurityMeasure
from dtcontrol.decision_tree.impurity.twoing_rule import TwoingRule
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplit, CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.oc1 import OC1SplittingStrategy
from dtcontrol.util import print_tuple

class DecisionTree(BenchmarkSuiteClassifier):
    def __init__(self, splitting_strategies, impurity_measure, name, early_stopping=False,
                 early_stopping_num_examples=None):
        super().__init__(name)
        self.root = None
        self.name = name
        self.splitting_strategies = splitting_strategies
        self.impurity_measure = impurity_measure
        self.early_stopping = early_stopping
        self.early_stopping_num_examples = early_stopping_num_examples
        self.check_valid()

    def check_valid(self):
        multi = any(isinstance(strategy, CategoricalMultiSplittingStrategy) for strategy in self.splitting_strategies)
        if multi and isinstance(self.impurity_measure, TwoingRule):
            raise ValueError('The twoing rule cannot be used with the multi splitting strategy.')
        oc1 = any(isinstance(strategy, OC1SplittingStrategy) for strategy in self.splitting_strategies)
        if oc1 and self.impurity_measure.get_oc1_name() is None:
            raise ValueError('Incompatible impurity measure used with OC1.')
        if oc1 and not (self.impurity_measure.determinizer.is_pre_split() or
                        self.impurity_measure.determinizer.is_pre_construction()):
            raise ValueError('OC1 can only be used with pre-determinization.')
        if not self.early_stopping and self.early_stopping_num_examples is not None:
            raise ValueError('Early stopping parameters set although early stopping is disabled.')

        determinization = isinstance(self.impurity_measure, NondeterministicImpurityMeasure) or \
                          not self.impurity_measure.determinizer.is_pre_construction()
        if determinization and (not self.early_stopping or self.early_stopping_num_examples is not None):
            raise ValueError('Determinization during tree construction '
                             'can only be used if early stopping is enabled without parameters.')

    def is_applicable(self, dataset):
        if dataset.is_deterministic:
            if isinstance(self.impurity_measure, NondeterministicImpurityMeasure):
                return False
            if not isinstance(self.impurity_measure.determinizer, NonDeterminizer):
                return False
        return True

    def fit(self, dataset):
        reset_determinizer = False
        if isinstance(self.impurity_measure, DeterministicImpurityMeasure):
            determinizer = self.impurity_measure.determinizer
            if determinizer.is_pre_construction():
                determinizer.pre_determinized_labels = determinizer.determinize(dataset)
                reset_determinizer = True

        self.root = Node(self.splitting_strategies, self.impurity_measure, self.early_stopping,
                         self.early_stopping_num_examples)
        self.root.fit(dataset)

        if reset_determinizer:
            determinizer.pre_determinized_labels = None

    def predict(self, dataset, actual_values=True):
        return self.root.predict(dataset.x, actual_values)

    def get_stats(self):
        return {
            'nodes': self.root.num_nodes,
            'inner nodes': self.root.num_inner_nodes,
            'paths': self.root.num_nodes - self.root.num_inner_nodes,
            'bandwidth': int(np.ceil(np.log2((self.root.num_nodes - self.root.num_inner_nodes))))
        }

    def print_dot(self, x_metadata, y_metadata):
        return self.root.print_dot(x_metadata, y_metadata)

    def print_c(self):
        return self.root.print_c()

    # Needs to know the number of inputs, because it has to define how many inputs the hardware component has in
    # the "entity" block
    def print_vhdl(self, num_inputs, file=None):  # TODO: multi-output; probably just give dataset to this method...
        entity_str = "entity controller is\n\tport (\n"
        all_inputs = ""
        for i in range(0, num_inputs):
            entity_str += "\t\tx" + str(i) + ": in <type>;\n"  # TODO: get type from dtcontrol.dataset :(
            all_inputs += "x" + str(i) + ","
        entity_str += "\t\ty: out <type>\n\t);\nend entity;\n\n"  # no semicolon after last declaration
        architecture = "architecture v1 of controller is\nbegin\n\tprocess(" + all_inputs[:-1] + ")\n\t \
                        begin\n" + self.root.print_vhdl() + "\n\tend process;\nend architecture;"
        if file:
            with open(file, 'w+') as outfile:
                outfile.write(entity_str + architecture)
        else:
            return entity_str + architecture

    def save(self, filename):
        with open(filename, 'wb') as outfile:
            pickle.dump(self, outfile)

    def __str__(self):
        return self.name

class Node:
    def __init__(self, splitting_strategies, impurity_measure, early_stopping=False, early_stopping_num_examples=None,
                 depth=0):
        self.splitting_strategies = splitting_strategies
        self.impurity_measure = impurity_measure
        self.early_stopping = early_stopping
        self.early_stopping_num_examples = early_stopping_num_examples
        self.depth = depth
        self.split = None
        self.num_nodes = 0
        self.num_inner_nodes = 0
        self.children = []
        # labels can be one of the following: a single label, a single tuple, a list of possible labels,
        #                                     a list of tuples
        self.index_label = None  # the label with int indices
        self.actual_label = None  # the actual float or categorical label
        self.logged_depth_problem = False

    def predict(self, x, actual_values=True):
        pred = []
        for row in np.array(x):
            pred.append(self.predict_one(row.reshape(1, -1), actual_values))
        return pred

    def predict_one(self, features, actual_values=True):
        node = self
        while not node.is_leaf():
            node = node.children[node.split.predict(features)]
        return node.actual_label if actual_values else node.index_label

    def fit(self, dataset):
        if self.check_done(dataset):
            return
        pre_determinize = isinstance(self.impurity_measure, DeterministicImpurityMeasure) and \
                          self.impurity_measure.determinizer.is_pre_split()
        if pre_determinize:
            determinized_labels = self.impurity_measure.determinizer.determinize(dataset)
            self.impurity_measure.determinizer.pre_determinized_labels = determinized_labels
        splits = [strategy.find_split(dataset, self.impurity_measure) for strategy in self.splitting_strategies]
        splits = [s for s in splits if s is not None]
        if not splits:
            logging.error("Aborting branch: no split possible.")
            return
        self.split = min(splits, key=lambda s: self.impurity_measure.calculate_impurity(dataset, s))
        if pre_determinize:
            self.impurity_measure.determinizer.pre_determinized_labels = None

        subsets = self.split.split(dataset)
        assert len(subsets) > 1
        if any(len(s.x) == 0 for s in subsets):
            logging.error("Aborting branch: no split possible. "
                          "You might want to consider adding more splitting strategies.")
            return
        for subset in subsets:
            node = Node(self.splitting_strategies, self.impurity_measure, self.early_stopping,
                        self.early_stopping_num_examples, self.depth + 1)
            node.fit(subset)
            self.children.append(node)
        self.num_nodes = 1 + sum([c.num_nodes for c in self.children])
        self.num_inner_nodes = 1 + sum([c.num_inner_nodes for c in self.children])

    def check_done(self, dataset):
        if self.depth >= 100 and not self.logged_depth_problem:
            self.logged_depth_problem = True
            logging.info("Depth >= 100. Maybe something is going wrong?")
        if self.depth >= 500:
            logging.error("Aborting branch: depth >= 500.")
            return True

        y = dataset.get_single_labels()
        if len(np.unique(y, axis=0)) <= 1:
            self.set_labels(y[0, :], dataset)
            return True

        if self.early_stopping:
            if self.early_stopping_num_examples is None or len(dataset.x) <= self.early_stopping_num_examples:
                intersection = reduce(np.intersect1d, y)
                intersection = intersection[intersection != -1]
                if len(intersection) > 0:
                    self.set_labels(intersection, dataset)
                    return True

        unique_x = np.unique(dataset.x)
        if len(unique_x) <= 1:
            self.index_label = self.actual_label = None
            self.num_nodes = 1
            return True

        return False

    def set_labels(self, label_array, dataset):
        self.index_label = [dataset.map_single_label_back(label) for label in list(label_array) if label != -1]
        if len(self.index_label) == 1:
            self.index_label = self.index_label[0]
        self.actual_label = dataset.index_label_to_actual(self.index_label)
        self.num_nodes = 1

    def is_leaf(self):
        return not self.children

    def print_dot(self, x_metadata, y_metadata):
        text = 'digraph {{\n{}\n}}'.format(self._print_dot(0, x_metadata, y_metadata)[1])
        return text

    def _print_dot(self, starting_number, x_metadata, y_metadata):
        variables = x_metadata.get('variables')
        x_category_names = x_metadata.get('category_names')
        if self.is_leaf():
            return starting_number, '{} [label=\"{}\"];\n'.format(starting_number, self.print_dot_label(y_metadata))

        text = '{} [label=\"{}\"'.format(starting_number, self.split.print_dot(variables, x_category_names))
        text += "];\n"

        last_number = -1
        child_starting_number = starting_number + 1
        if isinstance(self.split, CategoricalMultiSplit):
            names = None
            if x_category_names and self.split.feature in x_category_names:
                names = x_category_names[self.split.feature]
            labels = []
            for group in self.split.value_groups:
                if len(group) == 1:
                    label = group[0] if not names else names[group[0]]
                    labels.append(label)
                else:
                    str_group = group if not names else [names[v] for v in group]
                    label = f'{{{str_group[0]}'
                    for s in str_group[1:]:
                        label += f',\\n{s}'
                    label += '}'
                    labels.append(label)
        else:
            labels = ['True', 'False']
        assert len(self.children) == len(labels)
        for i in range(len(self.children)):
            child = self.children[i]
            last_number, child_text = child._print_dot(child_starting_number, x_metadata, y_metadata)
            text += child_text
            text += f'{starting_number} -> {child_starting_number} ['
            if not isinstance(self.split, CategoricalMultiSplit) and i == 1:
                text += 'style="dashed", '
            text += f'label="{labels[i]}"];\n'
            child_starting_number = last_number + 1
        assert last_number != -1
        return last_number, text

    def print_c(self):
        return self.print_if_then_else(1, 'c')

    def print_vhdl(self):
        return self.print_if_then_else(2, 'vhdl')

    def print_if_then_else(self, indentation_level, type):
        if type not in ['c', 'vhdl']:
            raise ValueError('Only c and vhdl printing is currently supported.')

        if self.is_leaf():
            return "\t" * indentation_level + (self.print_c_label() if type == 'c' else self.print_vhdl_label())

        if isinstance(self.split, CategoricalMultiSplit):
            if type == 'vhdl':
                raise ValueError('VHDL does not (yet?) support multi splits')
            disjunction = " || ".join([
                f"{self.split.print_c()} == {self.split.value_groups[0][i]}"
                for i in range(len(self.split.value_groups[0]))
            ])
            text = "\t" * indentation_level + f"if ({disjunction}) {{\n"
        else:
            text = "\t" * indentation_level + (
                f"if ({self.split.print_c()}) {{\n" if type == 'c' else f"if {self.split.print_vhdl()} then\n")

        text += f"{self.children[0].print_if_then_else(indentation_level + 1, type)}\n"
        if type == 'c':
            text += "\t" * indentation_level + "}\n"
        for i in range(1, len(self.children)):
            if isinstance(self.split, CategoricalMultiSplit):
                disjunction = " || ".join([
                    f"{self.split.print_c()} == {self.split.value_groups[i][j]}"
                    for j in range(len(self.split.value_groups[i]))
                ])
                c_text = f"else if ({disjunction}) {{\n"
                text += "\t" * indentation_level + c_text
            else:
                text += "\t" * indentation_level + ("else {\n" if type == 'c' else "else \n")
            text += f"{self.children[i].print_if_then_else(indentation_level + 1, type)}\n"
            text += "\t" * indentation_level + ("}\n" if type == 'c' else "end if;")

        return text

    def get_determinized_label(self):
        if isinstance(self.actual_label, list):
            # nondeterminsm present, need to determinize by finding min norm
            return min(self.actual_label, key=lambda l: self.norm(l))
        else:
            return self.actual_label

    @staticmethod
    def norm(tup):
        if isinstance(tup, tuple):
            return sum([i * i for i in tup])
        else:
            return abs(tup)

    def print_dot_label(self, y_metadata):
        if self.actual_label is None:
            raise ValueError('print_dot_label called although label is None.')

        if isinstance(self.actual_label, list):
            new_label = [self.print_single_actual_label(label, y_metadata) for label in self.actual_label]
            return util.split_into_lines(new_label)
        else:
            return self.print_single_actual_label(self.actual_label, y_metadata)

    @staticmethod
    def print_single_actual_label(label, y_metadata):
        categorical = y_metadata.get('categorical', [])
        category_names = y_metadata.get('category_names', {})
        if not isinstance(label, tuple):
            label = tuple([label])
        new_label = []
        for i in range(len(label)):
            if i in categorical:
                assert isinstance(label[i], int)
                if i in category_names:
                    new_label.append(category_names[i][label[i]])
                else:
                    new_label.append(label[i])
            else:
                new_label.append(str(util.objround(label[i], 6)))
        if len(new_label) == 1:
            return new_label[0]
        return print_tuple(new_label)

    def print_c_label(self):
        if self.actual_label is None:
            raise ValueError('print_c_label called although label is None.')
        label = self.get_determinized_label()
        if isinstance(label, Sequence):
            return ' '.join([
                f'result[{i}] = {round(label[i], 6)}f;' for i in range(len(label))
            ])
        return f'return {round(float(label), 6)}f;'

    def print_vhdl_label(self):
        if self.actual_label is None:
            raise ValueError('print_vhdl_label called although label is None.')
        label = self.get_determinized_label()
        if isinstance(label, Iterable):
            i = 0
            result = ""
            for controlInput in label:
                result += f'y{str(i)} <= {str(controlInput)}; '
                i += 1
            return result
        return f'y <= {str(label)};'
