import numpy as np

from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.decision_tree.determinization.determinizer import Determinizer

class RandomDeterminizer(Determinizer):
    """
    This determinizer determinizes randomly.
    """

    def determinize(self, dataset):
        if isinstance(dataset, SingleOutputDataset):
            return self.choose_random_labels(dataset.y)
        else:
            return self.choose_random_labels(dataset.get_tuple_ids())

    def get_index_label(self, label):
        if isinstance(self.dataset, SingleOutputDataset):
            return label
        else:
            return self.dataset.map_tuple_id_back(label)

    def determinize_once_before_construction(self):
        return True

    def is_only_multioutput(self):
        return False

    @staticmethod
    def choose_random_labels(y):
        return np.apply_along_axis(lambda x: np.random.choice(x[x != -1]), axis=1, arr=y)
