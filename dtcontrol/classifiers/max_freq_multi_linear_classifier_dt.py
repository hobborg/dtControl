from dtcontrol.classifiers.linear_classifier_dt import LinearClassifierDT, LinearClassifierOrAxisAlignedNode
from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset

class MaxFreqMultiLinearClassifierDT(LinearClassifierDT):
    def __init__(self, classifier_class, **kwargs):
        super().__init__(classifier_class, **kwargs)
        self.name = 'MaxFreqMulti-LinearClassifierDT'

    def is_applicable(self, dataset):
        return isinstance(dataset, MultiOutputDataset) and not dataset.is_deterministic

    def fit(self, dataset):
        if dataset.tuple_to_tuple_id is None:
            dataset.get_tuple_ids()
        self.root = MaxFreqMultiLinearClassifierNode(dataset.tuple_to_tuple_id, self.classifier_class, **self.kwargs)
        self.root.fit(dataset.X_train, dataset.Y_train)
        self.set_labels(lambda leaf: dataset.map_tuple_id_back(leaf.trained_label), dataset.index_to_value)

class MaxFreqMultiLinearClassifierNode(LinearClassifierOrAxisAlignedNode):
    def __init__(self, tuple_to_tuple_id, classifier_class, depth=0, **kwargs):
        super().__init__(classifier_class, depth, **kwargs)
        self.tuple_to_tuple_id = tuple_to_tuple_id

    def create_child_node(self):
        return MaxFreqMultiLinearClassifierNode(self.tuple_to_tuple_id, self.classifier_class, self.depth + 1,
                                                **self.kwargs)

    def find_split(self, X, y):
        return super().find_split(X, MultiOutputDataset.determinize_max_over_all_inputs(y, self.tuple_to_tuple_id))

    def check_done(self, X, y):
        return super().check_done(X, MultiOutputDataset.determinize_max_over_all_inputs(y, self.tuple_to_tuple_id))
