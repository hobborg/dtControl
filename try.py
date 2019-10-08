from benchmark_suite import BenchmarkSuite
from classifiers.linear_classifier_decision_tree import LinearClassifierDecisionTree
from classifiers.cart_custom_decision_tree import CartCustomDecisionTree
from classifiers.max_every_node_decision_tree import MaxCartDecisionTree
from classifiers.max_every_node_lc_decision_tree import MaxLCDecisionTree
from classifiers.oc1_wrapper import OC1Wrapper
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

suite = BenchmarkSuite()
suite.add_datasets('../XYdatasets',
                   include=['cartpole'],
                   exclude=['cruise-latest',
                            'cruise-medium-latest',
                            'cruise-small-latest',
                            #'cartpole',
                            'tworooms_large',
                            'aircraft',
                            'vehicle'
                            ],
                   multiout=['vehicle', 'aircraft', '10rooms'])
classifiers = [CartCustomDecisionTree(),
               #LinearClassifierDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
               LinearClassifierDecisionTree(LinearSVC, max_iter=5000),
               MaxCartDecisionTree(),
               #MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
               OC1Wrapper(num_restarts=20, num_jumps=5)
               ]
suite.benchmark(classifiers, file='benchmark.json')
