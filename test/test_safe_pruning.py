from unittest import TestCase

from dtcontrol.decision_tree.decision_tree import Node, DecisionTree
from dtcontrol.decision_tree.determinization.determinizer import Determinizer
from dtcontrol.post_processing.safe_pruning import SafePruning

class TestSafePruning(TestCase):
    def test_run(self):
        lll = self.create_leaf([1, 2, 3])
        llr = self.create_leaf([2, 3])
        ll = self.create_parent(lll, llr)
        lr = self.create_leaf(2)
        l = self.create_parent(ll, lr)
        rl = self.create_leaf([1, 2, 3])
        rr = self.create_leaf([4, 5])
        r = self.create_parent(rl, rr)
        root = self.create_parent(l, r)

        sp = SafePruning(DecisionTree(None, None, None, 'name'))
        sp.classifier.root = root
        sp.run()

        self.assertEqual(5, root.num_nodes)
        self.assertTrue(root.left.is_leaf())
        self.assertEqual(2, root.left.index_label)
        self.assertTrue(root.right.left.is_leaf())
        self.assertEqual([1, 2, 3], root.right.left.index_label)
        self.assertTrue(root.right.right.is_leaf())
        self.assertEqual([4, 5], root.right.right.index_label)

    @staticmethod
    def create_leaf(label):
        node = Node(MockDeterminizer(), None, None)
        node.num_nodes = 1
        node.index_label = label
        return node

    @staticmethod
    def create_parent(left, right):
        node = Node(MockDeterminizer(), None, None)
        node.left = left
        node.right = right
        node.num_nodes = 1 + left.num_nodes + right.num_nodes
        return node

class MockDeterminizer(Determinizer):
    def determinize(self, dataset):
        pass

    def determinize_once_before_construction(self):
        pass

    def get_index_label(self, label):
        pass

    def is_only_multioutput(self):
        pass

    def index_label_to_actual(self, index_label):
        return None
