import json
import logging
import pickle
from abc import ABC, abstractmethod
from os import makedirs
from os.path import getmtime, split, exists, join, splitext, isfile

import numpy as np

import dtcontrol.util as util
from dtcontrol.util import is_int

class DatasetLoader(ABC):
    def __init__(self):
        self.loaded_datasets = {}
        self.PATH = '.benchmark_suite'

    def load_dataset(self, filename):
        if filename not in self.loaded_datasets:
            if self.is_already_converted(filename):
                self.loaded_datasets[filename] = self.load_converted_dataset(filename)
            else:
                self.loaded_datasets[filename] = self.load_dataset_and_config(filename)
                self.save_converted_dataset(filename)
        return self.loaded_datasets[filename]

    def is_already_converted(self, filename):
        possible_path = self.get_converted_folder(filename)
        return exists(possible_path)

    def load_converted_dataset(self, filename):
        folder = self.get_converted_folder(filename)
        assert exists(folder)
        util.log_without_newline('Loading existing converted dataset...')
        x = np.load(join(folder, 'X_train.npy'))
        y = np.load(join(folder, 'Y_train.npy'))
        with open(join(folder, 'extra_data.pickle'), 'rb') as infile:
            extra_data = pickle.load(infile)
            index_to_actual = extra_data["index_to_value"]
            x_metadata = extra_data["X_metadata"]
            y_metadata = extra_data["Y_metadata"]
        logging.info(" Done.")
        return x, x_metadata, y, y_metadata, index_to_actual

    def save_converted_dataset(self, filename):
        folder = self.get_converted_folder(filename)
        if not exists(folder):
            makedirs(folder)
        x, x_metadata, y, y_metadata, index_to_actual = self.loaded_datasets[filename]
        np.save(join(folder, 'X_train.npy'), x)
        np.save(join(folder, 'Y_train.npy'), y)
        with open(join(folder, 'extra_data.pickle'), 'wb+') as outfile:
            pickle.dump({"index_to_value": index_to_actual,
                         "X_metadata": x_metadata,
                         "Y_metadata": y_metadata},
                        outfile)

    def get_converted_folder(self, filename):
        directory, name = split(filename)
        return join(directory, self.PATH, f'{name}_{getmtime(filename)}')

    def load_dataset_and_config(self, filename):
        tup = self._load_dataset(filename)
        name, _ = splitext(filename)
        config_name = name + '_config.json'
        if exists(config_name) and isfile(config_name):
            self.update_with_config(config_name, tup[0], tup[1])
        return tup

    @staticmethod
    def update_with_config(config_filename, x, x_metadata):
        with open(config_filename, 'r') as infile:
            config = json.load(infile)
        if 'column_types' in config:
            column_types = config['column_types']
            if 'categorical' in column_types:
                x_metadata['categorical'] = column_types['categorical']
            if 'numeric' in column_types:
                # columns are numeric by default, we only need to check for conflicts here
                if len(set(column_types['numeric']).intersection(column_types['categorical'])) != 0:
                    raise ValueError(f'\'{config_filename}\' contains columns marked as '
                                     f'categorical as well as numeric.')
        if 'column_names' in config:
            column_names = config['column_names']
            if len(column_names) != x.shape[1]:
                raise ValueError(f'\'{config_filename}\': the number of column names '
                                 f'does not match the actual number of columns.')
            x_metadata['variables'] = column_names

        if 'category_names' in config:
            category_names = config['category_names']
            column_to_index = {}
            for column in category_names:
                if not is_int(column):
                    try:
                        column_to_index[column] = x_metadata['variables'].index(column)
                    except ValueError:
                        raise ValueError(f'\'{config_filename}\': unknown column name in category_names.')
                else:
                    column_to_index[column] = int(column)
                if column_to_index[column] not in x_metadata['categorical']:
                    raise ValueError(f'\'{config_filename}\': numeric column in category_names.')
                num_distinct = len(np.unique(x[:, column_to_index[column]]))
                if num_distinct != len(category_names[column]):
                    raise ValueError(f'\'{config_filename}\':{column}: number of category names does not '
                                     f'match number of distinct values.')
            x_metadata['category_names'] = {column_to_index[k]: v for k, v in category_names.items()}

    @abstractmethod
    def _load_dataset(self, filename):
        """
        Loads a dataset and returns x, x_metadata, y, y_metadata, index_to_actual
        """
        pass
