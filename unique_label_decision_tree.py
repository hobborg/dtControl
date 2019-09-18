from sklearn.tree import DecisionTreeClassifier, export_graphviz
from label_format import LabelFormat

class UniqueLabelDecisionTree:
    def __init__(self, **kwargs):
        self.name = 'UniqueLabelDT'
        self.dt = DecisionTreeClassifier(**kwargs)
        self.label_format = LabelFormat.COMBINATIONS

    def get_stats(self):
        return {
            'num_nodes': self.dt.tree_.node_count
        }

    def fit(self, X_train, Y_train):
        self.dt.fit(X_train, Y_train)

    def predict(self, X):
        return self.dt.predict(X)
