import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

from dtcontrol.decision_tree.impurity.impurity_measure import ImpurityMeasure

class FScore(ImpurityMeasure):
    def calculate_impurity(self, x, y, mask):
        left_labels = y[mask]
        right_labels = y[~mask]
        left = self.calculate_fscore(x[mask], left_labels)
        right = self.calculate_fscore(x[~mask], right_labels)
        if left == 0 or right == 0:
            return sys.maxsize
        return 1 / ((len(left_labels) / len(y)) * left + (len(right_labels) / len(y)) * right)

    @staticmethod
    def calculate_fscore(x, y):
        if len(y) == 0:
            return 0
        unique_labels = np.unique(y)
        if len(unique_labels) == 1:
            return 1  # perfect split
        logreg = LogisticRegression(solver='lbfgs', penalty='none', multi_class='multinomial', n_jobs=-1)
        logreg.fit(x, y)
        return f1_score(y, logreg.predict(x), average='weighted')
