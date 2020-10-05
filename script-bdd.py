from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.decision_tree.decision_tree import DecisionTree
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.pre_processing.norm_pre_processor import NormPreProcessor
from dtcontrol.decision_tree.pre_processing.random_pre_processor import RandomPreProcessor
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from dtcontrol.decision_tree.splitting.categorical_multi import CategoricalMultiSplittingStrategy
from dtcontrol.decision_tree.splitting.linear_classifier import LinearClassifierSplittingStrategy
from dtcontrol.decision_tree.splitting.oc1 import OC1SplittingStrategy
from dtcontrol.bdd import BDD

suite = BenchmarkSuite(timeout=60 * 60 * 15,
                       save_folder='saved_classifiers',
                       benchmark_file='benchmark_new_asd2',
                       rerun=True)

suite.add_datasets(['examples', 'examples/prism'],
                   include=[
                       # "firewire_abst",
                       # "wlan0",
                       # "mer10"
                       # "cartpole",
                       # "tworooms-noneuler-latest",
                       # "helicopter",
                       # "cruise-latest",
                       # "dcdc",
                       # "10rooms",
                       # "truck_trailer",
                       # "traffic_1m",
                       # "traffic_10m",
                        "traffic_30m",
                       # "vehicle",
                       # "aircraft"
                   ]
                   )

aa = AxisAlignedSplittingStrategy()
cat = CategoricalMultiSplittingStrategy()
oc1 = OC1SplittingStrategy(num_restarts=10, num_jumps=5)
logreg = LinearClassifierSplittingStrategy(LogisticRegression, solver='lbfgs', penalty='none',
                                           determinizer=MaxFreqDeterminizer())
linsvc = LinearClassifierSplittingStrategy(LinearSVC, max_iter=5000, determinizer=MaxFreqDeterminizer())
bdd_actOR = BDD(0)
bdd_actOR_minnorm = BDD(0, label_pre_processor=NormPreProcessor(min))
bdd_actUL = BDD(1)
bdd_actUL_minnorm = BDD(1, label_pre_processor=NormPreProcessor(min))
# TODO: Add parameter preprocessor to BDD
# dataset = normprocessor.preprocess(dataset)
# bdd_actUL = BDD(1, normpreprocessor)
classifiers = [
    #bdd_actOR,
    bdd_actOR_minnorm,
    #bdd_actUL,
    #bdd_actUL_minnorm
    #DecisionTree([aa], Entropy(), 'CART'),
    #DecisionTree([aa], Entropy(), 'Min', label_pre_processor=NormPreProcessor(min)),
    #DecisionTree([aa], Entropy(), 'Rand', label_pre_processor=RandomPreProcessor()),
    #DecisionTree([aa], Entropy(MaxFreqDeterminizer()), 'MaxFreq', early_stopping=True),
    #DecisionTree([aa], Entropy(MaxFreqDeterminizer(pre_determinize=False)), 'MaxFreq-post', early_stopping=True),
]
suite.benchmark(classifiers)
suite.display_html()
