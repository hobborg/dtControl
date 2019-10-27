import re
import logging

import numpy as np
import pandas as pd

from dtcontrol.dataset.dataset_loader import DatasetLoader
from tqdm import tqdm


class CSVDatasetLoader(DatasetLoader):
    def _load_dataset(self, filename):
        f = open(filename, 'r')
        print(f"Reading from {filename}")
        f.readline()  # whether permissive
        state_dim, input_dim = map(int, f.readline().split("BEGIN")[1].split())

        ds = pd.read_csv(f, header=None)

        unique_list = []
        for i in range(state_dim, state_dim+input_dim):
            unique_list += ds[i].unique().tolist()
        index_to_value = {x: y for x, y in enumerate(set(unique_list))}
        value_to_index = {y: x for x, y in index_to_value.items()}

        ds[[i for i in range(state_dim, state_dim+input_dim)]] = ds[[i for i in range(state_dim, state_dim+input_dim)]].applymap(lambda x: value_to_index[x])

        grouped = ds.groupby([i for i in range(state_dim)], sort=False)
        aggregate = grouped[state_dim].apply(list).reset_index(name=state_dim)
        for i in range(1, input_dim):
            aggregate[state_dim+i] = grouped[state_dim+i].apply(list).reset_index(name=state_dim+i)[state_dim+i]

        max_non_det = aggregate[state_dim].agg(len).max()

        for i in range(0, input_dim):
            aggregate[state_dim+i] = aggregate[state_dim+i].apply(lambda ls: ls + [-1 for i in range(max_non_det - len(ls))])

        X_train = np.array(aggregate[[i for i in range(state_dim)]])

        if input_dim > 1:
            Y_train = np.ndarray((input_dim, X_train.shape[0], max_non_det), dtype=np.int16)
            for i in range(input_dim):
                Y_train[i] = np.array(aggregate[state_dim+i].tolist())
        else:  # input_dim = 1
            Y_train = np.array(aggregate[state_dim].tolist())

        # construct metadata
        # assumption is that UPPAAL only works with integers
        X_metadata = dict()
        X_metadata["variables"] = [f"x_{i}" for i in range(state_dim)]
        X_metadata["min"] = [int(i) for i in np.amin(X_train, axis=0)]
        X_metadata["max"] = [int(i) for i in np.amax(X_train, axis=0)]
        X_metadata["step_size"] = None  # todo

        Y_metadata = dict()
        Y_metadata["variables"] = [f"u_{i}" for i in range(input_dim)]
        Y_metadata["min"] = [min(index_to_value.values())]
        Y_metadata["max"] = [max(index_to_value.values())]
        Y_metadata["step_size"] = None  # todo

        logging.debug(X_metadata)
        logging.debug(Y_metadata)

        return (X_train, X_metadata, Y_train, Y_metadata, index_to_value)