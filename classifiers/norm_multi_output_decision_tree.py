import numpy as np

from classifiers.cart_custom_decision_tree import CartCustomDecisionTree, CartCustomNode
from dataset.multi_output_dataset import MultiOutputDataset


class NormMultiOutputDecisionTree(CartCustomDecisionTree):
    """
    :param comp: The comparison function to be used (either max or min)
    """

    def __init__(self, comp):
        super().__init__()
        self.name = f'NormMultiOutputDT({"Max" if comp == max else "Min"})'
        self.comp = comp

    def is_applicable(self, dataset):
        return isinstance(dataset, MultiOutputDataset) and not dataset.is_deterministic

    def fit(self, dataset):
        if dataset.tuple_to_tuple_id is None:  # TODO: refactor stuff like this with something like dataset.get_tuple_to_tuple_ids()
            dataset.get_unique_labels()
        self.root = NormMultiOutputNode(dataset.index_to_value, dataset.tuple_to_tuple_id, self.comp)
        self.root.fit(dataset.X_train, dataset.Y_train)
        self.set_labels(lambda leaf: dataset.map_tuple_id_back(leaf.trained_label), dataset.index_to_value)

    def __str__(self):
        return 'NormMultiOutputDT'

class NormMultiOutputNode(CartCustomNode):
    def __init__(self, index_to_value, tuple_to_tuple_id, comp, depth=0):
        super().__init__(depth)
        self.index_to_value = index_to_value
        self.tuple_to_tuple_id = tuple_to_tuple_id
        self.comp = comp

    def create_child_node(self):
        return NormMultiOutputNode(self.index_to_value, self.tuple_to_tuple_id, self.comp, self.depth + 1)

    def find_split(self, X, y):
        return super().find_split(X, self.determinize(y))

    def check_done(self, X, y):
        return super().check_done(X, self.determinize(y))

    def determinize(self, y):
        zipped = np.stack(y, axis=2)
        result = []
        i = 0
        for arr in zipped:
            result.append(self.comp([t for t in arr if t[0] != -1],
                              key=lambda t: sum(float(self.index_to_value[i]) ** 2 for i in t)))
            i += 1
        return np.array([self.tuple_to_tuple_id[tuple(t)] for t in result])
