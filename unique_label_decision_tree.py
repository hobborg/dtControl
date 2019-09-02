from sklearn.tree import DecisionTreeClassifier, export_graphviz

class UniqueLabelDecisionTree:
    def __init__(self, **kwargs):
        self.name = 'UniqueLabelDecisionTree'
        self.needs_unique_labels = True
        self.dt = DecisionTreeClassifier(**kwargs)

    def get_stats(self):
        return {
            'num_nodes': self.dt.tree_.node_count
        }

    def fit(self, X_train, Y_train):
        self.dt.fit(X_train, Y_train)

    def predict(self, X):
        return self.dt.predict(X)
