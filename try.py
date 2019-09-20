from sklearn.tree import DecisionTreeClassifier
from sklearn.multioutput import MultiOutputClassifier
from benchmark_suite import BenchmarkSuite
from max_every_node_decision_tree import MaxEveryNodeDecisionTree
from decision_tree_wrapper import DecisionTreeWrapper
from unique_label_decision_tree import UniqueLabelDecisionTree
from smarter_splits.LinearClassifierDecisionTree import LinearClassifierDecisionTree
from smarter_splits.OC1Wrapper import OC1Wrapper
from sklearn.linear_model import LogisticRegression
from table_printer import print_table
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from dataset import MultiOutputDataset
from label_format import LabelFormat
from multi_output_decision_tree import MultiOutputDecisionTree

suite = BenchmarkSuite(timeout=100)
suite.load_datasets('../XYdatasets', exclude=[], multiout=['vehicle'])
classifiers = [
               MultiOutputDecisionTree(presort=False,criterion='entropy', min_samples_split=2)
              ]
suite.benchmark(classifiers, file='benchmark_tmp.json')