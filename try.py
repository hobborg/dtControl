from benchmark_suite import BenchmarkSuite
from classifiers.linear_classifier_decision_tree import LinearClassifierDecisionTree
from classifiers.cart_custom_decision_tree import CartCustomDecisionTree
from classifiers.max_every_node_decision_tree import MaxCartDecisionTree
from classifiers.max_every_node_lc_decision_tree import MaxLCDecisionTree
from classifiers.oc1_wrapper import OC1Wrapper
from sklearn.linear_model import LogisticRegression

suite = BenchmarkSuite(timeout=10000)
suite.add_datasets('../XYdatasets',
                   exclude=['aircraft', 'vehicle', 'cruise-latest', 'cruise-medium-latest'],
                   multiout=['vehicle', 'aircraft'])
classifiers = [
    CartCustomDecisionTree(),
    LinearClassifierDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
    MaxCartDecisionTree(),
    MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
    OC1Wrapper(num_restarts=20, num_jumps=5)
]
suite.benchmark(classifiers, file='benchmark_tmp.json')
