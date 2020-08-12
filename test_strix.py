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
from os import listdir, stat
from os.path import isfile, join
mypath = '/home/steffi/Downloads/controllers/'
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
sizedict = {f : stat(mypath + f).st_size for f in onlyfiles}
sizefiles = []
for file,size in sorted(sizedict.items(), key = lambda kv:(kv[1], kv[0])):
    sizefiles.append((file,size))
errorfiles = []
for i,(file,size) in enumerate(sizefiles):
    print(i, ' of ', len(onlyfiles))
    print(file)
    try:
        ds = SingleOutputDataset(mypath + file)
        ds.load_if_necessary()
        print('   Loading finished')
        dt = DecisionTree([AxisAlignedSplittingStrategy()], Entropy(), 'CART')
        dt.fit(ds)

    except Exception as e:
        errorfiles.append(file)
        #print(file)
        print('   ',e)
print(errorfiles)


ds = MultiOutputDataset('/home/steffi/Downloads/controllers/UnderapproxStrengthenedDemo.kiss.kiss')
ds.load_if_necessary()
dt = DecisionTree([AxisAlignedSplittingStrategy()], Entropy(), 'CART')
dt.fit(ds)
