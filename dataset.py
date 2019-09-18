import pandas as pd
import numpy as np
import os
from sklearn.metrics import accuracy_score
from label_format import LabelFormat

class Dataset:
    """
    :param any_label: indicates whether this dataset is a multi-label dataset where any of the given labels is
    considered correct
    """

    def __init__(self, X_file, Y_file):
        self.name = Dataset.get_dataset_name(X_file)
        self.X_train = np.array(pd.read_pickle(X_file))
        self.Y_train = np.load(Y_file)
        self.combination_label_mapping = {}

    @staticmethod
    def get_dataset_name(file):
        return os.path.basename(file).replace('_X.pickle', '')

    def get_labels_for_format(self, label_format):
        if label_format == LabelFormat.VECTOR:
            return self.get_vector_labels()
        elif label_format == LabelFormat.COMBINATIONS:
            return self.get_combination_labels()
        elif label_format == LabelFormat.MAX:
            return self.get_max_labels(self.Y_train)
        elif label_format == LabelFormat.MAX_EVERY_NODE:
            return self.get_vector_labels()

    def get_vector_labels(self):
        return self.Y_train

    def get_combination_labels(self):
        l = []
        next_unused_int = 0
        label_to_int = {}
        for i in range(len(self.Y_train)):
            label = ','.join([str(i) for i in self.Y_train[i]])
            if label not in label_to_int:
                next_unused_int += 1
                label_to_int[label] = next_unused_int
            new_label = label_to_int[label]
            self.combination_label_mapping[new_label] = self.Y_train[i]
            l.append(new_label)
        return np.array(l)

    @staticmethod
    def get_max_labels(y):
        label_counts = np.count_nonzero(y, axis=0)
        new_labels = []
        for i in range(len(y)):
            labels = y[i]
            max_label = max([i for i in range(len(labels)) if labels[i] == 1], key=lambda l: label_counts[l])
            new_labels.append(max_label)
        return np.array(new_labels)

    def compute_accuracy(self, classifier):
        Y_pred = classifier.predict(self.X_train)
        if len(Y_pred[Y_pred == None]) != 0:
            return None

        num_correct = 0
        for i in range(len(Y_pred)):
            if classifier.label_format == LabelFormat.VECTOR:
                pred = Y_pred[i]
            elif classifier.label_format == LabelFormat.COMBINATIONS:
                pred = self.combination_label_mapping[Y_pred[i]]
            else:
                pred = self.create_one_hot_vector(Y_pred[i], self.Y_train.shape[1])
            predicted_indices = set(np.nonzero(pred)[0])
            correct_indices = set(np.nonzero(self.Y_train[i])[0])
            if set.issubset(predicted_indices, correct_indices):
                num_correct += 1
        return num_correct / len(Y_pred)

    @staticmethod
    def create_one_hot_vector(index, length):
        return np.array([int(tmp == index) for tmp in range(length)])
