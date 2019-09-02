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
        self.unique_label_mapping = {}

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
            new_label = label_to_int[label]
            self.unique_label_mapping[new_label] = self.Y_train[i]
            l.append(new_label)
        return np.array(l)

    def get_labels_as_unique2(self):
        label_counts = np.count_nonzero(self.Y_train, axis=0)
        new_labels = []
        for i in range(len(self.Y_train)):
            labels = self.Y_train[i]
            max_label = max([i for i in range(len(labels)) if labels[i] == 1], key=lambda l: label_counts[l])
            new_labels.append(max_label)
        for i in range(self.Y_train.shape[1]):
            self.unique_label_mapping[i] = np.array([int(tmp == i) for tmp in range(self.Y_train.shape[1])])
        return np.array(new_labels)

    def compute_accuracy(self, classifier):
        Y_pred = classifier.predict(self.X_train)
        if len(Y_pred[Y_pred == None]) != 0:
            return None
        if not self.any_label:
            return accuracy_score(self.Y_train, Y_pred)

        num_correct = 0
        for i in range(len(Y_pred)):
            pred = self.unique_label_mapping[Y_pred[i]] if classifier.needs_unique_labels else Y_pred[i]
            predicted_indices = set(np.nonzero(pred)[0])
            correct_indices = set(np.nonzero(self.Y_train[i])[0])
            if set.issubset(predicted_indices, correct_indices):
                num_correct += 1
        return num_correct / len(Y_pred)
