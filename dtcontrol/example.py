from sklearn.linear_model import LogisticRegression

from src.benchmark_suite import BenchmarkSuite
from src.classifiers.decision_tree import DecisionTree
from src.classifiers.determinization.nondet_determinizer import NondetDeterminizer
from src.classifiers.impurity.entropy import Entropy
from src.classifiers.splitting.cart import CartSplittingStrategy
from src.classifiers.splitting.linear_classifier import LinearClassifierSplittingStrategy

suite = BenchmarkSuite(timeout=60 * 5, save_folder='saved_classifiers', benchmark_file='benchmark_example', rerun=True)
suite.add_datasets(['examples'],
                   include=[
                       # "cartpole",
                       # "tworooms-noneuler-latest",
                       # "helicopter",
                       # "cruise-latest",
                       # "dcdc",
                       # "10rooms",
                       # "truck_trailer",
                       # "traffic_1m",
                       # "traffic_10m",
                       # "traffic_30m",
                       "vehicle",
                       # "aircraft"
                   ],
                   exclude=[
                       'aircraft', 'traffic_30m', 'truck_trailer'
                   ]
                   )
logistic = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
classifiers = [
    DecisionTree(NondetDeterminizer(), [CartSplittingStrategy()], Entropy(), 'Cart'),
    DecisionTree(NondetDeterminizer(), [CartSplittingStrategy(), logistic], Entropy(), 'Logistic'),
    # DecisionTree(MaxFreqDeterminizer(), [CartSplittingStrategy()], Entropy(), 'MaxFreq'),
    # DecisionTree(NormDeterminizer(min), [CartSplittingStrategy()], Entropy(), 'MinNorm'),
    # DecisionTree(NormDeterminizer(min), [CartSplittingStrategy(), logistic], Entropy(), 'MinNormLogistic'),
    # LinearClassifierDecisionTree(LinearSVC, max_iter=5000),
    # MaxLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
    # OC1Wrapper(num_restarts=1, num_jumps=1),
    # BDD()
    # MaxEveryNodeMultiDecisionTree()
]
suite.benchmark(classifiers)
