import numpy as np

from dtcontrol.decision_tree.determinization.determinizer import Determinizer

class MaxFreqDeterminizer(Determinizer):
    """
    This determinizer uses the maximum frequency determinization approach.
    """

    def determinize(self, dataset):
        if self.pre_determinized_labels is not None:
            return self.pre_determinized_labels
        return self.get_max_freq_labels(dataset.get_single_labels())

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
