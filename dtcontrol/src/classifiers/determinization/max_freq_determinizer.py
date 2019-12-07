import numpy as np

from src.classifiers.determinization.determinizer import Determinizer
from src.dataset.single_output_dataset import SingleOutputDataset

class MaxFreqDeterminizer(Determinizer):
    """
    This determinizer uses the maximum frequency determinization approach.
    """

    def determinize(self, dataset):
        if isinstance(dataset, SingleOutputDataset):
            return self.get_max_freq_labels(dataset.Y_train)
        else:
            return self.get_max_freq_labels(dataset.get_tuple_ids())

    def get_index_label(self, label):
        if isinstance(self.dataset, SingleOutputDataset):
            return label
        else:
            return self.dataset.map_tuple_id_back(label)

    def determinize_once_before_construction(self):
        return False

    def is_only_multioutput(self):
        return False

    @staticmethod
    def get_max_freq_labels(labels):
        flattened_labels = labels.flatten()
        # remove -1 as we use it only as a filler
        flattened_labels = flattened_labels[flattened_labels != -1]
        label_counts = np.bincount(flattened_labels)
        new_labels = []
        for i in range(len(labels)):
            current = labels[i]
            current = current[current != -1]
            max_label = max(list(current), key=lambda l: label_counts[l])
            assert max_label != -1
            new_labels.append(max_label)
        return np.array(new_labels)
