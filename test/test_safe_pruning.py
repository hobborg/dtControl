from unittest import TestCase

from dtcontrol.decision_tree.decision_tree import Node, DecisionTree
from dtcontrol.decision_tree.impurity.entropy import Entropy
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

        sp = SafePruning(DecisionTree([], Entropy(), 'name'))
        sp.classifier.root = root
        sp.run()

        self.assertEqual(5, root.num_nodes)
        self.assertTrue(root.children[0].is_leaf())
        self.assertEqual(2, root.children[0].index_label)
        self.assertTrue(root.children[1].children[0].is_leaf())
        self.assertEqual([1, 2, 3], root.children[1].children[0].index_label)
        self.assertTrue(root.children[1].children[1].is_leaf())
        self.assertEqual([4, 5], root.children[1].children[1].index_label)

    def test_rounds(self):
        ll = self.create_leaf([1,2])
        lr = self.create_leaf([3,4])
        l = self.create_parent(ll, lr)
        rll = self.create_leaf([1,2,3])
        rlr = self.create_leaf([2,3,4])
        rl = self.create_parent(rll, rlr)
        rrl = self.create_leaf([2,5])
        rrr = self.create_leaf([8, 2])
        rr = self.create_parent(rrl, rrr)
        r = self.create_parent(rl, rr)
        root = self.create_parent(l, r)

        sp = SafePruning(DecisionTree([], Entropy(), 'name'), rounds=1)
        sp.classifier.root = root
        sp.run()

        self.assertEqual(7, root.num_nodes)
        self.assertTrue(root.children[0].children[0].is_leaf())
        self.assertEqual([1,2], root.children[0].children[0].index_label)
        self.assertTrue(root.children[0].children[1].is_leaf())
        self.assertEqual([3, 4], root.children[0].children[1].index_label)
        self.assertTrue(root.children[1].children[0].is_leaf())
        self.assertEqual([2,3], root.children[1].children[0].index_label)
        self.assertTrue(root.children[1].children[1].is_leaf())
        self.assertEqual(2, root.children[1].children[1].index_label)

    @staticmethod
    def create_leaf(label):
        node = Node(None, None)
        node.num_nodes = 1
        node.index_label = label
        node.actual_label = label
        return node

    @staticmethod
    def create_parent(left, right):
        node = Node(None, None)
        node.children = [left, right]
        node.num_nodes = 1 + left.num_nodes + right.num_nodes
        return node
