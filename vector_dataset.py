from benchmark_suite.dataset import Dataset
import os
import numpy as np
import pandas as pd

class VectorDataset(Dataset):
    def __init__(self, X_file, Y_file):
        super().__init__(self.get_dataset_name(X_file))
        self.X_file = X_file
        self.Y_file = Y_file

    @staticmethod
    def get_dataset_name(file):
        return os.path.basename(file).replace('_X.pickle', '')

    def load(self):
        self.X_train = pd.read_pickle(self.X_file)
        self.Y_train = np.load(self.Y_file)