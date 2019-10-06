from dataset.dataset_loader import DatasetLoader
import numpy as np
import pandas as pd
from os.path import splitext

# This class enables us to load the datasets we have already converted to the XY (vector) format
class VectorDatasetLoader(DatasetLoader):
    def _load_dataset(self, filename):
        path, _ = splitext(filename)
        X_train = pd.read_pickle(f'{path}_X.pickle')
        Y_train = np.load(f'{path}_Y.npy')
        Y_train = self.convert_vector_labels_to_new_format(Y_train)
        return np.array(X_train), list(X_train.columns), Y_train, {x:x for x in Y_train.flatten()}

    @staticmethod
    def convert_vector_labels_to_new_format(labels):
        m = np.max(np.nonzero(labels)[1]) + 1
        l = []
        for row in labels:
            values = list(np.nonzero(row)[0] + 1)
            filler = [0] * (m - len(values))
            l.append(values + filler)
        return np.array(l)
