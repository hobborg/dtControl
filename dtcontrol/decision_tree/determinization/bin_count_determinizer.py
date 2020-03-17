import numpy as np

from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.decision_tree.determinization.determinizer import Determinizer

class BinCountDeterminizer(Determinizer):
    """
    This determinizer uses the bincount determinization approach.
    """

    def determinize(self, dataset):
        if isinstance(dataset, SingleOutputDataset):
            return self.get_bin_count_labels(dataset.y)
        else:
            return self.get_bin_count_labels(dataset.get_tuple_ids())

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
    def get_bin_count_labels(labels):
        return labels
