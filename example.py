from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.bin_count_determinizer import BinCountDeterminizer
from dtcontrol.decision_tree.impurity.bin_count_entropy import AvgBinCount
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.oc1 import OC1SplittingStrategy

suite = BenchmarkSuite(timeout=60 * 60 * 3,
                       save_folder='saved_classifiers',
                       benchmark_file='bincount',
                       rerun=True)

suite.add_datasets(['examples', 'examples/prism'],
                   include=[
                       # "firewire_abst",
                       # "wlan0",
                       # "mer10"
                       "cartpole",
                       # "tworooms-noneuler-latest",
                       "helicopter",
                       # "cruise-latest",
                       # "dcdc",
                       # "10rooms",
                       # "truck_trailer",
                       # "traffic_1m",
                       # "traffic_10m",
                       # "traffic_30m",
                       # "vehicle",
                       # "aircraft"
                   ]
                   )

aa = AxisAlignedSplittingStrategy()
cat = CategoricalMultiSplittingStrategy()
oc1 = OC1SplittingStrategy(num_restarts=10, num_jumps=5)
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
linsvc = LinearClassifierSplittingStrategy(LinearSVC, max_iter=5000)
classifiers = [
    # DecisionTree(MaxFreqDeterminizer(), [aa], Entropy(), 'MaxFreq'),
    DecisionTree(BinCountDeterminizer(), [aa], AvgBinCount(), 'BinCount'),
    # SafePruning(DecisionTree(NonDeterminizer(), [aa], Entropy(), 'safe pruning')),
]
suite.benchmark(classifiers)
suite.display_html()
