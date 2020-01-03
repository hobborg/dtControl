import numpy as np
from dataset.multi_output_dataset import MultiOutputDataset
from src.decision_tree.cart_custom_dt import CartNode

class MaxCartForest():
    def __init__(self):
        self.trees = None
        self.name = 'MaxCARTForest'

    def is_applicable(self, dataset):
        return isinstance(dataset, MultiOutputDataset) and not dataset.is_deterministic

    def fit(self, dataset):  # TODO: extend to do max at every node (currently only at root node)
        if dataset.tuple_to_tuple_id is None:
            dataset.get_tuple_ids()
        Y_det = dataset.determinize_max_over_all_inputs(dataset.Y_train, dataset.tuple_to_tuple_id)
        Y_det = Y_det.reshape(-1, 1)
        Y_det_tuples = np.apply_along_axis(lambda x: dataset.map_tuple_id_back(x[0]), axis=1, arr=Y_det)
        self.trees = []
        num_outputs = len(dataset.Y_train)
        for i in range(num_outputs):
            tree = CartNode()
            tree.fit(dataset.X_train, Y_det_tuples[:, i])
            tree.set_labels(lambda leaf: leaf.trained_label, dataset.index_to_value)
            self.trees.append(tree)

    def predict(self, dataset):
        return list(zip(*[self.trees[i].predict(dataset.X_train) for i in range(len(self.trees))]))

    def get_stats(self) -> dict:
        stats = {}
        for i in range(len(self.trees)):
            stats[f'num_nodes_{i}'] = self.trees[i].num_nodes
        return stats

    def save(self, file):
        pass

    def export_dot(self, file):
        pass

    def export_c(self, file):
        pass

    def __str__(self):
        return 'MaxCARTForest'
