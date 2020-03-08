import logging
import pickle
from collections.abc import Iterable
from typing import Sequence

import numpy as np

import dtcontrol.util as util
from dtcontrol.benchmark_suite_classifier import BenchmarkSuiteClassifier
from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplit
from dtcontrol.util import print_tuple

class DecisionTree(BenchmarkSuiteClassifier):
    def __init__(self, determinizer, split_strategies, impurity_measure, name):
        super().__init__(name)
        self.root = None
        self.name = name
        self.determinizer = determinizer
        self.split_strategies = split_strategies
        self.impurity_measure = impurity_measure

    def is_applicable(self, dataset):
        return not (self.determinizer.is_only_multioutput() and isinstance(dataset, SingleOutputDataset)) and \
               not (dataset.is_deterministic and not isinstance(self.determinizer, NonDeterminizer))

    def fit(self, dataset):
        self.determinizer.set_dataset(dataset)
        self.root = Node(self.determinizer, self.split_strategies, self.impurity_measure)
        prev_y = dataset.y
        if self.determinizer.determinize_once_before_construction():
            y = self.determinizer.determinize(dataset)
            dataset.y = y
        self.root.fit(dataset)
        dataset.y = prev_y

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
    def __init__(self, determinizer, split_strategies, impurity_measure, depth=0):
        self.determinizer = determinizer
        self.split_strategies = split_strategies
        self.impurity_measure = impurity_measure
        self.split = None
        self.depth = depth
        self.num_nodes = 0
        self.num_inner_nodes = 0
        self.children = []
        # labels can be one of the following: a single label, a single tuple, a list of possible labels,
        #                                     a list of tuples
        self.index_label = None  # the label with int indices
        self.actual_label = None  # the actual float or categorical label

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
        y = self.determinizer.determinize(dataset) if not self.determinizer.determinize_once_before_construction() \
            else dataset.y
        if self.check_done(dataset.x, y):
            return
        splits = [strategy.find_split(dataset, y, self.impurity_measure) for strategy in self.split_strategies]
        splits = [s for s in splits if s is not None]
        if not splits:
            logging.error("Aborting branch: no split possible.")
            return
        self.split = min(splits, key=lambda s: self.impurity_measure.calculate_impurity(dataset, y, s))

        subsets = self.split.split(dataset)
        assert len(subsets) > 1
        for subset in subsets:
            node = Node(self.determinizer, self.split_strategies, self.impurity_measure, self.depth + 1)
            node.fit(subset)
            self.children.append(node)
        self.num_nodes = 1 + sum([c.num_nodes for c in self.children])
        self.num_inner_nodes = 1 + sum([c.num_inner_nodes for c in self.children])

    def check_done(self, x, y):
        if self.depth >= 100:
            logging.info("Depth >= 100. Maybe something is going wrong?")
        if self.depth >= 500:
            logging.error("Aborting branch: depth >= 500.")
            return True

        unique_labels = np.unique(y)
        num_unique_labels = len(unique_labels)
        unique_data = np.unique(x, axis=0)
        num_unique_data = len(unique_data)
        if num_unique_labels <= 1 or num_unique_data <= 1:
            if len(unique_labels) > 0:
                self.index_label = self.determinizer.get_index_label(y[0])
                self.actual_label = self.determinizer.get_actual_label(y[0])
            else:
                self.index_label = self.actual_label = None
            self.num_nodes = 1
            return True
        return False

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
            if x_category_names and self.split.feature in x_category_names:
                names = x_category_names[self.split.feature]
                labels = [names[i] for i in self.split.value_groups]
            else:
                labels = self.split.value_groups
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
            text = "\t" * indentation_level + (
                f"if ({self.split.print_c()} == {self.split.value_groups[0]}) {{\n" if type == 'c' else
                f"if {self.split.print_vhdl()} = {self.split.value_groups[0]} then\n")
        else:
            text = "\t" * indentation_level + (
                f"if ({self.split.print_c()}) {{\n" if type == 'c' else f"if {self.split.print_vhdl()} then\n")

        text += f"{self.children[0].print_if_then_else(indentation_level + 1, type)}\n"
        if type == 'c':
            text += "\t" * indentation_level + "}\n"
        for i in range(1, len(self.children)):
            if isinstance(self.split, CategoricalMultiSplit):
                c_text = f"else if ({self.split.print_c()} == {self.split.value_groups[i]}) {{\n"
                vhdl_text = f"else if ({self.split.print_vhdl()} = {self.split.value_groups[i]} then\n"
                text += "\t" * indentation_level + (c_text if type == 'c' else vhdl_text)
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
            if len(new_label) == 1:
                return new_label[0]
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
