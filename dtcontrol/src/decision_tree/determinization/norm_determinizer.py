import numpy as np

from src.dataset.single_output_dataset import SingleOutputDataset
from src.decision_tree.determinization.determinizer import Determinizer

class NormDeterminizer(Determinizer):
    """
    This determinizer uses the (min/max)norm determinization approach.
    """

    def __init__(self, comp):
        """
        :param comp: the comparison function to be used, either min or max
        """
        super().__init__()
        self.comp = comp

    def determinize(self, dataset):
        if isinstance(dataset, SingleOutputDataset):
            return self.determinize_single_output(dataset)
        else:
            return self.determinize_multi_output(dataset)

    def get_index_label(self, label):
        if isinstance(self.dataset, SingleOutputDataset):
            return label
        else:
            return self.dataset.map_tuple_id_back(label)

    def determinize_once_before_construction(self):
        return True

    def is_only_multioutput(self):
        return False

    def determinize_single_output(self, dataset):
        return np.apply_along_axis(lambda x: self.comp(x[x != -1], key=lambda i: dataset.index_to_actual[i] ** 2),
                                   axis=1,
                                   arr=dataset.y)

    def determinize_multi_output(self, dataset):
        zipped = np.stack(dataset.y, axis=2)
        result = []
        i = 0
        for arr in zipped:
            result.append(self.comp([t for t in arr if t[0] != -1],
                                    key=lambda t: sum(dataset.index_to_actual[i] ** 2 for i in t)))
            i += 1
        return np.array([dataset.get_tuple_to_tuple_id()[tuple(t)] for t in result])
