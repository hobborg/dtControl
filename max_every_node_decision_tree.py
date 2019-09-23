import sys
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.exceptions import ConvergenceWarning
from dataset import AnyLabelDataset
from label_format import LabelFormat

import warnings

from smarter_splits.LinearClassifierDecisionTree import LinearClassifierDecisionTree, Node

class MaxEveryNodeDecisionTree(LinearClassifierDecisionTree):
    def __init__(self, classifierClass, **kwargs):
        super().__init__(classifierClass, **kwargs)
        self.name = 'MaxEveryNodeDT({})'.format(classifierClass.__name__)
        self.label_format = LabelFormat.MAX_EVERY_NODE

    def fit(self, X, y):
        self.root = MaxNode(self.classifierClass, **self.kwargs)
        self.root.fit(X, y)

    def __str__(self):
        return 'MaxEveryNodeDecisionTree'

class MaxNode(Node):
    def __init__(self, classifier_class, depth=0, **kwargs):
        super().__init__(classifier_class, depth, **kwargs)

    def fit(self, X, y):
        new_labels = AnyLabelDataset.get_max_labels(y)
        mask, done = super().find_split(X, new_labels)
        if not done:
            self.left = MaxNode(self.classifier_class, self.depth + 1, **self.kwargs)
            self.right = MaxNode(self.classifier_class, self.depth + 1, **self.kwargs)
            super().fit_children(X, y, mask)
