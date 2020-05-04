import sys

from dtcontrol.bdd import BDD
from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.multi_label_entropy import MultiLabelEntropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.pre_processing.norm_pre_processor import NormPreProcessor

aa = AxisAlignedSplittingStrategy()
cat = CategoricalMultiSplittingStrategy(value_grouping=True)
cat2 = CategoricalMultiSplittingStrategy(value_grouping=True, tolerance=sys.maxsize)  # this is AVG with a different
# tolerance setting; in the paper we always report the best out of all
bdd_actOR = BDD(0, label_pre_processor=NormPreProcessor(min))
bdd_actUL = BDD(1, label_pre_processor=NormPreProcessor(min))

mdp_classifiers = [
    DecisionTree([aa, cat], Entropy(), 'DT'),
    bdd_actUL,
    bdd_actOR
]
mdp_classifiers2 = [
    DecisionTree([aa, cat2], Entropy(), 'DT'),
    bdd_actUL,
    bdd_actOR
]
cps_classifiers = [
    DecisionTree([aa], MultiLabelEntropy(), 'DT', early_stopping=True),
    bdd_actOR,
    bdd_actUL
]

suite = BenchmarkSuite(benchmark_file='benchmark')

suite.add_datasets(['dtcontrol-examples', 'dtcontrol-examples/prism'], include=[
    "firewire_abst",
    "ij.10",
    "beb.3-4.LineSeized",
    "eajs.2.100.5.ExpUtil",
    "zeroconf",
    "exploding-blocksworld.5",
    "firewire.true.3.200.time_min",
])
suite.benchmark(mdp_classifiers)

suite.add_datasets(['dtcontrol-examples', 'dtcontrol-examples/prism'], include=[
    "leader4",
    "csma2_4_max",
    "wlan2",
    "mer30",
])
suite.benchmark(mdp_classifiers2)

suite.add_datasets(['dtcontrol-examples'], include=[
    "cartpole",
    "10rooms",
    "helicopter"
])
suite.benchmark(cps_classifiers)
suite.display_html()
