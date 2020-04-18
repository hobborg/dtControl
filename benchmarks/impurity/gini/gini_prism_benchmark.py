from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.gini_index import GiniIndex
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_single import CategoricalSingleSplittingStrategy

suite = BenchmarkSuite(timeout=60,
                       benchmark_file='benchmarks/impurity/gini/gini_prism',
                       rerun=False)

suite.add_datasets(['examples/prism'])

aa = AxisAlignedSplittingStrategy()
categorical = CategoricalMultiSplittingStrategy()
grouping = CategoricalMultiSplittingStrategy(value_grouping=True)
single = CategoricalSingleSplittingStrategy()
classifiers = [
    DecisionTree(LabelPowersetDeterminizer(), [aa, categorical], Entropy(), 'Cat-ent'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, categorical], GiniIndex(), 'Cat-gini'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, grouping], Entropy(), 'Group-ent'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, grouping], GiniIndex(), 'Group-gini'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, single], Entropy(), 'Single-ent'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, single], GiniIndex(), 'Single-gini'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, single, categorical], Entropy(), 'Both-ent'),
    DecisionTree(LabelPowersetDeterminizer(), [aa, single, categorical], GiniIndex(), 'Both-gini'),
]
suite.benchmark(classifiers)
suite.display_html()
