import unittest

from dtcontrol.dataset.single_output_dataset import SingleOutputDataset

class TestCategorical(unittest.TestCase):
    def test_categorical(self):
        ds = SingleOutputDataset('golf.csv')
        ds.load_if_necessary()
        self.assertEqual([0, 1, 2, 3], ds.get_categorical())
