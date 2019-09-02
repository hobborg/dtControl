import pandas as pd
import numpy as np
import os
from sklearn.metrics import accuracy_score

class Dataset:
    """
    :param any_label: indicates whether this dataset is a multi-label dataset where any of the given labels is
    considered correct
    """
    def __init__(self, X_file, Y_file, any_label=False):
        self.name = Dataset.get_dataset_name(X_file)
        self.X_train = np.array(pd.read_pickle(X_file))
        self.Y_train = np.load(Y_file)
        self.any_label = any_label

    @staticmethod
    def get_dataset_name(file):
        return os.path.basename(file).replace('_X.pickle', '')

    def get_labels_as_unique(self):
        l = []
        next_unused_int = 0
        label_to_int = {}
        for i in range(len(self.Y_train)):
            label = ','.join([str(i) for i in self.Y_train[i]])
            if label not in label_to_int:
                next_unused_int += 1
                label_to_int[label] = next_unused_int
            l.append(label_to_int[label])
        return np.array(l)

    def compute_accuracy(self, classifier):
        Y_pred = classifier.predict(self.X_train)
        if len(Y_pred[Y_pred == None]) != 0:
            return None
        if classifier.needs_unique_labels:
            return accuracy_score(self.get_labels_as_unique(), Y_pred)
        if not self.any_label:
            return accuracy_score(self.Y_train, Y_pred)

        num_correct = 0
        for i in range(len(Y_pred)):
            if set.issubset(set(Y_pred[i]), set(self.Y_train[i])):
                num_correct += 1
        return num_correct / len(Y_pred)
