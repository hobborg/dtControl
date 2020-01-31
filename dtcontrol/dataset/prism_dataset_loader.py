import logging
from os.path import splitext, exists

import numpy as np

from dtcontrol.dataset.dataset_loader import DatasetLoader

class PrismDatasetLoader(DatasetLoader):
    def _load_dataset(self, filename):
        logging.info(f"Reading from {filename}")
        name, ext = splitext(filename)
        states_file = name + '_states.prism'
        if not exists(states_file):
            raise ValueError(f'Couldn\'t find states file for prism dataset {filename}.')

        state_mapping = {}
        with open(states_file, 'r') as f:
            x_variables = f.readline()
            x_variables = x_variables.replace('(', '').replace(')', '').split(',')
            last_state = -1
            for line in f:
                n, t = line.split(':')
                last_state += 1
                assert int(n) == last_state
                state_mapping[int(n)] = [int(i) for i in t.replace('(', '').replace(')', '').split(',')]

        x = []
        y = []
        y_variables = {}
        y_index = 0
        with open(filename, 'r') as f:
            for line in f:
                n, a = line.split(':')
                x.append(state_mapping[int(n)])
                if a not in y_variables:
                    y_variables[a] = y_index
                    y_index += 1
                y.append([y_variables[a]])

        x_metadata = dict()
        x_metadata["variables"] = x_variables
        x_metadata["categorical"] = []
        x_metadata["min"] = [int(i) for i in np.amin(x, axis=0)]
        x_metadata["max"] = [int(i) for i in np.amax(x, axis=0)]
        x_metadata["step_size"] = None  # todo

        index_to_actual = {i: i for i in y_variables.values()}

        y_metadata = dict()
        y_metadata["variables"] = sorted(y_variables.keys(), key=y_variables.get)
        y_metadata["min"] = [min(index_to_actual.values())]
        y_metadata["max"] = [max(index_to_actual.values())]
        y_metadata["step_size"] = None  # todo

        logging.debug(x_metadata)
        logging.debug(y_metadata)

        return (np.array(x), x_metadata, np.array(y), y_metadata, index_to_actual)