from abc import ABC, abstractmethod

import numpy as np

from dataset.vector_dataset_loader import VectorDatasetLoader
from util import get_filename_and_ext

class Dataset(ABC):
    def __init__(self, filename):
        self.filename = filename
        self.name, self.extension = get_filename_and_ext(filename)
        self.extension_to_loader = {
            '.vector': VectorDatasetLoader()
        }
        if self.extension not in self.extension_to_loader:
            raise ValueError('Unknown file format.')

        self.X_train = None
        self.X_vars = None
        self.Y_train = None
        self.index_to_value = {}

    def load_if_necessary(self):
        if self.X_train is None:
            X_train, X_vars, Y_train, index_to_value = self.extension_to_loader[self.extension] \
                .load_dataset(self.filename)
            self.X_train = X_train
            self.X_vars = X_vars
            self.Y_train = Y_train
            self.index_to_value = index_to_value

    def check_loaded(self):
        if self.X_train is None:
            raise RuntimeError('Dataset is not loaded.')

    @abstractmethod
    def compute_accuracy(self, Y_pred):
        pass

    @abstractmethod
    def get_unique_labels(self):
        pass

    @abstractmethod
    def map_unique_label_back(self, label):
        pass

    """
    Computes unique labels of a 2d label array by mapping every unique inner array to an int. Returns the unique labels
    and the int mapping.
    """
    @staticmethod
    def _get_unique_labels(labels):
        l = []
        int_to_label = {}
        next_unused_int = 1  # OC1 expects labels starting with 1
        label_str_to_int = {}
        for i in range(len(labels)):
            label_str = ','.join(sorted([str(i) for i in labels[i]]))
            if label_str not in label_str_to_int:
                label_str_to_int[label_str] = next_unused_int
                int_to_label[next_unused_int] = labels[i]
                next_unused_int += 1
            new_label = label_str_to_int[label_str]
            l.append(new_label)
        return np.array(l), int_to_label

    @staticmethod
    def _get_max_labels(labels):
        label_counts = np.bincount(labels.flatten())
        label_counts[0] = -1  # ignore count of zeros since we use it only as a filler
        new_labels = []
        for i in range(len(labels)):
            current = labels[i]
            max_label = max(list(current), key=lambda l: label_counts[l])
            assert max_label != -1
            new_labels.append(max_label)
        return np.array(new_labels)

    @staticmethod
    def _convert_floats_to_ints(labels):  # TODO: double-check if this works / remove if not needed
        l = []
        next_unused_int = 1  # OC1 expects labels starting with 1
        multi_label_mapping = {}
        label_to_int = {}
        for i in range(len(labels)):
            inner = []
            for j in range(labels.shape[1]):
                label = labels[i, j]
                if label not in label_to_int:
                    label_to_int[label] = next_unused_int
                    multi_label_mapping[next_unused_int] = label
                    next_unused_int += 1
                new_label = label_to_int[label]
                inner.append(new_label)
            l.append(inner)
        return np.array(l), multi_label_mapping
