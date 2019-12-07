import pickle
from collections.abc import Iterable

import numpy as np
from jinja2 import FileSystemLoader, Environment
from sklearn.base import BaseEstimator

import dtcontrol
from src import util
from src.dataset.multi_output_dataset import MultiOutputDataset
from src.dataset.single_output_dataset import SingleOutputDataset

file_loader = FileSystemLoader([path + "/src/c_templates" for path in dtcontrol.__path__])
env = Environment(loader=file_loader)
single_output_c_template = env.get_template('single_output.c')
multi_output_c_template = env.get_template('multi_output.c')

class DecisionTree(BaseEstimator):
    def __init__(self, det_strategy, split_strategies, impurity_measure):
        self.root = None
        self.name = None
        self.det_strategy = det_strategy
        self.split_strategies = split_strategies
        self.impurity_measure = impurity_measure

    def is_applicable(self, dataset):
        return isinstance(dataset, MultiOutputDataset) and self.det_strategy.is_only_multioutput() or \
               isinstance(dataset, SingleOutputDataset) and not self.det_strategy.is_only_multioutput()

    def fit(self, dataset):
        self.det_strategy.set_dataset(dataset)
        self.root = Node(self.det_strategy, self.split_strategies, self.impurity_measure)
        prev_y = dataset.Y_train
        if self.det_strategy.determinize_once_before_construction():
            y = self.det_strategy.determinize(dataset)
            dataset.Y_train = y
        self.root.fit(dataset)
        dataset.Y_train = prev_y

    def predict(self, dataset, actual_values=True):
        return self.root.predict(dataset.X_train, actual_values)

    def get_stats(self):  # TODO: add entry for every splitting strategy if # > 2
        return {
            'nodes': self.root.num_nodes,
            'bandwidth': int(np.ceil(np.log2((self.root.num_nodes + 1) / 2)))
        }

    def export_dot(self, file=None):
        dot = self.root.export_dot()
        if file:
            with open(file, 'w+') as outfile:
                outfile.write(dot)
        else:
            return dot

    def export_c(self, num_outputs, example, file=None):
        template = multi_output_c_template if num_outputs > 1 else single_output_c_template
        code = self.root.export_c()
        result = template.render(example=example, num_outputs=num_outputs, code=code)
        if file:
            with open(file, 'w+') as outfile:
                outfile.write(result)
        else:
            return result

    # Needs to know the number of inputs, because it has to define how many inputs the hardware component has in
    # the "entity" block
    def export_vhdl(self, num_inputs, file=None):  # TODO: multi-output; probably just give dataset to this method...
        entity_str = "entity controller is\n\tport (\n"
        all_inputs = ""
        for i in range(0, num_inputs):
            entity_str += "\t\tx" + str(i) + ": in <type>;\n"  # TODO: get type from dtcontrol.dataset :(
            all_inputs += "x" + str(i) + ","
        entity_str += "\t\ty: out <type>\n\t);\nend entity;\n\n"  # no semicolon after last declaration
        architecture = "architecture v1 of controller is\nbegin\n\tprocess(" + all_inputs[:-1] + ")\n\t \
                        begin\n" + self.root.export_vhdl() + "\n\tend process;\nend architecture;"
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
    def __init__(self, det_strategy, split_strategies, impurity_measure, depth=0):
        self.det_strategy = det_strategy
        self.split_strategies = split_strategies
        self.impurity_measure = impurity_measure
        self.split = None
        self.depth = depth
        self.num_nodes = 0
        self.left = None
        self.right = None
        # labels can be one of the following: a single label, a single tuple, a list of possible labels,
        #                                     a list of tuples
        self.index_label = None  # the label with int indices
        self.actual_label = None  # the actual float label

    def predict(self, X, actual_values=True):
        pred = []
        for row in np.array(X):
            pred.append(self.predict_one(row.reshape(1, -1), actual_values))
        return pred

    def predict_one(self, features, actual_values=True):
        node = self
        while node.left:
            node = node.left if node.test_condition(features) else node.right
        return node.actual_label if actual_values else node.index_label

    def test_condition(self, x):
        return self.split.predict(x)

    def fit(self, dataset):
        y = self.det_strategy.determinize(dataset) if not self.det_strategy.determinize_once_before_construction() \
            else dataset.Y_train
        if self.check_done(dataset.X_train, y):
            return
        splits = [strategy.find_split(dataset.X_train, y, self.impurity_measure) for strategy in self.split_strategies]
        mask, self.split = min(splits, key=lambda mask, split: self.impurity_measure.calculate_impurity(y, mask))

        left_data, right_data = dataset.split(mask)
        self.left = Node(self.det_strategy, self.split_strategies, self.impurity_measure, self.depth + 1)
        self.right = Node(self.det_strategy, self.split_strategies, self.impurity_measure, self.depth + 1)
        self.left.fit(left_data)
        self.right.fit(right_data)
        self.num_nodes = 1 + self.left.num_nodes + self.right.num_nodes

    def check_done(self, X, y):
        if self.depth >= 500:
            print("Aborting: depth >= 500.")
            return True

        unique_labels = np.unique(y)
        num_unique_labels = len(unique_labels)
        unique_data = np.unique(X, axis=0)
        num_unique_data = len(unique_data)
        if num_unique_labels <= 1 or num_unique_data <= 1:
            if len(unique_labels) > 0:
                self.index_label = self.actual_label = None
            else:
                self.index_label = self.det_strategy.get_index_label(y[0])
                self.actual_label = self.det_strategy.get_actual_label(y[0])
            self.num_nodes = 1
            return True
        return False

    def is_leaf(self):
        return not self.left and not self.right

    def export_dot(self):
        text = 'digraph {{\n{}\n}}'.format(self._export_dot(0)[1])
        return text

    def _export_dot(self, starting_number):
        if self.is_leaf():
            return starting_number, '{} [label=\"{}\"];\n'.format(starting_number, self.print_dot_label())

        text = '{} [label=\"{}\"'.format(starting_number, self.split.print_dot())
        text += "];\n"

        number_for_right = starting_number + 1
        last_number = starting_number

        if self.left:
            last_left_number, left_text = self.left._export_dot(starting_number + 1)
            text += left_text
            label = 'True' if starting_number == 0 else ''
            text += '{} -> {} [label="{}"];\n'.format(starting_number, starting_number + 1, label)
            number_for_right = last_left_number + 1
            last_number = last_left_number

        if self.right:
            last_right_number, right_text = self.right._export_dot(number_for_right)
            text += right_text
            label = 'False' if starting_number == 0 else ''
            text += '{} -> {} [style="dashed", label="{}"];\n'.format(starting_number, number_for_right, label)
            last_number = last_right_number

        return last_number, text

    def export_c(self):
        return self.export_if_then_else(0, 'c')

    def export_vhdl(self):
        return self.export_if_then_else(2, 'vhdl')

    def export_if_then_else(self, indentation_level, type):
        if type not in ['c', 'vhdl']:
            raise ValueError('Only c and vhdl printing is currently supported.')

        if self.is_leaf():
            return "\t" * indentation_level + (self.print_c_label() if type == 'c' else self.print_vhdl_label())

        text = "\t" * indentation_level + (
            f"if ({self.split.print_c()}) {{\n" if type == 'c' else f"if {self.split.print_vhdl()} then\n")

        if self.left:
            text += f"{self.left.export_if_then_else(indentation_level + 1, type)}\n"
        else:
            text += "\t" * (indentation_level + 1) + ";\n"
        if type == 'c':
            text += "\t" * indentation_level + "}\n"

        if self.right:
            text += "\t" * indentation_level + ("else {\n" if type == 'c' else "else \n")
            text += f"{self.right.export_if_then_else(indentation_level + 1, type)}\n"
            text += "\t" * indentation_level + ("}" if type == 'c' else "end if;")

        return text

    def get_determinized_label(self):
        if isinstance(self.actual_label, list):
            # nondeterminsm present, need to determinize by finding min norm
            return min(self.actual_label, key=lambda l: self.norm(l))
        else:
            return self.actual_label

    def norm(self, tup):
        if isinstance(tup, tuple):
            return sum([i * i for i in tup])
        else:
            return abs(tup)

    def print_dot_label(self):
        if self.actual_label is None:
            raise ValueError('print_dot_label called although label is None.')
        rounded = util.objround(self.actual_label, 6)
        return util.split_into_lines(rounded)

    def print_c_label(self):
        if self.actual_label is None:
            raise ValueError('print_c_label called although label is None.')
        if isinstance(self.actual_label, Iterable):
            return ' '.join([
                f'result[{i}] = {round(self.actual_label[i], 6)}f;' for i in range(len(self.actual_label))
            ])
        return f'return {round(float(self.actual_label), 6)}f;'

    def print_vhdl_label(self):
        if self.actual_label is None:
            raise ValueError('print_vhdl_label called although label is None.')
        if isinstance(self.actual_label, Iterable):
            i = 0
            result = ""
            for controlInput in self.actual_label:
                result += f'y{str(i)} <= {str(controlInput)}; '
                i += 1
            return result
        return f'y <= {str(self.actual_label)};'
