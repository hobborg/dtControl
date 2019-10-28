from abc import ABC, abstractmethod

import numpy as np

from dtcontrol.dataset.scots_dataset_loader import ScotsDatasetLoader
from dtcontrol.dataset.uppaal_dataset_loader import UppaalDatasetLoader
from dtcontrol.dataset.vector_dataset_loader import VectorDatasetLoader
from dtcontrol.dataset.csv_dataset_loader import CSVDatasetLoader
from dtcontrol.util import get_filename_and_ext


class Dataset(ABC):
    """
    Attributes:
        X_train: the training data of shape (num_states, num_state_dims)
        Y_train:
            Multi-output: the training labels of shape (num_input_dims, num_states, max_non_determinism)
                For example:  [ [[1  2 -1]  [[4  5 -1]
                                [2  3 -1]   [4  6 -1]
                                [1  2  3]   [4  6  6]
                                [1 -1 -1]]  [5 -1 -1]] ]
                has the shape (2, 4, 3) as there are two control inputs, 4 states and
                at most 3 non-deterministic choices for each state.

                The Y_train in the above example can be thought of a list [y1, y2]
                where y1 gives the values for the first control input and y2 gives
                the values for the second control input. Let us for example see
                which inputs are allowed for the 2nd state.

                y1[1] = [2  3 -1] and y2[1] = [4  6 -1]

                This means that the allowed control inputs for the 2nd state are
                (2, 4) and (3, 6). The -1 is a filler just to make the length of
                the lists  = max_non_determinism.

                Use np.stack(Y_train, axis=2) in order to get an array of the form
                [[[1  4], [ 2  5], [-1 -1]],
                 [[2  4], [ 3  6], [-1 -1]]
                 [[1  4], [ 2  6], [ 3  6]]
                 [[1  5], [-1 -1], [-1 -1]]

                from which it is easier to extract control actions as tuples.
            Single-output: the training labels of shape (num_states, max_non_determinism)
                For example:   [[1  2 -1]
                                [2  3 -1]
                                [1  2  3]
                                [1 -1 -1]]
                has the shape (4, 3) as there are 4 states and at most 3 non-deterministic
                choices for each state.

                Y_train[i] gives the allowed control inputs for the ith state. -1 is a
                filler just to make the length of the lists  = max_non_determinism.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name, self.extension = get_filename_and_ext(filename)
        self.extension_to_loader = {
            '.vector': VectorDatasetLoader(),
            '.scs': ScotsDatasetLoader(),
            '.dump': UppaalDatasetLoader(),
            '.csv': CSVDatasetLoader(),
        }
        if self.extension not in self.extension_to_loader:
            raise ValueError('Unknown file format.')
        self.X_train = None
        self.X_metadata = {"variables": None, "min": None, "max": None, "step_size": None}
        self.Y_train = None
        self.Y_metadata = {"variables": None, "min": None, "max": None, "step_size": None, 'num_rows': None, 'num_flattened': None}
        self.index_to_value = {}
        self.is_deterministic = None

    def load_if_necessary(self):
        if self.X_train is None:
            self.X_train, self.X_metadata, self.Y_train, self.Y_metadata, self.index_to_value = self.extension_to_loader[
                self.extension].load_dataset(self.filename)
            self.Y_metadata['num_rows'] = len(self.X_train)
            self.Y_metadata['num_flattened'] = sum(1 for row in self.Y_train for y in row)

    def load_metadata_from_json(self, json):
        metadata = json['metadata']
        self.X_metadata = metadata['X_metadata']
        self.Y_metadata = metadata['Y_metadata']

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
            label_str = ','.join(sorted([str(i) for i in labels[i] if i != -1]))
            if label_str not in label_str_to_int:
                label_str_to_int[label_str] = next_unused_int
                int_to_label[next_unused_int] = labels[i]
                next_unused_int += 1
            new_label = label_str_to_int[label_str]
            l.append(new_label)
        return np.array(l), int_to_label

    @staticmethod
    def _get_max_labels(labels):
        flattened_labels = labels.flatten()
        # remove -1 as we use it only as a filler
        flattened_labels = flattened_labels[flattened_labels != -1]
        label_counts = np.bincount(flattened_labels)
        new_labels = []
        for i in range(len(labels)):
            current = labels[i]
            current = current[current != -1]
            max_label = max(list(current), key=lambda l: label_counts[l])
            assert max_label != -1
            new_labels.append(max_label)
        return np.array(new_labels)
