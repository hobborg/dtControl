from sklearn.tree import DecisionTreeClassifier
import numpy as np
from label_format import LabelFormat

class MultiOutputDecisionTree:
    def __init__(self, **kwargs):
        self.name = 'MultiOutputDT'
        self.kwargs = kwargs
        self.label_format = LabelFormat.MULTI
        self.dts = []

    def get_stats(self):
        stats = {}
        for i in range(len(self.dts)):
            stats[f'num_nodes_{i}'] = self.dts[i].tree_.node_count
        return stats

    def fit(self, X_train, Y_train):
        for i in range(Y_train.shape[1]):
            dt = DecisionTreeClassifier(**self.kwargs)
            dt.fit(X_train, Y_train[:,i])
            self.dts.append(dt)

    def predict(self, X):
        preds = self.dts[0].predict(X)
        for dt in self.dts[1:]:
            preds = np.c_[preds, dt.predict(X)]
        return preds
