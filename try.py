from sklearn.tree import DecisionTreeClassifier
from sklearn.multioutput import MultiOutputClassifier
from benchmark_suite import BenchmarkSuite
from max_every_node_lc_decision_tree import MaxEveryNodeLCDecisionTree
from max_every_node_decision_tree import MaxEveryNodeDecisionTree
from decision_tree_wrapper import DecisionTreeWrapper
from unique_label_decision_tree import UniqueLabelDecisionTree
from linear_classifier_decision_tree import LinearClassifierDecisionTree
from smarter_splits.OC1Wrapper import OC1Wrapper
from sklearn.linear_model import LogisticRegression
from table_printer import print_table
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from dataset import MultiOutputDataset
from label_format import LabelFormat
from multi_output_decision_tree import MultiOutputDecisionTree
from standard_custom_decision_tree import StandardCustomDecisionTree

suite = BenchmarkSuite(timeout=10000)
suite.load_datasets('../XYdatasets',
                    exclude=['aircraft', 'vehicle', 'cruise-latest', 'cruise-medium-latest', 'tworooms_large'],
                    multiout=['vehicle', 'aircraft'])
classifiers = [
    MaxEveryNodeLCDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
    MaxEveryNodeDecisionTree(),
    StandardCustomDecisionTree(),
    LinearClassifierDecisionTree(LogisticRegression, solver='lbfgs', penalty='none'),
]
suite.benchmark(classifiers, file='benchmark_tmp.json')
