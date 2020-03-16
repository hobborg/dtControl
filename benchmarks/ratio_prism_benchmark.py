from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.entropy_ratio import EntropyRatio
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_single import CategoricalSingleSplittingStrategy

suite = BenchmarkSuite(timeout=60,
                       benchmark_file='benchmarks/ratio_prism',
                       rerun=False)

suite.add_datasets(['examples/prism'])

aa = AxisAlignedSplittingStrategy()
categorical = CategoricalMultiSplittingStrategy()
grouping = CategoricalMultiSplittingStrategy(value_grouping=True)
single = CategoricalSingleSplittingStrategy()
classifiers = [
    DecisionTree(NonDeterminizer(), [aa, categorical], Entropy(), 'Cat-ent'),
    DecisionTree(NonDeterminizer(), [aa, categorical], EntropyRatio(), 'Cat-ratio'),
    DecisionTree(NonDeterminizer(), [aa, grouping], Entropy(), 'Group-ent'),
    DecisionTree(NonDeterminizer(), [aa, grouping], EntropyRatio(), 'Group-ratio'),
    DecisionTree(NonDeterminizer(), [aa, single], Entropy(), 'Single-ent'),
    DecisionTree(NonDeterminizer(), [aa, single], EntropyRatio(), 'Single-ratio'),
    DecisionTree(NonDeterminizer(), [aa, single, categorical], Entropy(), 'Both-ent'),
    DecisionTree(NonDeterminizer(), [aa, single, categorical], EntropyRatio(), 'Both-ratio'),
]
suite.benchmark(classifiers)
suite.display_html()
