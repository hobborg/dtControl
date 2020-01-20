import unittest

from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy

class TestCategorical(unittest.TestCase):
    def test_categorical(self):
        try:
            ds = SingleOutputDataset('golf.csv')
        except FileNotFoundError:
            ds = SingleOutputDataset('test/golf.csv')
        ds.load_if_necessary()
        self.assertEqual([0, 1, 2, 3], ds.x_metadata['categorical'])
        self.assertEqual(["Outlook", "Temperature", "Humidity", "Windy"], ds.x_metadata['variables'])
        self.assertEqual({
            0: ["Rainy", "Overcast", "Sunny"],
            1: ["Cool", "Mild", "Hot"],
            3: ["No", "Yes"]
        }, ds.x_metadata['category_names'])

        dt = DecisionTree(NonDeterminizer(), [CategoricalMultiSplittingStrategy(), AxisAlignedSplittingStrategy()],
                          Entropy(), 'categorical')
        dt.fit(ds)
        root = dt.root
        self.assertEqual(0, root.split.feature)
        self.assertEqual(3, len(root.children))
        l = root.children[0]
        self.assertEqual(2, l.split.feature)
        self.assertEqual(2, len(l.children))
        ll = l.children[0]
        lr = l.children[1]
        self.assertTrue(ll.is_leaf())
        self.assertEqual([1], ll.actual_label)
        self.assertTrue(lr.is_leaf())
        self.assertEqual([0], lr.actual_label)
        m = root.children[1]
        self.assertTrue(m.is_leaf())
        self.assertEqual([1], m.actual_label)
        r = root.children[2]
        self.assertEqual(3, r.split.feature)
        self.assertEqual(2, len(r.children))
        rl = r.children[0]
        rr = r.children[1]
        self.assertTrue(rl.is_leaf())
        self.assertEqual([1], rl.actual_label)
        self.assertTrue(rr.is_leaf())
        self.assertEqual([0], rr.actual_label)
