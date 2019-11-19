import os
import unittest

from sklearn.linear_model import LogisticRegression

from src.benchmark_suite import BenchmarkSuite
from src.classifiers.cart_custom_dt import CartDT
from src.classifiers.linear_classifier_dt import LinearClassifierDT
from src.classifiers.max_freq_dt import MaxFreqDT
from src.classifiers.max_freq_linear_classifier_dt import MaxFreqLinearClassifierDT
from src.classifiers.norm_dt import NormDT
from src.classifiers.norm_linear_classifier_dt import NormLinearClassifierDT
from src.classifiers.oc1_wrapper import OC1Wrapper

class IntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.suite = BenchmarkSuite(timeout=60 * 5,
                                    save_folder='test_saved_classifiers',
                                    benchmark_file='test_benchmark',
                                    rerun=True)
        self.expected_results = {
            'cartpole': {
                'CART': 127,
                'LinearClassifierDT-LogisticRegression': 100,  # this is different from the table but apparently correct
                'OC1': 92,
                'MaxFreqDT': 6,
                'MaxFreq-LinearClassifierDT-LogisticRegression': 7,
                'MinNormDT': 56,
                'MinNorm-LinearClassifierDT-LogisticRegression': 16
            },
            'cruise-latest': {
                'CART': 494,
                'LinearClassifierDT-LogisticRegression': 392,
                'OC1': -1,  # TODO
                'MaxFreqDT': 2,
                'MaxFreq-LinearClassifierDT-LogisticRegression': 2,
                'MinNormDT': 282,
                'MinNorm-LinearClassifierDT-LogisticRegression': 197
            },
            'dcdc': {
                'CART': 136,
                'LinearClassifierDT-LogisticRegression': 140,
                'OC1': -1,  # TODO
                'MaxFreqDT': 5,
                'MaxFreq-LinearClassifierDT-LogisticRegression': 5,
                'MinNormDT': 11,
                'MinNorm-LinearClassifierDT-LogisticRegression': 125
            },
            '10rooms': {
                'CART': 8649,
                'LinearClassifierDT-LogisticRegression': 74,
                'OC1': -1,  # TODO
                'MaxFreqDT': 4,
                'MaxFreq-LinearClassifierDT-LogisticRegression': 10,
                'MinNormDT': 2704,
                'MinNorm-LinearClassifierDT-LogisticRegression': 28
            },
            'vehicle': {
                'CART': 6619,
                'LinearClassifierDT-LogisticRegression': 5195,  # again different from table
                'OC1': -1  # TODO
            }
        }
        os.remove('test_benchmark.json')

    def test_fast(self):
        datasets = ['cartpole', '10rooms', 'vehicle']
        classifiers = [CartDT(), MaxFreqDT(), NormDT(min)]
        self.run_test(datasets, classifiers)

    def test_medium(self):
        datasets = ['cartpole', '10rooms', 'vehicle']
        classifiers = [CartDT(),
                       LinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none'),
                       MaxFreqDT(),
                       MaxFreqLinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none'),
                       NormDT(min)
                       ]
        self.run_test(datasets, classifiers)

    def test_slow(self):
        datasets = [
            'cartpole',
            'cruise-latest',
            'dcdc',
            '10rooms',
            'vehicle'
        ]
        classifiers = [CartDT(),
                       LinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none'),
                       OC1Wrapper(),
                       MaxFreqDT(),
                       MaxFreqLinearClassifierDT(LogisticRegression, solver='lbfgs', penalty='none'),
                       NormDT(min),
                       NormLinearClassifierDT(min, LogisticRegression, solver='lbfgs', penalty='none')
                       ]
        self.run_test(datasets, classifiers)

    def run_test(self, datasets, classifiers):
        self.suite.add_datasets(['../examples'], include=datasets)
        self.suite.benchmark(classifiers)
        self.assert_results_almost_equal(self.expected_results, self.suite.results)

    def assert_results_almost_equal(self, expected, actual, tol_percent=5):
        for ds in actual:
            for classifier in actual[ds]['classifiers']:
                if classifier not in expected[ds]:
                    continue
                expected_paths = expected[ds][classifier]
                actual_paths = (actual[ds]['classifiers'][classifier]['stats']['nodes'] + 1) / 2
                tol = (tol_percent / 100) * expected_paths
                tol = max(tol, 5)  # fix for small trees
                self.assertTrue(expected_paths - tol <= actual_paths <= expected_paths + tol,
                                f'Expected: [{expected_paths - tol}, {expected_paths + tol}], Actual: {actual_paths}'
                                f' with {classifier} on {ds}')

if __name__ == '__main__':
    unittest.main()
