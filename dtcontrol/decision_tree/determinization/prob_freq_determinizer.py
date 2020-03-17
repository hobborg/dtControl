import numpy as np

from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.decision_tree.determinization.determinizer import Determinizer

class ProbFreqDeterminizer(Determinizer):
    """
    This determinizer uses the probabilistic frequency determinization approach.
    """

    def determinize(self, dataset):
        if isinstance(dataset, SingleOutputDataset):
            return self.get_prob_freq_labels(dataset.y)
        else:
            return self.get_prob_freq_labels(dataset.get_tuple_ids())

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
    def get_prob_freq_labels(labels):
        max_num_labels = np.max(labels)
        flattened_labels = labels.flatten()
        # remove -1 as we use it only as a filler
        flattened_labels = flattened_labels[flattened_labels != -1]
        label_counts = np.bincount(flattened_labels)
        new_labels = []
        for i in range(len(labels)):
            current = labels[i]
            hashed = set(current)
            if -1 in hashed:
                hashed.remove(-1)
            total = sum(label_counts[j] for j in hashed)
            prob_label = [label_counts[j] / total if j in hashed else 0 for j in range(1, max_num_labels + 1)]
            # prob_label = [1 / len(hashed) if j in hashed else 0 for j in range(1, max_num_labels + 1)]
            assert abs(sum(prob_label) - 1) < 1e-10 and len(prob_label) == max_num_labels
            new_labels.append(prob_label)
        return np.array(new_labels)
