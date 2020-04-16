import os
import unittest
from unittest import SkipTest

from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.multi_label_entropy import MultiLabelEntropy
from dtcontrol.decision_tree.pre_processing.norm_pre_processor import NormPreProcessor
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy

class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.suite = BenchmarkSuite(timeout=60 * 60 * 2,
                                    save_folder='test_saved_classifiers',
                                    benchmark_file='benchmark_test',
                                    rerun=True)
        self.expected_results = {
            'cartpole': {
                'CART': 127,
                'logreg': 100,  # this is different from the table but apparently correct
                'OC1': 92,
                'maxfreq': 6,
                'maxfreq-logreg': 7,
                'minnorm': 56,
                'minnorm-logreg': 16,
                'multilabel': 4
            },
            'cruise-latest': {
                'CART': 494,
                'logreg': 392,
                'OC1': 290,
                'maxfreq': 2,
                'maxfreq-logreg': 2,
                'minnorm': 282,
                'minnorm-logreg': 197,
                'multilabel': 2
            },
            'dcdc': {
                'CART': 136,
                'logreg': 70,  # again different
                'maxfreq': 5,
                'maxfreq-logreg': 5,
                'minnorm': 11,
                'minnorm-logreg': 125,
                'multilabel': 3
            },
            '10rooms': {
                'CART': 8649,
                'logreg': 74,
                'OC1': 903,
                'maxfreq': 4,
                'maxfreq-logreg': 10,
                'minnorm': 2704,
                'minnorm-logreg': 28,
                'multilabel': 4
            },
            'vehicle': {
                'CART': 6619,
                'logreg': 5195,  # again different from table
                'OC1': 4639
            },
            'firewire_abst': {
                'CategoricalCART': 13,
                'AVG': 6
            },
            'wlan0': {
                'CategoricalCART': 135,
                'AVG': 106
            }
        }
        self.init_classifiers()
        if os.path.exists('benchmark_test.json'):
            os.remove('benchmark_test.json')

    def init_classifiers(self):
        self.cart = DecisionTree([AxisAlignedSplittingStrategy()], Entropy(), 'CART')
        self.maxfreq = DecisionTree([AxisAlignedSplittingStrategy()], Entropy(MaxFreqDeterminizer()), 'maxfreq',
                                    early_stopping=True, early_stopping_optimized=True)
        self.minnorm = DecisionTree([AxisAlignedSplittingStrategy()], Entropy(), 'minnorm',
                                    label_pre_processor=NormPreProcessor(min))
        logreg_strategy = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
        self.logreg = DecisionTree([AxisAlignedSplittingStrategy(), logreg_strategy], Entropy(), 'logreg')
        self.maxfreq_logreg = DecisionTree([AxisAlignedSplittingStrategy(), logreg_strategy],
                                           Entropy(MaxFreqDeterminizer()),
                                           'maxfreq-logreg', early_stopping=True, early_stopping_optimized=True)
        self.minnorm_logreg = DecisionTree([AxisAlignedSplittingStrategy(), logreg_strategy], Entropy(), 'minnorm-logreg',
                                           label_pre_processor=NormPreProcessor(min))
        self.multilabel = DecisionTree([AxisAlignedSplittingStrategy()], MultiLabelEntropy(), 'multilabel',
                                       early_stopping=True, early_stopping_optimized=True)
        self.categorical_cart = DecisionTree([AxisAlignedSplittingStrategy(), CategoricalMultiSplittingStrategy()],
                                             Entropy(), 'CategoricalCART')
        self.avg = DecisionTree([AxisAlignedSplittingStrategy(), CategoricalMultiSplittingStrategy(value_grouping=True)],
                                Entropy(), 'AVG')

    def test_fast(self):  # takes about 30s on my laptop
        datasets = ['cartpole', '10rooms', 'vehicle']
        classifiers = [self.cart, self.maxfreq, self.minnorm, self.multilabel]
        self.run_test(datasets, classifiers)

    def test_categorical(self):
        datasets = ['firewire_abst', 'wlan0']
        classifiers = [self.categorical_cart, self.avg]
        self.run_test(datasets, classifiers)

    @SkipTest
    def test_medium(self):  # takes about 4 min on my laptop
        datasets = ['cartpole', '10rooms', 'vehicle']
        classifiers = [self.cart, self.logreg, self.maxfreq, self.maxfreq_logreg, self.minnorm, self.multilabel]
        self.run_test(datasets, classifiers)

    @SkipTest
    def test_slow(self):  # takes about 6h on my laptop
        datasets = [
            'cartpole',
            'cruise-latest',
            'dcdc',
            '10rooms',
            'vehicle'
        ]
        classifiers = [self.cart, self.logreg, self.maxfreq, self.maxfreq_logreg, self.minnorm,
                       self.minnorm_logreg, self.multilabel]
        self.run_test(datasets, classifiers)

    def run_test(self, datasets, classifiers):
        # docker and local folders
        self.suite.add_datasets(['../examples', '../examples/prism', '/examples', '/examples/prism'], include=datasets)
        self.suite.benchmark(classifiers)
        self.assert_results_almost_equal(self.expected_results, self.suite.results)

    def assert_results_almost_equal(self, expected, actual, tol_percent=5):
        for ds in actual:
            for classifier in actual[ds]['classifiers']:
                if classifier not in expected[ds] or 'stats' not in actual[ds]['classifiers'][classifier]:
                    continue
                expected_paths = expected[ds][classifier]
                stats = actual[ds]['classifiers'][classifier]['stats']
                self.assertFalse('accuracy' in stats, 'Accuracy not 1.0')
                actual_paths = stats['paths']
                tol = (tol_percent / 100) * expected_paths
                tol = max(tol, 5)  # fix for small trees
                self.assertTrue(expected_paths - tol <= actual_paths <= expected_paths + tol,
                                f'Expected: [{expected_paths - tol}, {expected_paths + tol}], Actual: {actual_paths}'
                                f' with {classifier} on {ds}')

if __name__ == '__main__':
    unittest.main()
