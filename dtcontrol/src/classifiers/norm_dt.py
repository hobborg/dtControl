from src.classifiers.cart_custom_dt import CartDT, CartNode
from src.dataset.single_output_dataset import SingleOutputDataset

class NormDT(CartDT):
    """
    :param comp: The comparison function to be used (either max or min)
    """

    def __init__(self, comp):
        super().__init__()
        self.name = f'{"Max" if comp == max else "Min"}NormDT'
        self.comp = comp

    def is_applicable(self, dataset):
        return not dataset.is_deterministic

    def fit(self, dataset):
        self.root = CartNode()
        if isinstance(dataset, SingleOutputDataset):
            self.root.fit(dataset.X_train, self.determinize_single_output(dataset))
            self.set_labels(lambda leaf: leaf.trained_label, dataset.index_to_value)
        else:
            self.root.fit(dataset.X_train, self.determinize_multi_output(dataset))
            self.set_labels(lambda leaf: dataset.map_tuple_id_back(leaf.trained_label), dataset.index_to_value)

