from dataset import AnyLabelDataset
from label_format import LabelFormat
from custom_decision_tree import CustomDecisionTree, Node
from linear_classifier_decision_tree import LinearClassifierDecisionTree, LinearClassifierOrAxisAlignedNode

class MaxEveryNodeLCDecisionTree(LinearClassifierDecisionTree):
    def __init__(self, classifier_class, **kwargs):
        super().__init__(classifier_class, **kwargs)
        self.name = 'MaxEveryNodeLCDT({})'.format(classifier_class.__name__)
        self.label_format = LabelFormat.MAX_EVERY_NODE

    def create_root_node(self):
        return MaxLCNode(self.classifier_class, **self.kwargs)

    def __str__(self):
        return 'MaxEveryNodeLCDecisionTree'

class MaxLCNode(LinearClassifierOrAxisAlignedNode):
    def __init__(self, classifier_class, depth=0, **kwargs):
        super().__init__(classifier_class, depth, **kwargs)

    def create_child_node(self):
        return MaxLCNode(self.classifier_class, self.depth + 1, **self.kwargs)

    def find_split(self, X, y):
        return super().find_split(X, AnyLabelDataset.get_max_labels(y))

    def check_done(self, y):
        return super().check_done(AnyLabelDataset.get_max_labels(y))
