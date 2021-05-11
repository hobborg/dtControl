from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from dtcontrol.dataset.csv_dataset_loader import CSVDatasetLoader
from dtcontrol.dataset.prism_dataset_loader import PrismDatasetLoader
from dtcontrol.dataset.scots_dataset_loader import ScotsDatasetLoader
from dtcontrol.dataset.storm_dataset_loader import StormDatasetLoader
from dtcontrol.dataset.uppaal_dataset_loader import UppaalDatasetLoader
from dtcontrol.util import get_filename_and_relevant_extension


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
        self.name, self.extension = get_filename_and_relevant_extension(filename)
        self.extension_to_loader = {
            '.scs': ScotsDatasetLoader(),
            '.dump': UppaalDatasetLoader(),
            '.csv': CSVDatasetLoader(),
            '.prism': PrismDatasetLoader(),
            '.storm.json': StormDatasetLoader()
        }
        if self.extension not in self.extension_to_loader:
            raise ValueError('Unknown file format.')
        self.x = None
        self.numeric_x = None
        self.categorical_x = None

        # In case all splitting strategies are numeric, this variable is set to true so that
        # numeric splitting strategies can work on the categorical variables
        self.treat_categorical_as_numeric = False

        self.x_metadata = {"variables": None, "categorical": None, "category_names": None,
                           "min": None, "max": None, "step_size": None}
        self.y = None
        self.y_metadata = {"categorical": None, "category_names": None, "min": None, "max": None, "step_size": None,
                           'num_rows': None, 'num_flattened': None, 'num_unique_labels': None}
        self.index_to_actual = {}  # mapping from arbitrary integer indices to the actual float/categorical labels
        self.numeric_feature_mapping = {}  # maps indices in the numeric array to the actual column index in x
        self.numeric_columns = None
        self.categorical_feature_mapping = {}  # the same thing for the categorical array
        self.categorical_columns = None
        self.is_deterministic = None
        self.parent_mask = None  # if this is a subset, parent_mask saves the mask into the parent dataset
        self.tranformed_x = {} # numeric_x transformed to higher dimensional space: {key -> transformed data set}
        self.feature_importance = None

    def get_name(self):
        return self.name

    def copy_from_other_dataset(self, ds):
        self.x = ds.x
        self.numeric_x = None
        self.tranformed_x = {}
        self.numeric_columns = None
        self.categorical_x = None
        self.x_metadata = ds.x_metadata
        self.y = ds.y
        self.y_metadata = ds.y_metadata
        self.index_to_actual = ds.index_to_actual
        self.numeric_feature_mapping = ds.numeric_feature_mapping
        self.categorical_feature_mapping = ds.categorical_feature_mapping
        self.is_deterministic = ds.is_deterministic
        self.treat_categorical_as_numeric = ds.treat_categorical_as_numeric
        self.feature_importance = ds.feature_importance

    def load_if_necessary(self):
        if self.x is None:
            self.x, self.x_metadata, self.y, self.y_metadata, self.index_to_actual = \
                self.extension_to_loader[self.extension].load_dataset(self.filename)
            assert len([i for i in self.index_to_actual if i == 0]) == 0  # labels have to start with 1 because of OC1
            self.y_metadata['num_rows'] = len(self.x)
            self.y_metadata['num_flattened'] = sum(1 for row in self.y for y in row)
            self.y_metadata['num_unique_labels'] = len(np.unique(self.get_unique_labels()))
            self.feature_importance = self.calc_all_feature_importance()

    def load_metadata_from_json(self, json_object):
        metadata = json_object['metadata']
        self.x_metadata = metadata['X_metadata']
        self.y_metadata = metadata['Y_metadata']

    def check_loaded(self):
        if self.x is None:
            raise RuntimeError('Dataset is not loaded.')

    def get_numeric_x(self, min_feature_importance=1e-9):
        if self.numeric_x is None:
            if self.treat_categorical_as_numeric:
                self.numeric_columns = set(range(self.x.shape[1]))
            else:
                self.numeric_columns = set(range(self.x.shape[1])).difference(set(self.x_metadata['categorical']))
            irrelevant_cols = {col for col in range(self.x.shape[1]) if self.feature_importance[col] < min_feature_importance} 
            self.numeric_columns -= irrelevant_cols
            self.numeric_columns = sorted(list(self.numeric_columns))
            self.numeric_feature_mapping = {i: self.numeric_columns[i] for i in range(len(self.numeric_columns))}
            self.numeric_x = self.x[:, self.numeric_columns]
        return self.numeric_x

    def get_categorical_x(self):
        if self.categorical_x is None:
            self.categorical_columns = self.x_metadata['categorical']
            self.categorical_feature_mapping = {i: self.categorical_columns[i] for i in
                                                range(len(self.categorical_columns))}
            self.categorical_x = self.x[:, self.categorical_columns]
        return self.categorical_x

    def get_transformed_x(self, transformer, key):
        # returns a cached transformed dataset (e.g. with add. features x1^2)
        # or calculates it and caches it then
        if self.tranformed_x.get(key) is None:
            self.tranformed_x[key] = transformer(self.get_numeric_x())
        return self.tranformed_x[key]

    def set_treat_categorical_as_numeric(self):
        self.treat_categorical_as_numeric = True

    def map_numeric_feature_back(self, feature):
        return self.numeric_feature_mapping[feature]

    def map_categorical_feature_back(self, feature):
        return self.categorical_feature_mapping[feature]

    def calc_all_feature_importance(self):
        """
        Returns an array of values ∈ [0., 1.] for every feature with 
        0.0: the feature has no impact
        1.0: the feature is very important

        Note that this only gives an approximation for the *most permissive* controller.
        """
        # Keep track of already ignored features so that we do not ignore both
        # features in this example:
        # |    X
        # | O   
        # +----->
        featureImportance = []
        ignoredFeatures = [] 
        for i in range(self.x.shape[1]):
            imp = self.calc_single_feature_importance(i, ignoredFeatures)
            featureImportance.append(imp)
            if imp == 0:
                ignoredFeatures.append(i)
        return featureImportance
    
    @abstractmethod
    def calc_single_feature_importance(self, featureInd, ignoredFeatures):
        # implementation depends on whether ys is single or multi output
        pass

    def calc_feature_importance_for_y(self, featureInd, y, ignoredFeatures):
        x = self.x
        fVals = np.unique(x[:, featureInd])
        if len(fVals) <= 1:
            return 0 # feature is constant -> no information
        # leave out the feature (and all already ignored ones)
        # group same x-values
        # then see if all those have the same label
        xInds = [i for i in range(x.shape[1])
                    if i != featureInd and not i in ignoredFeatures]
        yInds = list(range(x.shape[1], x.shape[1] + y.shape[1]))
        xy = np.concatenate((x,y), axis=1)
        df = pd.DataFrame(xy)
        df = df.groupby(xInds).nunique()[yInds]
        # df : y1, y2, y3
        #    :  1,  3,  2
        #    :  1,  1,  1
        df = (df == [1 for _ in yInds]).all(axis=1)
        eqCnt = df.sum()
        nonEqCnt = (~df).sum()
        tot = eqCnt + nonEqCnt
        return nonEqCnt / tot

    def __len__(self):
        return len(self.x)

    @abstractmethod
    def compute_accuracy(self, y_pred):
        pass

    @abstractmethod
    def get_single_labels(self):
        """
        Converts multi-output labels to the tuple-id-representation, resulting in single-output labels that are
        returned.
        For a SingleOutputDataset, simply returns y.
        """
        pass

    @abstractmethod
    def map_single_label_back(self, single_label):
        """
        For a multi-output dataset, returns the tuple corresponding to the tuple id.
        For a single-output dataset, simply returns the single-label.
        """
        pass

    @abstractmethod
    def get_unique_labels(self):
        """
        Returns a label representation in which each combination of possible labels occurring in the data is
        assigned a new unique label.
        """
        pass

    def index_label_to_actual(self, index_label):
        """
        :param index_label: the index label
        :returns: the actual (float/categorical) label, which can either be a single label, a single tuple, a list of
                  labels, or a list of tuples
        """
        if isinstance(index_label, tuple):  # single tuple
            return tuple([self.index_to_actual[i] for i in index_label if i != -1])
        elif isinstance(index_label, list):
            if isinstance(index_label[0], tuple):  # list of tuples
                return [tuple(map(lambda x: self.index_to_actual[x], tup)) for tup in index_label]
            else:  # list of labels
                return [self.index_to_actual[i] for i in index_label if i != -1]
        else:  # single label
            return self.index_to_actual[index_label]

    @abstractmethod
    def map_unique_label_back(self, label):
        """
        :param label: the unique label
        :return: the corresponding index (int) label
        """
        pass

    @abstractmethod
    def from_mask(self, mask):
        """
        Returns the subset given by the mask.
        :param mask: a numpy array of 0s and 1s with len(mask) == num_examples
        """
        pass

    @abstractmethod
    def from_mask_optimized(self, mask):
        """
        An optimized version of the from_mask method that only copies the labels. This is used inside the critical
        impurity measure code.
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
