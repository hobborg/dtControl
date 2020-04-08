import unittest

from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy

class TestCategorical(unittest.TestCase):
    def test_categorical(self):
        try:
            ds = SingleOutputDataset('golf.csv')
            ds.load_if_necessary()
        except FileNotFoundError:
            ds = SingleOutputDataset('test/golf.csv')
            ds.load_if_necessary()
        self.assertEqual([0, 1, 2, 3], ds.x_metadata['categorical'])
        self.assertEqual(["Weather", "Temperature", "Humidity", "Wind"], ds.x_metadata['variables'])
        self.assertEqual({
            0: ["Rain", "Overcast", "Sunny"],
            1: ["Cool", "Mild", "Hot"],
            3: ["Weak", "Strong"]
        }, ds.x_metadata['category_names'])

        dt = DecisionTree([CategoricalMultiSplittingStrategy(), AxisAlignedSplittingStrategy()],
                          Entropy(), 'categorical')
        dt.fit(ds)
        root = dt.root
        self.assertEqual(0, root.split.feature)
        self.assertEqual(3, len(root.children))
        l = root.children[0]
        self.assertTrue(l.is_leaf())
        self.assertEqual(0, l.actual_label)
        m = root.children[1]
        self.assertEqual(1, m.split.feature)
        self.assertEqual(3, len(m.children))
        ml = m.children[0]
        self.assertTrue(ml.is_leaf())
        self.assertEqual(1, ml.actual_label)
        mm = m.children[0]
        self.assertTrue(mm.is_leaf())
        self.assertEqual(1, mm.actual_label)
        mr = m.children[2]
        self.assertTrue(mr.is_leaf())
        self.assertEqual(0, mr.actual_label)
        r = root.children[2]
        self.assertEqual(3, r.split.feature)
        self.assertEqual(2, len(r.children))
        rl = r.children[0]
        rr = r.children[1]
        self.assertTrue(rl.is_leaf())
        self.assertEqual(1, rl.actual_label)
        self.assertTrue(rr.is_leaf())
        self.assertEqual(0, rr.actual_label)
