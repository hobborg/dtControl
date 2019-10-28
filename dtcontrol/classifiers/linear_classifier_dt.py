import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.tree import DecisionTreeClassifier

import dtcontrol.util
from dtcontrol.classifiers.custom_dt import CustomDT, Node

# SVM sometimes does not converge and clutters the output with warnings
warnings.filterwarnings("ignore", category=ConvergenceWarning)

class LinearClassifierDT(CustomDT):
    def __init__(self, classifier_class, **kwargs):
        super().__init__()
        self.kwargs = kwargs
        self.classifier_class = classifier_class
        self.name = 'LinearClassifierDT-{}'.format(classifier_class.__name__)

    def is_applicable(self, dataset):
        return True

    def fit(self, dataset):
        self.root = LinearClassifierOrAxisAlignedNode(self.classifier_class, **self.kwargs)
        self.root.fit(dataset.X_train, dataset.get_unique_labels())
        self.set_labels(lambda leaf: dataset.map_unique_label_back(leaf.trained_label), dataset.index_to_value)

    def get_stats(self) -> dict:
        return {
            'nodes': self.root.num_nodes,
            'oblique': self.root.num_not_axis_aligned,
            'bandwidth': int(np.ceil(np.log2((self.root.num_nodes + 1)/2)))
        }

class LinearClassifierOrAxisAlignedNode(Node):
    def __init__(self, classifier_class, depth=0, **kwargs):
        super().__init__(depth)
        self.classifier_class = classifier_class
        self.classifier = None
        self.kwargs = kwargs
        self.num_not_axis_aligned = 0

    def test_condition(self, x):
        if not self.is_axis_aligned():
            return self.classifier.predict(x)[0] == -1
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
            new_y[~label_mask] = -1
            classifier = self.classifier_class(**self.kwargs)
            classifier.fit(X, new_y)
            label_to_classifier[label] = classifier
            pred = classifier.predict(X)
            impurity = self.calculate_impurity(y, (pred == -1))
            label_to_impurity[label] = impurity

        min_impurity = min(label_to_impurity.values())
        label = min(label_to_impurity.items(), key=lambda x: x[1])[0]
        classifier = label_to_classifier[label]
        mask = (classifier.predict(X) == -1)
        return classifier, min_impurity, mask

    def find_best_axis_aligned_split(self, X, y):
        dt = DecisionTreeClassifier(max_depth=1, criterion='entropy')
        dt.fit(X, y)
        dt_mask = X[:, dt.tree_.feature[0]] <= dt.tree_.threshold[0]
        return dt, self.calculate_impurity(y, dt_mask), dt_mask

    def is_axis_aligned(self):
        return not isinstance(self.classifier, self.classifier_class)

    def get_dot_label(self):
        if self.actual_label is not None:
            rounded = dtcontrol.util.objround(self.actual_label, 6) # TODO get precision from flag?
            return dtcontrol.util.split_into_lines(rounded)
        if self.is_axis_aligned():
            tree = self.classifier.tree_
            return f'X[{tree.feature[0]}] <= {round(tree.threshold[0], 6)}'  # TODO get precision from flag?
        else:
            # this implicitly assumes n_classes == 2
            coef_ = self.classifier.coef_[0]
            intercept_ = self.classifier.intercept_[0]
            line = []
            for i in range(len(coef_)):
                line.append(f"{round(coef_[i], 6)}*X[{i}]")  # TODO get precision from flag?
            line.append(f"{round(intercept_, 6)}")  # TODO get precision from flag?
            hyperplane = "\n+".join(line) + " <= 0"
            return hyperplane.replace('+-', '-')

    def print_dot_red(self):
        return False
