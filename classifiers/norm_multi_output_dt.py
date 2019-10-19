import numpy as np

from classifiers.cart_custom_dt import CartDT, CartNode
from dataset.multi_output_dataset import MultiOutputDataset

class NormMultiOutputDT(CartDT):
    """
    :param comp: The comparison function to be used (either max or min)
    """

    def __init__(self, comp):
        super().__init__()
        self.name = f'{"Max" if comp == max else "Min"}Norm-MultiOutputDT'
        self.comp = comp

    def is_applicable(self, dataset):
        return isinstance(dataset, MultiOutputDataset) and not dataset.is_deterministic

    def fit(self, dataset):
        if dataset.tuple_to_tuple_id is None:  # TODO: refactor stuff like this with something like dataset.get_tuple_to_tuple_ids()
            dataset.get_unique_labels()
        self.root = CartNode()
        self.root.fit(dataset.X_train, self.determinize(dataset))
        self.set_labels(lambda leaf: dataset.map_tuple_id_back(leaf.trained_label), dataset.index_to_value)

    def determinize(self, dataset):
        zipped = np.stack(dataset.Y_train, axis=2)
        result = []
        i = 0
        for arr in zipped:
            result.append(self.comp([t for t in arr if t[0] != -1],
                                    key=lambda t: sum(dataset.index_to_value[i] ** 2 for i in t)))
            i += 1
        return np.array([dataset.tuple_to_tuple_id[tuple(t)] for t in result])
