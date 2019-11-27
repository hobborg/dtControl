import pickle
import sys
from collections.abc import Iterable

import numpy as np
from jinja2 import FileSystemLoader, Environment
from sklearn.base import BaseEstimator

import dtcontrol
from src.dataset.multi_output_dataset import MultiOutputDataset
from src.dataset.single_output_dataset import SingleOutputDataset

file_loader = FileSystemLoader([path + "/src/c_templates" for path in dtcontrol.__path__])
env = Environment(loader=file_loader)
single_output_c_template = env.get_template('single_output.c')
multi_output_c_template = env.get_template('multi_output.c')

class DecisionTree(BaseEstimator):
    def __init__(self, det_strategy, split_strategies):
        self.root = None
        self.name = None
        self.check_combinable(det_strategy, split_strategies)
        self.det_strategy = det_strategy
        self.split_strategies = split_strategies

    def check_combinable(self, det_strategy, split_strategies):
        pass  # TODO

    def is_applicable(self, dataset):
        return isinstance(dataset, MultiOutputDataset) and self.det_strategy.is_only_multioutput() or \
               isinstance(dataset, SingleOutputDataset) and not self.det_strategy.is_only_multioutput()

    def fit(self, dataset):
        self.root = Node(self.det_strategy, self.split_strategies)
        self.root.fit(dataset)

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

    # Needs to know the number of inputs, because it has to define how many inputs the hardware component has in the "entity" block
    def export_vhdl(self, numInputs, file=None):
        entitystr = "entity controller is\n\tport (\n"
        allInputs = ""
        for i in range(0, numInputs):
            entitystr += "\t\tx" + str(i) + ": in <type>;\n"  # todo: get type from dtcontrol.dataset :(
            allInputs += "x" + str(i) + ","
        entitystr += "\t\ty: out <type>\n\t);\nend entity;\n\n"  # no semicolon after last declaration. todo: multi-output; probably just give dataset to this method...
        architecture = "architecture v1 of controller is\nbegin\n\tprocess(" + allInputs[
                                                                               :-1] + ")\n\tbegin\n" + self.root.export_vhdl() + "\n\tend process;\nend architecture;"
        if file:
            with open(file, 'w+') as outfile:
                outfile.write(entitystr + architecture)
        else:
            return entitystr + architecture

    def save(self, filename):
        with open(filename, 'wb') as outfile:
            pickle.dump(self, outfile)

    def __str__(self):
        return self.name

class Node:
    def __init__(self, det_strategy, split_strategies, depth=0):
        self.det_strategy = det_strategy
        self.split_strategies = split_strategies
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
        y = self.det_strategy.determinize(dataset)
        if self.check_done(dataset.X_train, y):
            return
        mask = self.find_split(X, y)
        self.left = self.create_child_node()
        self.right = self.create_child_node()
        self.fit_children(X, y, mask)

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
            self.trained_label = y[0] if len(unique_labels) > 0 else None  # WIP
            self.num_nodes = 1
            return True
        return False

    @abstractmethod
    def create_child_node(self):
        pass

    @abstractmethod
    def find_split(self, X, y):
        pass

    def fit_children(self, X, y, mask):
        if len(y.shape) == 3:
            left_labels, right_labels = y[:, mask, :], y[:, ~mask, :]
        else:
            left_labels, right_labels = y[mask], y[~mask]
        self.left.fit(X[mask], left_labels)
        self.right.fit(X[~mask], right_labels)
        self.num_nodes = 1 + self.left.num_nodes + self.right.num_nodes

    @staticmethod
    def calculate_impurity(labels, mask):
        left = labels[mask]
        right = labels[~mask]
        if len(left) == 0 or len(right) == 0: return sys.maxsize
        num_labels = len(labels)
        return (len(left) / num_labels) * Node.calculate_entropy(left) + \
               (len(right) / num_labels) * Node.calculate_entropy(right)

    @staticmethod
    def calculate_entropy(labels):
        num_labels = len(labels)
        unique = np.unique(labels)
        probs = [len(labels[labels == label]) / num_labels for label in unique]
        return sum(-prob * np.log2(prob) for prob in probs)

    def export_dot(self):
        text = 'digraph {{\n{}\n}}'.format(self._export_dot(0)[1])
        return text

    def _export_dot(self, starting_number):
        if not self.left and not self.right:
            return starting_number, '{} [label=\"{}\"];\n'.format(starting_number, self.get_dot_label())

        text = '{} [label=\"{}\"'.format(starting_number, self.get_dot_label())
        if self.print_dot_red():
            text += ', fillcolor=firebrick1, style=filled'
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

    @abstractmethod
    def is_axis_aligned(self):
        pass

    def export_c(self):
        return self._export_if_then_else(0, 'c')

    def export_vhdl(self):
        return self._export_if_then_else(2, 'vhdl')

    # This handles both the c and vhdl export of nodes, as they both have the if-then-else structure and differ only in details
    # Type can be 'c' or 'vhdl', currently
    def _export_if_then_else(self, indent_index, type):
        # get label depending on type
        if type == 'c':
            label = self.get_c_label()
        elif type == 'vhdl':
            label = self.get_vhdl_label()
        else:
            raise Exception(
                f'Unknown type {type} in _export_if_then_else')  # do this type check once; from now on, else always means vhdl
        # If leaf node
        if not self.left and not self.right:
            return "\t" * indent_index + str(label)

        # if inner node
        text = ""
        text += "\t" * indent_index + (
            f"if ({self.get_c_label()}) {{\n" if type == 'c' else f"if {self.get_vhdl_label()} then\n")

        if self.left:
            text += f"{self.left._export_if_then_else(indent_index + 1, type)}\n"
        else:
            text += "\t" * (indent_index + 1) + ";\n"
        if type == 'c':
            text += "\t" * indent_index + "}\n"

        if self.right:
            text += "\t" * indent_index + ("else {\n" if type == 'c' else "else \n")
            text += f"{self.right._export_if_then_else(indent_index + 1, type)}\n"
            text += "\t" * indent_index + ("}" if type == 'c' else "end if;")

        return text

    def get_determinized_label(self):
        if isinstance(self.actual_label,
                      list):  # list of things, i.e. nondeterminsm present, need to determinise by finding max norm (could use other ideas as well)
            return min(self.actual_label, key=lambda l: self.norm(l))
        else:  # just an int or a tuple, easy; note that we have to use list and not iterable in the above if, because tuples (multi control input) are also iterable
            return self.actual_label

            # If tup is an int, return abs of that number; if it is a tuple, return sum of absolutes of contents

    # Used by get_determinized_label
    def norm(self, tup):
        if isinstance(tup, tuple):
            return sum([i * i for i in tup])
        else:  # if it is not iterable, then it was a single number, return abs of that
            return abs(tup)

    @abstractmethod
    def get_dot_label(self):
        pass

    @abstractmethod
    def print_dot_red(self):
        pass

    def get_c_label(self):
        return self._get_label('c')

    def get_vhdl_label(self):
        return self._get_label('vhdl')

    def _get_label(self, type):
        # if leaf, return class; determinize if necessary, and handle multi output printing
        if self.actual_label is not None:
            label = self.get_determinized_label()
            if isinstance(label, Iterable):
                if type == 'c':
                    return ' '.join([
                        f'result[{i}] = {round(label[i], 6)}f;' for i in range(len(label))
                    ])
                else:
                    i = 0
                    result = ""
                    for controlInput in label:
                        result += f'y{str(i)} <= {str(controlInput)}; '
                        i += 1
                    return result
            else:
                if type == 'c':
                    return f'return {round(float(label), 6)}f;'
                else:
                    return f'y <= {str(label)};'
        # else, print predicate in correct format

        if self.is_axis_aligned():
            try:  # the guy keeping track of the tree is called differently depending on subclass. This ain't nice, but it works.
                tree = self.dt.tree_
            except:
                tree = self.classifier.tree_
            l = f'X[{tree.feature[0]}]' if type == 'c' else f'x{tree.feature[0]}'
            return f'{l} <= {round(tree.threshold[0], 4)}'
        else:
            # this implicitly assumes n_classes == 2
            if self.classifier is not None:
                coef_ = self.classifier.coef_[0]
                intercept_ = self.classifier.intercept_[0]
            else:  # OC1Node
                coef_ = self.coeff
                intercept_ = self.intercept
            line = []
            for i in range(0, len(coef_)):
                line.append(f"{coef_[i]}*X[{i}]" if type == 'c' else f"{coef_[i]}*x{i}")
            line.append(f"{intercept_}")
            hyperplane = "+".join(line) + " <= 0"
            return hyperplane.replace('+-', '-')
