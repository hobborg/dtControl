from dataset.dataset import Dataset
from dataset.single_output_dataset import SingleOutputDataset
from classifiers.linear_classifier_dt import LinearClassifierDT, LinearClassifierOrAxisAlignedNode

class MaxFreqLinearClassifierDT(LinearClassifierDT):
    def __init__(self, classifier_class, **kwargs):
        super().__init__(classifier_class, **kwargs)
        self.name = 'MaxFreqLinearClassifierDT({})'.format(classifier_class.__name__)

    def is_applicable(self, dataset):
        return isinstance(dataset, SingleOutputDataset) and not dataset.is_deterministic

    def fit(self, dataset):
        self.root = MaxFreqLinearClassifierNode(self.classifier_class, **self.kwargs)
        self.root.fit(dataset.X_train, dataset.Y_train)
        self.set_labels(lambda leaf: leaf.trained_label, dataset.index_to_value)

class MaxFreqLinearClassifierNode(LinearClassifierOrAxisAlignedNode):
    def __init__(self, classifier_class, depth=0, **kwargs):
        super().__init__(classifier_class, depth, **kwargs)

    def create_child_node(self):
        return MaxFreqLinearClassifierNode(self.classifier_class, self.depth + 1, **self.kwargs)

    def find_split(self, X, y):
        return super().find_split(X, Dataset._get_max_labels(y))

    def check_done(self, X, y):
        return super().check_done(X, Dataset._get_max_labels(y))