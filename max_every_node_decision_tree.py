import sys
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.base import BaseEstimator
from dataset import AnyLabelDataset
from label_format import LabelFormat

import warnings

warnings.filterwarnings("ignore", category=ConvergenceWarning)

class MaxEveryNodeDecisionTree(BaseEstimator):
    def __init__(self, classifierClass, **kwargs):
        self.root = None
        self.kwargs = kwargs
        self.classifierClass = classifierClass
        self.name = 'MaxEveryNodeDT({})'.format(classifierClass.__name__)
        self.label_format = LabelFormat.MAX_EVERY_NODE

    def fit(self, X, y):
        self.root = Node(self.classifierClass, **self.kwargs)
        self.root.fit(X, y)

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
            'num_nodes': self.root.num_nodes,
            'num_not_aa': self.root.num_not_axis_aligned
        }

    def export_dot(self, file=None):
        dot = self.root.export_dot()
        if file:
            with open(file, 'w+') as outfile:
                outfile.write(dot)
        else:
            return dot

    def __str__(self):
        return 'MaxEveryNodeDecisionTree'

class Node:
    def __init__(self, classifierClass, depth=0, **kwargs):
        self.classifierClass = classifierClass
        self.classifier = None
        self.kwargs = kwargs
        self.left = None
        self.right = None
        self.label = None
        self.depth = depth
        self.num_nodes = 0
        self.num_not_axis_aligned = 0

    def test_condition(self, x):
        if not self.is_axis_aligned():
            return self.classifier.predict(x)[0] == 0
        else:
            tree = self.classifier.tree_
            return x[:, tree.feature[0]][0] <= tree.threshold[0]

    def fit(self, X, y):
        if self.depth >= 500:
            print("Cannot find a good split.")
            return

        new_labels = AnyLabelDataset.get_max_labels(y)
        unique_labels = np.unique(new_labels)
        num_unique_labels = len(unique_labels)
        if num_unique_labels <= 1:
            self.label = new_labels[0] if len(unique_labels) > 0 else None
            self.num_nodes = 1
            return

        label_to_impurity = {}
        label_to_classifier = {}
        for label in unique_labels:
            new_y = np.copy(new_labels)
            labelMask = (new_y == label)
            new_y[labelMask] = 1
            new_y[~labelMask] = 0
            classifier = self.classifierClass(**self.kwargs)
            classifier.fit(X, new_y)
            label_to_classifier[label] = classifier
            pred = classifier.predict(X)
            impurity = self.calculate_impurity(new_labels, (pred == 0))
            label_to_impurity[label] = impurity

        min_impurity = min(label_to_impurity.values())
        decisionTree = DecisionTreeClassifier(max_depth=1, criterion='entropy')
        decisionTree.fit(X, new_labels)
        decisionTreeMask = X[:, decisionTree.tree_.feature[0]] <= decisionTree.tree_.threshold[0]

        if self.calculate_impurity(y, decisionTreeMask) <= min_impurity:
            self.classifier = decisionTree
            mask = decisionTreeMask
        else:
            self.num_not_axis_aligned += 1
            label = min(label_to_impurity.items(), key=lambda x: x[1])[0]
            self.classifier = label_to_classifier[label]
            pred = self.classifier.predict(X)
            mask = (pred == 0)

        self.left = Node(self.classifierClass, self.depth + 1, **self.kwargs)
        self.right = Node(self.classifierClass, self.depth + 1, **self.kwargs)
        self.left.fit(X[mask], y[mask])
        self.right.fit(X[~mask], y[~mask])
        self.num_nodes = 1 + self.left.num_nodes + self.right.num_nodes
        self.num_not_axis_aligned = self.num_not_axis_aligned + self.left.num_not_axis_aligned + self.right.num_not_axis_aligned

    def calculate_impurity(self, labels, mask):
        left = labels[mask]
        right = labels[~mask]
        if len(left) == 0 or len(right) == 0: return sys.maxsize
        num_labels = len(labels)
        return (len(left) / num_labels) * self.calculate_entropy(left) + \
               (len(right) / num_labels) * self.calculate_entropy(right)

    def calculate_entropy(self, labels):
        num_labels = len(labels)
        unique = np.unique(labels)
        probs = [len(labels[labels == label]) / num_labels for label in unique]
        return sum(-prob * np.log2(prob) for prob in probs)

    def is_axis_aligned(self):
        return not isinstance(self.classifier, self.classifierClass)

    def export_dot(self):
        text = 'digraph {{\n{}\n}}'.format(self._export_dot(0)[1])
        return text

    def _export_dot(self, starting_number):
        if not self.left and not self.right:
            return starting_number, '{} [label=\"{}\"];\n'.format(starting_number, self.label)

        tag = 'AA' if self.is_axis_aligned() else 'SVM'
        if self.is_axis_aligned():
            tree = self.classifier.tree_
            tag = f'X[{tree.feature[0]}] <= {round(tree.threshold[0], 4)}'
        text = '{} [label=\"{}\"'.format(starting_number, tag)
        if not self.is_axis_aligned():
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
