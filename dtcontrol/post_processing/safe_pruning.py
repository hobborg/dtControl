import sys

from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.post_processing.post_processing_method import PostProcessingMethod
from dtcontrol.util import make_set

class SafePruning(PostProcessingMethod):
    def __init__(self, classifier, rounds=None):
        if not isinstance(classifier, DecisionTree):  # in theory we also allow other classifiers
            raise ValueError('Safe pruning works only on decision trees.')
        self.name = classifier.get_name()
        super().__init__(classifier, self.name)
        self.rounds = rounds

    def run(self):
        self.prune(self.classifier.root, self.rounds)

    def prune(self, node, rounds):
        if node.is_leaf():
            return None if rounds is None else rounds
        remaining_rounds = None if rounds is None else sys.maxsize
        for child in node.children:
            r = self.prune(child, rounds)
            if rounds is not None and r < remaining_rounds:
                remaining_rounds = r
        if rounds is not None:
            assert remaining_rounds >= 0
        node.num_nodes = 1 + sum([c.num_nodes for c in node.children])
        node.num_inner_nodes = 1 + sum([c.num_inner_nodes for c in node.children])
        if remaining_rounds == 0 or any(not c.is_leaf() for c in node.children):
            return 0

        intersection = set.intersection(*[make_set(c.index_label) for c in node.children])
        if len(intersection) == 0:
            return None if rounds is None else remaining_rounds - 1
        node.index_label = list(intersection) if len(intersection) > 1 else list(intersection)[0]
        intersection = set.intersection(*[make_set(c.actual_label) for c in node.children])
        node.actual_label = list(intersection) if len(intersection) > 1 else list(intersection)[0]
        node.children = []
        node.num_nodes = 1
        node.num_inner_nodes = 0
        return None if rounds is None else remaining_rounds - 1
