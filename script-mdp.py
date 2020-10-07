from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.multi_label_entropy import MultiLabelEntropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier_only_leaf import LinearClassifierOnlyLeafSplittingStrategy



suite = BenchmarkSuite(timeout=900,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark_file-MDP',
                       rerun=False)

suite.add_datasets(['examples/storm']) #, include=['cartpole'])

aa = AxisAlignedSplittingStrategy()
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
only_leaf = LinearClassifierOnlyLeafSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
avg_em5 = CategoricalMultiSplittingStrategy(value_grouping=True, tolerance=0.00001)
avg_inf = CategoricalMultiSplittingStrategy(value_grouping=True, tolerance=float('inf'))


classifiers = [
    DecisionTree([aa], Entropy(), 'dtC1-aa'),
    DecisionTree([aa, logreg], Entropy(), 'dtC1-LogReg'),
    DecisionTree([aa, avg_em5], Entropy(), 'dtC2-aa-em5'),
    DecisionTree([aa, logreg,avg_em5], Entropy(), 'dtC2-LogReg-em5'),
    DecisionTree([aa, avg_inf], Entropy(), 'dtC2-aa-inf'),
    DecisionTree([aa, logreg,avg_inf], Entropy(), 'dtC2-LogReg-inf'),
    DecisionTree([aa, only_leaf], Entropy(), 'Viktor')
]
suite.benchmark(classifiers)
#suite.display_html()

#Missing: Viktor, possibly alg
