import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.exceptions import ConvergenceWarning
from custom_decision_tree import CustomDecisionTree, Node

import warnings

warnings.filterwarnings("ignore", category=ConvergenceWarning)

class LinearClassifierDecisionTree(CustomDecisionTree):
    def __init__(self, classifier_class, **kwargs):
        super().__init__()
        self.kwargs = kwargs
        self.classifier_class = classifier_class
        self.name = 'LinearClassifierDT({})'.format(classifier_class.__name__)

    def create_root_node(self):
        return LinearClassifierOrAxisAlignedNode(self.classifier_class, **self.kwargs)

    def get_stats(self):
        return {
            'num_nodes': self.root.num_nodes,
            'num_not_aa': self.root.num_not_axis_aligned
        }

    def __str__(self):
        return 'LinearClassifierDecisionTree'

class LinearClassifierOrAxisAlignedNode(Node):
    def __init__(self, classifier_class, depth=0, **kwargs):
        super().__init__(depth)
        self.classifier_class = classifier_class
        self.classifier = None
        self.kwargs = kwargs
        self.num_not_axis_aligned = 0

    def test_condition(self, x):
        if not self.is_axis_aligned():
            return self.classifier.predict(x)[0] == 0
        else:
            tree = self.classifier.tree_
            return x[:, tree.feature[0]][0] <= tree.threshold[0]

    def create_child_node(self):
        return LinearClassifierOrAxisAlignedNode(self.classifier_class, self.depth + 1, **self.kwargs)

    def fit_children(self, X, y, mask):
        super().fit_children(X, y, mask)
        self.num_not_axis_aligned = self.num_not_axis_aligned + self.left.num_not_axis_aligned + \
                                    self.right.num_not_axis_aligned

    def find_split(self, X, y):
        lc, lc_impurity, lc_mask = self.find_best_linear_classifier(X, y)
        dt, dt_impurity, dt_mask = self.find_best_axis_aligned_split(X, y)
        if dt_impurity <= lc_impurity:
            self.classifier = dt
            mask = dt_mask
        else:
            self.num_not_axis_aligned += 1
            self.classifier = lc
            mask = lc_mask
        return mask

    def find_best_linear_classifier(self, X, y):
        label_to_impurity = {}
        label_to_classifier = {}
        for label in np.unique(y):
            new_y = np.copy(y)
            label_mask = (new_y == label)
            new_y[label_mask] = 1
            new_y[~label_mask] = 0
            classifier = self.classifier_class(**self.kwargs)
            classifier.fit(X, new_y)
            label_to_classifier[label] = classifier
            pred = classifier.predict(X)
            impurity = self.calculate_impurity(y, (pred == 0))
            label_to_impurity[label] = impurity

        min_impurity = min(label_to_impurity.values())
        label = min(label_to_impurity.items(), key=lambda x: x[1])[0]
        classifier = label_to_classifier[label]
        mask = (classifier.predict(X) == 0)
        return classifier, min_impurity, mask

    def find_best_axis_aligned_split(self, X, y):
        dt = DecisionTreeClassifier(max_depth=1, criterion='entropy')
        dt.fit(X, y)
        dt_mask = X[:, dt.tree_.feature[0]] <= dt.tree_.threshold[0]
        return dt, self.calculate_impurity(y, dt_mask), dt_mask

    def is_axis_aligned(self):
        return not isinstance(self.classifier, self.classifier_class)

    def get_dot_label(self):
        if self.label is not None:
            return f'Leaf({self.label})'
        if self.is_axis_aligned():
            tree = self.classifier.tree_
            return f'X[{tree.feature[0]}] <= {round(tree.threshold[0], 4)}'
        else:
            return 'LC'

    def print_dot_red(self):
        return not self.is_axis_aligned()
