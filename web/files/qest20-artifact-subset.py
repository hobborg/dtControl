from dtcontrol.bdd import BDD
from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.multi_label_entropy import MultiLabelEntropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.pre_processing.norm_pre_processor import NormPreProcessor

suite = BenchmarkSuite(save_folder='saved_classifiers',
                       benchmark_file='benchmark',
                       rerun=False)

suite.add_datasets(['dtcontrol-examples', 'dtcontrol-examples/prism'],
                   include=[
                       "firewire_abst",
                       "leader4",
                       "beb.3-4.LineSeized",
                       "csma2_4_max",
                       "eajs.2.100.5.ExpUtil",
                       "wlan2",
                       "zeroconf",
                       "cartpole",
                       "10rooms"
                   ]
                   )

aa = AxisAlignedSplittingStrategy()
cat = CategoricalMultiSplittingStrategy(value_grouping=True, tolerance=0.05)
bdd_actOR = BDD(0, label_pre_processor=NormPreProcessor(min))
bdd_actUL = BDD(1, label_pre_processor=NormPreProcessor(min))
classifiers = [
    DecisionTree([aa], MultiLabelEntropy(), 'Multi-label', early_stopping=True),
    DecisionTree([cat], Entropy(), 'AVG'),
    bdd_actUL
]
suite.benchmark(classifiers)
