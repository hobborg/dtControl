import numpy as np

from classifiers.cart_custom_decision_tree import CartCustomDecisionTree, CartCustomNode
from dataset.single_output_dataset import SingleOutputDataset

class NormSingleOutputDecisionTree(CartCustomDecisionTree):
    """
    :param comp: The comparison function to be used (either max or min)
    """

    def __init__(self, comp):
        super().__init__()
        self.name = f'NormSingleOutputDT({"Max" if comp == max else "Min"})'
        self.comp = comp

    def is_applicable(self, dataset):
        return isinstance(dataset, SingleOutputDataset) and not dataset.is_deterministic

    def fit(self, dataset):
        self.root = NormSingleOutputNode(dataset.index_to_value, self.comp)
        self.root.fit(dataset.X_train, dataset.Y_train)
        self.set_labels(lambda leaf: leaf.trained_label, dataset.index_to_value)

    def __str__(self):
        return 'NormSingleOutputDT'

class NormSingleOutputNode(CartCustomNode):
    def __init__(self, index_to_value, comp, depth=0):
        super().__init__(depth)
        self.index_to_value = index_to_value
        self.comp = comp

    def create_child_node(self):
        return NormSingleOutputNode(self.index_to_value, self.comp, self.depth + 1)

    def find_split(self, X, y):
        return super().find_split(X, self.determinize(y))

    def check_done(self, X, y):
        return super().check_done(X, self.determinize(y))

    def determinize(self, y):
        return np.apply_along_axis(lambda x: self.comp(x[x != -1], key=lambda i: float(self.index_to_value[i]) ** 2),
                                   axis=1,
                                   arr=y)
