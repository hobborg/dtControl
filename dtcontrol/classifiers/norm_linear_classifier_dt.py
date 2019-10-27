import numpy as np

from dtcontrol.classifiers.linear_classifier_dt import LinearClassifierDT, LinearClassifierOrAxisAlignedNode
from dtcontrol.dataset.single_output_dataset import SingleOutputDataset

class NormLinearClassifierDT(LinearClassifierDT):
    """
    :param comp: The comparison function to be used (either max or min)
    """

    def __init__(self, comp, classifier_class, **kwargs):
        super().__init__(classifier_class, **kwargs)
        self.name = f'{"Max" if comp == max else "Min"}Norm-LinearClassifierDT'
        self.comp = comp

    def is_applicable(self, dataset):
        return not dataset.is_deterministic

    def fit(self, dataset):
        self.root = LinearClassifierOrAxisAlignedNode(self.classifier_class, **self.kwargs)
        if isinstance(dataset, SingleOutputDataset):
            self.root.fit(dataset.X_train, self.determinize_single_output(dataset))
            self.set_labels(lambda leaf: leaf.trained_label, dataset.index_to_value)
        else:
            self.root.fit(dataset.X_train, self.determinize_multi_output(dataset))
            self.set_labels(lambda leaf: dataset.map_tuple_id_back(leaf.trained_label), dataset.index_to_value)

    def determinize_single_output(self, dataset):
        return np.apply_along_axis(lambda x: self.comp(x[x != -1], key=lambda i: dataset.index_to_value[i] ** 2),
                                   axis=1,
                                   arr=dataset.Y_train)

    def determinize_multi_output(self, dataset):
        zipped = np.stack(dataset.Y_train, axis=2)
        result = []
        i = 0
        for arr in zipped:
            result.append(self.comp([t for t in arr if t[0] != -1],
                                    key=lambda t: sum(dataset.index_to_value[i] ** 2 for i in t)))
            i += 1
        if dataset.tuple_to_tuple_id is None:  # TODO: refactor stuff like this with something like dataset.get_tuple_to_tuple_ids()
            dataset.get_unique_labels()
        return np.array([dataset.tuple_to_tuple_id[tuple(t)] for t in result])
