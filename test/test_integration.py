import os
import unittest
from unittest import SkipTest

from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.determinization.norm_determinizer import NormDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.cart import CartSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy

class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.suite = BenchmarkSuite(timeout=60 * 60 * 2,
                                    save_folder='test_saved_classifiers',
                                    benchmark_file='benchmark_test',
                                    rerun=False)
        self.expected_results = {
            'cartpole': {
                'CART': 127,
                'logreg': 100,  # this is different from the table but apparently correct
                'OC1': 92,
                'maxfreq': 6,
                'maxfreq-logreg': 7,
                'minnorm': 56,
                'minnorm-logreg': 16
            },
            'cruise-latest': {
                'CART': 494,
                'logreg': 392,
                'OC1': 290,
                'maxfreq': 2,
                'maxfreq-logreg': 2,
                'minnorm': 282,
                'minnorm-logreg': 197
            },
            'dcdc': {
                'CART': 136,
                'logreg': 70,  # again different
                'maxfreq': 5,
                'maxfreq-logreg': 5,
                'minnorm': 11,
                'minnorm-logreg': 125
            },
            '10rooms': {
                'CART': 8649,
                'logreg': 74,
                'OC1': 903,
                'maxfreq': 4,
                'maxfreq-logreg': 10,
                'minnorm': 2704,
                'minnorm-logreg': 28
            },
            'vehicle': {
                'CART': 6619,
                'logreg': 5195,  # again different from table
                'OC1': 4639
            }
        }
        self.init_classifiers()
        if os.path.exists('benchmark_test.json'):
            os.remove('benchmark_test.json')

    def init_classifiers(self):
        self.cart = DecisionTree(NonDeterminizer(), [CartSplittingStrategy()], Entropy(), 'CART')
        self.maxfreq = DecisionTree(MaxFreqDeterminizer(), [CartSplittingStrategy()], Entropy(), 'maxfreq')
        self.minnorm = DecisionTree(NormDeterminizer(min), [CartSplittingStrategy()], Entropy(), 'minnorm')
        logreg_strategy = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
        self.logreg = DecisionTree(NonDeterminizer(),
                                   [CartSplittingStrategy(), logreg_strategy], Entropy(), 'logreg')
        self.maxfreq_logreg = DecisionTree(MaxFreqDeterminizer(),
                                           [CartSplittingStrategy(), logreg_strategy], Entropy(), 'maxfreq-logreg')
        self.minnorm_logreg = DecisionTree(NormDeterminizer(min),
                                           [CartSplittingStrategy, logreg_strategy], Entropy(), 'minnorm-logreg')

    def test_fast(self):  # takes about 30s on my laptop
        datasets = ['cartpole', '10rooms', 'vehicle']
        classifiers = [self.cart, self.maxfreq, self.minnorm]
        self.run_test(datasets, classifiers)

    @SkipTest
    def test_medium(self):  # takes about 4 min on my laptop
        datasets = ['cartpole', '10rooms', 'vehicle']
        classifiers = [self.cart, self.logreg, self.maxfreq, self.maxfreq_logreg, self.minnorm]
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
                       self.minnorm_logreg]
        self.run_test(datasets, classifiers)

    def run_test(self, datasets, classifiers):
        # the unzipped_examples folder is used in docker
        self.suite.add_datasets(['../examples', '/examples'], include=datasets)
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
                actual_paths = (stats['nodes'] + 1) / 2
                tol = (tol_percent / 100) * expected_paths
                tol = max(tol, 5)  # fix for small trees
                self.assertTrue(expected_paths - tol <= actual_paths <= expected_paths + tol,
                                f'Expected: [{expected_paths - tol}, {expected_paths + tol}], Actual: {actual_paths}'
                                f' with {classifier} on {ds}')

if __name__ == '__main__':
    unittest.main()
