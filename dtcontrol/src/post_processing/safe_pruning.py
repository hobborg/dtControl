from src.decision_tree.decision_tree import DecisionTree
from src.post_processing.post_processing_method import PostProcessingMethod
from src.util import make_set

class SafePruning(PostProcessingMethod):
    def __init__(self, classifier, name=None):
        if not isinstance(classifier, DecisionTree):  # in theory we also allow other classifiers
            raise ValueError('Safe pruning works only on decision trees.')
        if not name:
            name = f'SafePruning-{classifier.get_name()}'
        super().__init__(classifier, name)
        self.name = name

    def run(self):
        self.prune(self.classifier.root)

    def prune(self, node):
        if node.is_leaf():
            return
        self.prune(node.left)
        self.prune(node.right)
        node.num_nodes = 1 + node.left.num_nodes + node.right.num_nodes
        intersection = make_set(node.left.index_label) & make_set(node.right.index_label)
        if len(intersection) == 0:
            return
        node.index_label = list(intersection) if len(intersection) > 1 else list(intersection)[0]
        node.actual_label = node.determinizer.index_label_to_actual(node.index_label)
        node.left = None
        node.right = None
        node.num_nodes = 1
