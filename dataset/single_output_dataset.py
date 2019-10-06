from dataset.dataset import Dataset
from util import make_set

class SingleOutputDataset(Dataset):
    def __init__(self, filename):
        super().__init__(filename)
        self.unique_labels = None
        self.unique_mapping = None

    def compute_accuracy(self, Y_pred):
        self.check_loaded()
        if len(Y_pred[Y_pred == None]) != 0:
            return None
        num_correct = 0
        for i in range(len(Y_pred)):
            pred = Y_pred[i]
            if set.issubset(make_set(pred), set(self.Y_train[i])):
                num_correct += 1
        return num_correct / len(Y_pred)

    def get_unique_labels(self):
        if self.unique_labels is None:
            self.unique_labels, self.unique_mapping = self._get_unique_labels(self.Y_train)
        return self.unique_labels

    def map_unique_label_back(self, label):
        return self.unique_mapping[label]
