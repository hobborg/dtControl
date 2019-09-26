import pandas as pd
import numpy as np
import os
from sklearn.metrics import accuracy_score
from label_format import LabelFormat
from abc import ABC, abstractmethod

class Dataset(ABC):
    def __init__(self, X_file, Y_file):
        self.name = self.get_dataset_name(X_file)
        self.X_file = X_file
        self.Y_file = Y_file
        self.X_train = None
        self.Y_train = None
        self.combination_label_mapping = {}
        self.label_format_to_labels = None

    def load_if_necessary(self):
        if self.X_train is None:
            self.X_train = np.array(pd.read_pickle(self.X_file))
            self.Y_train = np.load(self.Y_file)

    def check_loaded(self):
        if self.X_train is None:
            raise RuntimeError('Dataset is not loaded.')

    @staticmethod
    def get_dataset_name(file):
        return os.path.basename(file).replace('_X.pickle', '')

    @abstractmethod
    def is_applicable(self, label_format):
        pass

    def get_labels_for_format(self, label_format):
        self.check_loaded()
        if not self.is_applicable(label_format):
            raise ValueError(f'Dataset is not applicable to {label_format}.')
        return self.label_format_to_labels[label_format]()

    def get_combination_labels(self):
        self.check_loaded()
        l = []
        next_unused_int = 0
        label_to_int = {}
        for i in range(len(self.Y_train)):
            label = ','.join([str(i) for i in self.Y_train[i]])
            if label not in label_to_int:
                label_to_int[label] = next_unused_int
                self.combination_label_mapping[next_unused_int] = self.Y_train[i]
                next_unused_int += 1
            new_label = label_to_int[label]
            l.append(new_label)
        return np.array(l)

    @abstractmethod
    def compute_accuracy(self, Y_pred, label_format):
        pass

class AnyLabelDataset(Dataset):
    def __init__(self, X_file, Y_file):
        super().__init__(X_file, Y_file)
        self.label_format_to_labels = {
            LabelFormat.VECTOR: lambda: self.Y_train,
            LabelFormat.COMBINATIONS: lambda: self.get_combination_labels(),  # lambda to delay computation
            LabelFormat.MAX: lambda: self.get_max_labels(self.Y_train),
            LabelFormat.MAX_EVERY_NODE: lambda: self.Y_train
        }

    def is_applicable(self, label_format):
        return label_format is not LabelFormat.MULTI

    @staticmethod
    def get_max_labels(y):
        label_counts = np.count_nonzero(y, axis=0)
        new_labels = []
        for i in range(len(y)):
            labels = y[i]
            max_label = max([i for i in range(len(labels)) if labels[i] == 1], key=lambda l: label_counts[l])
            new_labels.append(max_label)
        return np.array(new_labels)

    def compute_accuracy(self, Y_pred, label_format):
        self.check_loaded()
        if len(Y_pred[Y_pred == None]) != 0:
            return None
        num_correct = 0
        for i in range(len(Y_pred)):
            if label_format == LabelFormat.VECTOR:
                pred = Y_pred[i]
            elif label_format == LabelFormat.COMBINATIONS:
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

class MultiOutputDataset(Dataset):
    def __init__(self, X_file, Y_file):
        super().__init__(X_file, Y_file)
        self.multi_label_mapping = {}
        self.label_format_to_labels = {
            LabelFormat.COMBINATIONS: lambda: self.get_combination_labels(),
            LabelFormat.MULTI: lambda: self.get_multi_labels()
        }

    def get_multi_labels(self):
        """
        :return: a numpy array of the labels in integer format
        """
        self.check_loaded()
        l = []
        next_unused_int = 0
        label_to_int = {}
        for i in range(len(self.Y_train)):
            inner = []
            for j in range(self.Y_train.shape[1]):
                label = self.Y_train[i, j]
                if label not in label_to_int:
                    label_to_int[label] = next_unused_int
                    self.multi_label_mapping[next_unused_int] = label
                    next_unused_int += 1
                new_label = label_to_int[label]
                inner.append(new_label)
            l.append(inner)
        return np.array(l)

    def is_applicable(self, label_format):
        return label_format in [LabelFormat.MULTI, LabelFormat.COMBINATIONS]

    def compute_accuracy(self, Y_pred, label_format):
        self.check_loaded()
        if len(Y_pred[Y_pred == None]) != 0:
            return None
        labels = self.get_labels_for_format(label_format)
        if label_format == LabelFormat.COMBINATIONS:
            return accuracy_score(labels, Y_pred)
        return sum(int(np.all(Y_pred[i] == labels[i])) for i in range(len(labels))) / len(labels)
