import pickle
from abc import ABC, abstractmethod
from os import makedirs
from os.path import getmtime, split, exists, join

import numpy as np
import pandas as pd

class DatasetLoader(ABC):
    def __init__(self):
        self.loaded_datasets = {}
        self.PATH = '.benchmark_suite'

    def load_dataset(self, filename):
        if filename not in self.loaded_datasets:
            if self.already_converted(filename):
                self.loaded_datasets[filename] = self.load_converted_dataset(filename)
            else:
                self.loaded_datasets[filename] = self._load_dataset(filename)
                self.save_converted_dataset(filename)
        return self.loaded_datasets[filename]

    def already_converted(self, filename):
        possible_path = self.get_converted_folder(filename)
        return exists(possible_path)

    def load_converted_dataset(self, filename):
        folder = self.get_converted_folder(filename)
        assert exists(folder)
        print("Loading existing pickled dataset...", end=' ')
        X_train = np.load(join(folder, 'X_train.npy'))
        Y_train = np.load(join(folder, 'Y_train.npy'))
        with open(join(folder, 'extra_data.pickle'), 'rb') as infile:
            extra_data = pickle.load(infile)
            index_to_value = extra_data["index_to_value"]
            X_metadata = extra_data["X_metadata"]
            Y_metadata = extra_data["Y_metadata"]
        print("done loading.")
        return X_train, X_metadata, Y_train, Y_metadata, index_to_value

    def save_converted_dataset(self, filename):
        folder = self.get_converted_folder(filename)
        if not exists(folder):
            makedirs(folder)
        X_train, X_metadata, Y_train, Y_metadata, index_to_value = self.loaded_datasets[filename]
        np.save(join(folder, 'X_train.npy'), X_train)
        np.save(join(folder, 'Y_train.npy'), Y_train)
        with open(join(folder, 'extra_data.pickle'), 'wb+') as outfile:
            pickle.dump({"index_to_value": index_to_value,
                         "X_metadata": X_metadata,
                         "Y_metadata": Y_metadata},
                        outfile)

    def get_converted_folder(self, filename):
        directory, name = split(filename)
        return join(directory, self.PATH, f'{name}_{getmtime(filename)}')

    """
    Loads a dataset and returns X_train, X_metadata, Y_train, Y_metadata, index_to_value
    """

    @abstractmethod
    def _load_dataset(self, filename):
        pass
