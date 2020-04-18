from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.entropy_ratio import EntropyRatio
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_single import CategoricalSingleSplittingStrategy

suite = BenchmarkSuite(timeout=60,
                       benchmark_file='benchmarks/impurity/ratio/ratio_prism',
                       rerun=False)

suite.add_datasets(['examples/prism'])

aa = AxisAlignedSplittingStrategy()
categorical = CategoricalMultiSplittingStrategy()
grouping = CategoricalMultiSplittingStrategy(value_grouping=True)
single = CategoricalSingleSplittingStrategy()
classifiers = [
    DecisionTree(LabelPowersetDeterminizer(), [aa, categorical], Entropy(), 'Cat-ent'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, categorical], EntropyRatio(), 'Cat-ratio'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, grouping], Entropy(), 'Group-ent'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, grouping], EntropyRatio(), 'Group-ratio'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, single], Entropy(), 'Single-ent'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, single], EntropyRatio(), 'Single-ratio'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, single, categorical], Entropy(), 'Both-ent'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, single, categorical], EntropyRatio(), 'Both-ratio'),
]
suite.benchmark(classifiers)
suite.display_html()
