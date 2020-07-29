#import project_path
import numpy as np
import pandas as pd
from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset
from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.decision_tree.decision_tree import DecisionTree
#from dtcontrol.decision_tree.determinization.non_determinizer import NonDeterminizer
from dtcontrol.decision_tree.impurity.entropy import Entropy
from dtcontrol.decision_tree.splitting.axis_aligned import AxisAlignedSplittingStrategy
from sklearn.tree import DecisionTreeClassifier
from sklearn import tree

ds = MultiOutputDataset('/home/steffi/Downloads/controllers/mux_8.kiss')
ds.load_if_necessary()
dt = DecisionTree([AxisAlignedSplittingStrategy()], Entropy(), 'CART')
dt.fit(ds)
