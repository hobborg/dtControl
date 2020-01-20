from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy

suite = BenchmarkSuite(timeout=60 * 60 * 1, save_folder='saved_classifiers', benchmark_file='benchmark_example',
                       rerun=True)
suite.add_datasets(['examples'],
                   include=[
                       "firewire_abst",
                       "wlan0"
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
                       # "vehicle",
                       # "aircraft"
                   ],
                   exclude=[
                       'aircraft', 'traffic_30m'
                   ]
                   )

aa = AxisAlignedSplittingStrategy()
cat = CategoricalMultiSplittingStrategy()
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
linsvc = LinearClassifierSplittingStrategy(LinearSVC, max_iter=5000)
classifiers = [
    DecisionTree(NonDeterminizer(), [aa, cat], Entropy(), 'CartCat'),
    # SafePruning(DecisionTree(NonDeterminizer(), [cart], Entropy(), 'CART')),
    # DecisionTree(NonDeterminizer(), [aa, logreg], Entropy(), 'logreg'),
    # DecisionTree(MaxFreqDeterminizer(), [aa], Entropy(), 'MaxFreq'),
    # DecisionTree(NormDeterminizer(min), [cart], Entropy(), 'MinNorm'),
    # DecisionTree(NormDeterminizer(min), [cart, logreg], Entropy(), 'minnorm-logreg'),
]
suite.benchmark(classifiers)
suite.display_html()
