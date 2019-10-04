import numpy as np

class MediumCruiseDatasetClassifier:
    def __init__(self, **kwargs):
        self.name = 'MediumCruiseDatasetClassifier'
        self.needs_unique_labels = True

    def get_stats(self):
        return {
            'num_nodes': 3
        }

    def fit(self, X_train, Y_train):
        pass

    def predict(self, X):
        mask = X[:,1] <= 1
        pred = np.zeros((X.shape[0]))
        pred[mask] = 0
        pred[~mask] = 2
        return pred
