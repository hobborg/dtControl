import numpy as np

from dataset.dataset import Dataset

class MultiOutputDataset(Dataset):
    def __init__(self, filename):
        super().__init__(filename)
        self.tuple_labels = None

    def compute_accuracy(self, Y_pred):  # TODO: double-check that this works
        self.check_loaded()
        if len(Y_pred[Y_pred == None]) != 0:
            return None
        tuple_labels = self.get_tuple_labels()
        num_correct = 0
        for i in range(len(Y_pred)):
            pred = Y_pred[i]
            if set.issubset(set(pred), set(tuple_labels[i])):
                num_correct += 1
        return num_correct / len(Y_pred)

    def get_tuple_labels(self):
        if self.tuple_labels is None:
            self.tuple_labels = np.dstack(*self.Y_train)
        return self.tuple_labels

    def get_unique_labels(self):
        # TODO
        pass

    def map_unique_label_back(self, label):
        # TODO
        pass
