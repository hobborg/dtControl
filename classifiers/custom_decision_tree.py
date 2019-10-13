import pickle
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable
import numpy as np
from sklearn.base import BaseEstimator

class CustomDecisionTree(ABC, BaseEstimator):
    def __init__(self):
        self.root = None

    @abstractmethod
    def is_applicable(self, dataset):
        pass

    @abstractmethod
    def fit(self, dataset):
        pass

    def set_labels(self, leaf_fun, index_to_value):
        def _visit_leaves(tree):
            if tree is None:
                return
            if tree.trained_label is not None:
                tree.mapped_label = leaf_fun(tree)
                # the mapped label can be either a list of labels or a single label
                if isinstance(tree.mapped_label, Iterable):
                    if isinstance(tree.mapped_label[0], Iterable):
                        tree.actual_label = [(index_to_value[i], index_to_value[j]) for (i, j) in
                                             tree.mapped_label]  # TODO: this doesnt work if we have more than 2 control inputs
                    else:
                        tree.actual_label = [index_to_value[i] for i in tree.mapped_label if i != -1]
                else:
                    tree.actual_label = index_to_value[tree.mapped_label]
            _visit_leaves(tree.left)
            _visit_leaves(tree.right)

        _visit_leaves(self.root)

    def predict(self, dataset):
        pred = []
        for row in np.array(dataset.X_train):
            pred.append(self.classify_instance(row.reshape(1, -1)))
        return pred

    def classify_instance(self, features):
        node = self.root
        while node.left:
            node = node.left if node.test_condition(features) else node.right
        return node.mapped_label

    def get_stats(self):
        return {
            'num_nodes': self.root.num_nodes
        }

    def export_dot(self, file=None):
        dot = self.root.export_dot()
        if file:
            with open(file, 'w+') as outfile:
                outfile.write(dot)
        else:
            return dot

    def export_c(self, file=None):
        c = self.root.export_c()
        if file:
            with open(file, 'w+') as outfile:
                outfile.write(c)
        else:
            return c

    def save(self, filename):
        with open(filename, 'wb') as outfile:
            pickle.dump(self, outfile)

    @abstractmethod
    def __str__(self):
        pass

class Node(ABC):
    def __init__(self, depth=0):
        self.left = None
        self.right = None
        self.trained_label = None  # the label from the training data the node sees (e.g. unique)
        self.mapped_label = None  # the label corresponding to the actual int labels
        self.actual_label = None  # the actual float label
        self.depth = depth
        self.num_nodes = 0

    @abstractmethod
    def test_condition(self, x):
        pass

    def fit(self, X, y):
        if self.check_done(X, y):
            return
        mask = self.find_split(X, y)
        self.left = self.create_child_node()
        self.right = self.create_child_node()
        self.fit_children(X, y, mask)

    @abstractmethod
    def create_child_node(self):
        pass

    def check_done(self, X, y):
        if self.depth >= 500:
            print("Cannot find a good split.")
            return True

        unique_labels = np.unique(y)
        num_unique_labels = len(unique_labels)
        unique_data = np.unique(X, axis=0)
        num_unique_data = len(unique_data)
        if num_unique_labels <= 1 or num_unique_data <= 1:
            self.trained_label = y[0] if len(unique_labels) > 0 else None
            self.num_nodes = 1
            return True
        return False

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
            text += '{} -> {} [label="{}"];\n'.format(starting_number, number_for_right, label)
            last_number = last_right_number

        return last_number, text

    def export_c(self):
        return self._export_c(0)

    def _export_c(self, indent_index):
        # If leaf node
        if not self.left and not self.right:
            return "\t" * indent_index + self.get_c_label()

        text = ""
        text += "\t" * indent_index + f"if ({self.get_c_label()}) {{\n"
        if self.left:
            text += f"{self.left._export_c(indent_index + 1)}\n"
        else:
            text += "\t" * (indent_index + 1) + ";\n"
        text += "\t" * indent_index + "}\n"

        if self.right:
            text += "\t" * indent_index + "else {\n"
            text += f"{self.right._export_c(indent_index + 1)}\n"
            text += "\t" * indent_index + "}\n"

        return text

    @abstractmethod
    def get_dot_label(self):
        pass

    @abstractmethod
    def print_dot_red(self):
        pass

    @abstractmethod
    def get_c_label(self):
        # if non-leaf, return test condition; else return class
        pass