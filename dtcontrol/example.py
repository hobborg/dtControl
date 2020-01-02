from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from src.benchmark_suite import BenchmarkSuite
from src.decision_tree.decision_tree import DecisionTree
from src.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
from src.decision_tree.determinization.non_determinizer import NonDeterminizer
from src.decision_tree.impurity.entropy import Entropy
from src.decision_tree.splitting.cart import CartSplittingStrategy
from src.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from src.post_processing.safe_pruning import SafePruning

suite = BenchmarkSuite(timeout=60 * 60 * 1, save_folder='saved_classifiers', benchmark_file='benchmark_example',
                       rerun=False)
suite.add_datasets(['examples'],
                   include=[
                       "cartpole",
                       # "tworooms-noneuler-latest",
                       "helicopter",
                       "cruise-latest",
                       "dcdc",
                       "10rooms",
                       "truck_trailer",
                       # "traffic_1m",
                       # "traffic_10m",
                       # "traffic_30m",
                       "vehicle",
                       # "aircraft"
                   ],
                   exclude=[
                       'aircraft', 'traffic_30m'
                   ]
                   )

cart = CartSplittingStrategy()
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
linsvc = LinearClassifierSplittingStrategy(LinearSVC, max_iter=5000)
classifiers = [
    # DecisionTree(NondetDeterminizer(), [cart], Entropy(), 'CART'),
    SafePruning(DecisionTree(NonDeterminizer(), [cart], Entropy(), 'CART')),
    # DecisionTree(NondetDeterminizer(), [cart, logreg], Entropy(), 'logreg'),
    DecisionTree(MaxFreqDeterminizer(), [cart], Entropy(), 'MaxFreq'),
    # DecisionTree(NormDeterminizer(min), [cart], Entropy(), 'MinNorm'),
    # DecisionTree(NormDeterminizer(min), [cart, logreg], Entropy(), 'minnorm-logreg'),
]
suite.benchmark(classifiers)
