from sklearn.tree import DecisionTreeClassifier
from label_format import LabelFormat
import time
import pickle
from os import makedirs
from os.path import isdir

class DecisionTreeWrapper:
    def __init__(self, **kwargs):
        self.name = 'DT'
        self.dt = DecisionTreeClassifier(**kwargs)
        self.label_format = LabelFormat.VECTOR
        self.last_saved_file = ""

    def get_stats(self):
        return {
            'num_nodes': self.dt.tree_.node_count,
            'filename': self.last_saved_file
        }

    def fit(self, X_train, Y_train):
        self.dt.fit(X_train, Y_train)

    def predict(self, X):
        return self.dt.predict(X)

    def save_classifier(self, save_location='models/classifiers'):
        if not isdir(save_location):
            makedirs(save_location)
        assert isdir(save_location)
        timestr = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{save_location}/{self.name}-{timestr}.pickle"
        file = open(filename, 'wb')
        pickle.dump(self, file)
        self.last_saved_file = filename