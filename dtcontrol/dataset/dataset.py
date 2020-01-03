from abc import ABC, abstractmethod

import numpy as np

from dtcontrol.dataset.csv_dataset_loader import CSVDatasetLoader
from dtcontrol.dataset.scots_dataset_loader import ScotsDatasetLoader
from dtcontrol.dataset.uppaal_dataset_loader import UppaalDatasetLoader
from dtcontrol.util import get_filename_and_ext

class Dataset(ABC):
    """
    Attributes:
        x: the training data of shape (num_states, num_state_dims)
        y:
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

                y[i] gives the allowed control inputs for the ith state. -1 is a
                filler just to make the length of the lists  = max_non_determinism.
    """

    def __init__(self, filename):
        self.filename = filename
        self.name, self.extension = get_filename_and_ext(filename)
        self.extension_to_loader = {
            '.scs': ScotsDatasetLoader(),
            '.dump': UppaalDatasetLoader(),
            '.csv': CSVDatasetLoader(),
        }
        if self.extension not in self.extension_to_loader:
            raise ValueError('Unknown file format.')
        self.x = None
        self.x_metadata = {"variables": None, "min": None, "max": None, "step_size": None}
        self.y = None
        self.y_metadata = {"variables": None, "min": None, "max": None, "step_size": None, 'num_rows': None,
                           'num_flattened': None}
        self.index_to_actual = {}  # mapping from arbitrary integer indices to the actual float labels
        self.is_deterministic = None

    def get_name(self):
        return self.name

    def copy_from_other_dataset(self, ds):
        self.x = ds.x
        self.x_metadata = ds.x_metadata
        self.y = ds.y
        self.y_metadata = ds.y_metadata
        self.index_to_actual = ds.index_to_actual
        self.is_deterministic = ds.is_deterministic

    def load_if_necessary(self):
        if self.x is None:
            self.x, self.x_metadata, self.y, self.y_metadata, self.index_to_actual = \
                self.extension_to_loader[self.extension].load_dataset(self.filename)
            self.y_metadata['num_rows'] = len(self.x)
            self.y_metadata['num_flattened'] = sum(1 for row in self.y for y in row)

    def load_metadata_from_json(self, json_object):
        metadata = json_object['metadata']
        self.x_metadata = metadata['X_metadata']
        self.y_metadata = metadata['Y_metadata']

    def check_loaded(self):
        if self.x is None:
            raise RuntimeError('Dataset is not loaded.')

    @abstractmethod
    def compute_accuracy(self, y_pred):
        pass

    @abstractmethod
    def get_unique_labels(self):
        """
        Returns a label representation in which each combination of possible labels occurring in the data is
        assigned a new unique label.
        """
        pass

    @abstractmethod
    def map_unique_label_back(self, label):
        """
        :param label: the unique label
        :return: the corresponding index (int) label
        """
        pass

    def split(self, mask):
        """
        Splits the dataset into two subsets, as indicated by the given mask.
        :param mask: a numpy array of 0s and 1s with len(mask) == num_examples
        """
        left = self.from_mask(mask)
        right = self.from_mask(~mask)
        return left, right

    @abstractmethod
    def from_mask(self, mask):
        """
        Returns the subset given by the mask.
        :param mask: a numpy array of 0s and 1s with len(mask) == num_examples
        """
        pass

    @staticmethod
    def get_unique_labels_from_2d(labels):
        """
        Computes unique labels of a 2d label array by mapping every unique inner array to an int. Returns the unique labels
        and the int mapping.
        """
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
