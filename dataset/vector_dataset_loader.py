from benchmark_suite.dataset.dataset_loader import DatasetLoader
import numpy as np
import pandas as pd
from os.path import splitext

# This class enables us to load the datasets we have already converted to the XY (vector) format
class VectorDatasetLoader(DatasetLoader):
    def _load_dataset(self, filename):
        path, _ = splitext(filename)
        X_train = pd.read_pickle(f'{path}_X.pickle')
        Y_train = np.load(f'{path}_Y.npy')
        return X_train, Y_train