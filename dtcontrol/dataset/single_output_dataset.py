from dtcontrol.dataset.dataset import Dataset
from dtcontrol.util import make_set

class SingleOutputDataset(Dataset):
    def __init__(self, filename):
        super().__init__(filename)
        self.unique_labels = None  # a unique int for every combination of possible outputs
        self.unique_mapping = None

    def compute_accuracy(self, y_pred):
        self.check_loaded()
        num_correct = 0
        for i in range(len(y_pred)):
            pred = y_pred[i]
            if pred is None:
                return None
            if set.issubset(make_set(pred), set(self.y[i])):
                num_correct += 1
        return num_correct / len(y_pred)

    def get_single_labels(self):
        return self.y

    def map_single_label_back(self, single_label):
        return single_label

    def get_unique_labels(self):
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
        if self.unique_labels is None:
            self.unique_labels, self.unique_mapping = self.get_unique_labels_from_2d(self.y)
        return self.unique_labels

    def map_unique_label_back(self, label):
        return [i for i in self.unique_mapping[label] if i != -1]

    def from_mask(self, mask):
        subset = SingleOutputDataset(self.filename)
        subset.copy_from_other_dataset(self)
        subset.parent_mask = mask
        subset.x = self.x[mask]
        subset.y = self.y[mask]
        if self.unique_labels is not None:
            subset.unique_labels = self.unique_labels[mask]
            subset.unique_mapping = self.unique_mapping
        return subset

    def from_mask_optimized(self, mask):
        empty_object = type('', (), {})()
        empty_object.parent_mask = mask
        empty_object.get_single_labels = lambda: self.y[mask]
        return empty_object

    def calc_single_feature_importance(self, featureInd, ignoredFeatures):
        return self.calc_feature_importance_for_y(featureInd, self.y, ignoredFeatures)