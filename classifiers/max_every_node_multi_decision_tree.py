from dataset import AnyLabelDataset
from label_format import LabelFormat
from custom_decision_tree import CustomDecisionTree, Node
from standard_custom_decision_tree import StandardCustomDecisionTree, StandardCustomNode

class MaxEveryNodeMultiDecisionTree(StandardCustomDecisionTree):
    def __init__(self,):
        super().__init__()
        self.name = 'MaxEveryNodeMultiDT'
        self.label_format = LabelFormat.MAX_EVERY_NODE

    def create_root_node(self):
        return MaxStandardNode()

    def __str__(self):
        return 'MaxEveryNodeMultiDecisionTree'

class MaxMultiNode(StandardCustomNode):
    def __init__(self, depth=0):
        super().__init__(depth)

    def create_child_node(self):
        return MaxStandardNode(self.depth + 1)

    def find_split(self, X, y):
        return super().find_split(X, AnyLabelDataset.get_max_labels(y))

    def check_done(self, y):
        return super().check_done(AnyLabelDataset.get_max_labels(y))