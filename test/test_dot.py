import unittest

from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy

class TestDot(unittest.TestCase):
    def test_dot(self):
        try:
            ds = MultiOutputDataset('golf_multi.csv')
            ds.load_if_necessary()
        except FileNotFoundError:
            ds = MultiOutputDataset('test/golf_multi.csv')
            ds.load_if_necessary()

        dt = DecisionTree([CategoricalMultiSplittingStrategy(), AxisAlignedSplittingStrategy()],
                          Entropy(), 'categorical')
        dt.fit(ds)

        try:
            with open('golf_multi.dot') as infile:
                expected = infile.read()
        except FileNotFoundError:
            with open('test/golf_multi.dot') as infile:
                expected = infile.read()
        self.assertEqual(expected, dt.print_dot(ds.x_metadata, ds.y_metadata))
