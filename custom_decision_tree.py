from label_format import LabelFormat
import numpy as np
from abc import ABC, abstractmethod
from sklearn.base import BaseEstimator
import sys

class CustomDecisionTree(ABC, BaseEstimator):
    def __init__(self):
        self.root = None
        self.label_format = LabelFormat.COMBINATIONS

    def fit(self, X, y):
        self.root = self.create_root_node()
        self.root.fit(X, y)

    @abstractmethod
    def create_root_node(self):
        pass

    def predict(self, X):
        pred = []
        for row in np.array(X):
            pred.append(self.classify_instance(row.reshape(1, -1)))
        return np.array(pred)

    def classify_instance(self, features):
        node = self.root
        while node.left:
            node = node.left if node.test_condition(features) else node.right
        return node.label

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

    @abstractmethod
    def __str__(self):
        pass

class Node(ABC):
    def __init__(self, depth=0):
        self.left = None
        self.right = None
        self.label = None
        self.depth = depth
        self.num_nodes = 0

    @abstractmethod
    def test_condition(self, x):
        pass

    def fit(self, X, y):
        if self.check_done(y):
            return
        mask = self.find_split(X, y)
        self.left = self.create_child_node()
        self.right = self.create_child_node()
        self.fit_children(X, y, mask)

    @abstractmethod
    def create_child_node(self):
        pass

    def check_done(self, y):
        if self.depth >= 500:
            print("Cannot find a good split.")
            return True

        unique_labels = np.unique(y)
        num_unique_labels = len(unique_labels)
        if num_unique_labels <= 1:
            self.label = y[0] if len(unique_labels) > 0 else None
            self.num_nodes = 1
            return True

    @abstractmethod
    def find_split(self, X, y):
        pass

    def fit_children(self, X, y, mask):
        self.left.fit(X[mask], y[mask])
        self.right.fit(X[~mask], y[~mask])
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
            text += '{} -> {};\n'.format(starting_number, starting_number + 1)
            number_for_right = last_left_number + 1
            last_number = last_left_number

        if self.right:
            last_right_number, right_text = self.right._export_dot(number_for_right)
            text += right_text
            text += '{} -> {};\n'.format(starting_number, number_for_right)
            last_number = last_right_number

        return last_number, text

    @abstractmethod
    def get_dot_label(self):
        pass

    @abstractmethod
    def print_dot_red(self):
        pass
