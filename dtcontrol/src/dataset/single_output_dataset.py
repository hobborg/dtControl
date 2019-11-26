from src.dataset.dataset import Dataset
from src.util import make_set

class SingleOutputDataset(Dataset):
    def __init__(self, filename):
        super().__init__(filename)
        self.unique_labels = None  # a unique int for every combination of possible outputs
        self.unique_mapping = None

    def compute_accuracy(self, Y_pred):
        self.check_loaded()
        num_correct = 0
        for i in range(len(Y_pred)):
            pred = Y_pred[i]
            if pred is None:
                return None
            if set.issubset(make_set(pred), set(self.Y_train[i])):
                num_correct += 1
        return num_correct / len(Y_pred)

    """
    e.g. 
    [[1  2  3 -1 -1],
     [1 -1 -1 -1 -1],
     [1  2 -1 -1 -1],
    ]
    
    gets mapped to
     
    unique_labels = [1, 2, 3]
    unique_mapping = {1: [1 2 3 -1 -1], 2: [1 -1 -1 -1 -1], 3: [1 2 -1 -1 -1]}
    """

    def get_unique_labels(self):
        if self.unique_labels is None:
            self.unique_labels, self.unique_mapping = self.get_unique_labels_from_2d(self.Y_train)
        return self.unique_labels

    def map_unique_label_back(self, label):
        return self.unique_mapping[label]
