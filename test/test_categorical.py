import unittest

from dtcontrol.dataset.single_output_dataset import SingleOutputDataset

class TestCategorical(unittest.TestCase):
    def test_categorical(self):
        ds = SingleOutputDataset('golf.csv')
        ds.load_if_necessary()
        self.assertEqual([0, 1, 2, 3], ds.x_metadata['categorical'])
        self.assertEqual(["Outlook", "Temperature", "Humidity", "Windy"], ds.x_metadata['variables'])
        self.assertEqual({
            0: ["Rainy", "Overcast", "Sunny"],
            1: ["Cool", "Mild", "Hot"],
            3: ["No", "Yes"]
        }, ds.x_metadata['category_names'])
        # self.assertEqual([0, 1, 2, 3], ds.get_categorical())

        # dt = DecisionTree(NonDeterminizer(), [CartSplittingStrategy()], Entropy(), 'cart')
        # dt.fit(ds)
        pass
