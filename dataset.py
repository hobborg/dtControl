import pandas as pd
import numpy as np
import os

class Dataset:
    def __init__(self, X_file, Y_file):
        self.name = Dataset.get_dataset_name(X_file)
        self.X_train = np.array(pd.read_pickle(X_file))
        self.Y_train = np.load(Y_file)

    @staticmethod
    def get_dataset_name(file):
        return os.path.basename(file).replace('_X.pickle', '')

    def get_labels_as_unique(self):
        l = []
        next_unused_int = 0
        label_to_int = {}
        for i in range(len(self.Y_train)):
            label = ','.join([str(i) for i in self.Y_train[i]])
            if label not in label_to_int:
                next_unused_int += 1
                label_to_int[label] = next_unused_int
            l.append(label_to_int[label])
        return np.array(l)
