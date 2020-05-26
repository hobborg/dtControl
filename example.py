from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.context_aware.weinhuber_approach_splitting_strategy import \
    WeinhuberApproachSplittingStrategy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy

suite = BenchmarkSuite(timeout=999,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark',
                       rerun=True)

suite.add_datasets(['examples', 'examples/prism', 'examples/storm'], include=['fruits_dataset'])

weinhuber = WeinhuberApproachSplittingStrategy()
weinhuber.priority = 1

aa = AxisAlignedSplittingStrategy()
aa.priority = 0

classifiers = [
    DecisionTree([weinhuber, aa], Entropy(), 'Testing')
]
suite.benchmark(classifiers)
suite.display_html()
