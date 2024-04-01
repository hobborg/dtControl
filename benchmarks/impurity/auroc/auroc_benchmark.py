from sklearn.linear_model import LogisticRegression

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
from dtcontrol.decision_tree.impurity.auroc import AUROC
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy

suite = BenchmarkSuite(timeout=60 * 10,
                       benchmark_file='auroc',
                       rerun=False)

suite.add_datasets(['../../../examples'],
                   include=[
                       "cartpole",
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
                   ]
                   )

aa = AxisAlignedSplittingStrategy()
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty=None)

classifiers = [
    DecisionTree([aa, logreg], Entropy(), 'logreg-ent'),
    DecisionTree([aa, logreg], AUROC(), 'logreg-auroc'),
    DecisionTree([aa, logreg], Entropy(MaxFreqDeterminizer()), 'MaxFreq-logreg-ent', early_stopping=True),
    DecisionTree([aa, logreg], AUROC(MaxFreqDeterminizer()), 'MaxFreq-logreg-auroc',  early_stopping=True),
]
suite.benchmark(classifiers)
suite.display_html()
