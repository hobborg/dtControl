from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.impurity.multi_label_entropy import MultiLabelEntropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier_only_leaf import LinearClassifierOnlyLeafSplittingStrategy


suite = BenchmarkSuite(timeout=900,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark_file-CPS',
                       rerun=False)

suite.add_datasets(['examples/cps'], exclude=['aircraft','vehicle','traffic_30m']) #, include=['cartpole'])

aa = AxisAlignedSplittingStrategy()
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')
only_leaf = LinearClassifierOnlyLeafSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none')

classifiers = [
    DecisionTree([aa], Entropy(), 'dtC1-aa'),
    DecisionTree([aa, logreg], Entropy(), 'dtC1-LogReg'),
    DecisionTree([aa], Entropy(MaxFreqDeterminizer()), 'dtC1-aa-MaxFreq', early_stopping=True),
    DecisionTree([aa, logreg], Entropy(MaxFreqDeterminizer()), 'dtC1-LogReg-MaxFreq', early_stopping=True),
    DecisionTree([aa], MultiLabelEntropy(), 'dtC2-aa-MLE', early_stopping=True),
    DecisionTree([aa, logreg], MultiLabelEntropy(), 'dtC2-LogReg-MLE', early_stopping=True),
    DecisionTree([aa, only_leaf], Entropy(), 'Viktor'),
    DecisionTree([aa, only_leaf], MultiLabelEntropy(), 'Viktor-MLE', early_stopping=True)
]
suite.benchmark(classifiers)
#suite.display_html()

#Missing: Viktor, alg and alg MLE
#Also: alg on aircraft and vehicle
#Also: traffic_30m has the weirdest bugs...
