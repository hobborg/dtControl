from sklearn.tree import DecisionTreeClassifier
from label_format import LabelFormat

class DecisionTreeWrapper:
    def __init__(self, **kwargs):
        self.name = 'DT'
        self.dt = DecisionTreeClassifier(**kwargs)
        self.label_format = LabelFormat.VECTOR

    def get_stats(self):
        return {
            'num_nodes': self.dt.tree_.node_count,
            'filename': self.get_filename()
        }

    def get_filename():
        pass

    def fit(self, X_train, Y_train):
        self.dt.fit(X_train, Y_train)

    def predict(self, X):
        return self.dt.predict(X)
