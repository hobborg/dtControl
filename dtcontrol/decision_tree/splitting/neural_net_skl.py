from abc import ABC
import numpy as np
from sklearn.neural_network import MLPClassifier
import math, logging
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from dtcontrol.decision_tree.splitting.split import Split
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy

class NeuralNetSplittingStrategy(SplittingStrategy):
    def __init__(self, determinizer=LabelPowersetDeterminizer()):
        super().__init__()
        self.determinizer = determinizer
        self.logger = logging.getLogger("nn-Logger")
        self.logger.setLevel(logging.DEBUG)
    def calc_all_feature_importance(self, dataset):
        """
        Returns an array of values ∈ [0., 1.] for every feature with 
        0.0: the feature has no impact
        1.0: the feature is very important

        Note that this only gives an approximation for the *most permissive* controller.
        """
        # Keep track of already ignored features so that we do not ignore both
        # features in this example:
        # |    X
        # | O   
        # +----->
        featureImportance = []
        ignoredFeatures = [] 
        for i in range(dataset.x.shape[1]):
            imp = self.calc_single_feature_importance(dataset, i, ignoredFeatures)
            featureImportance.append(imp)
            if imp == 0:
                ignoredFeatures.append(i)
        return featureImportance
    
    def calc_single_feature_importance(self, dataset, featureInd, ignoredFeatures):
        # implementation depends on whether ys is single or multi output
        if isinstance(dataset, MultiOutputDataset):
            # take maximum over all y labels
            return max([
                self.calc_feature_importance_for_y(
                    dataset, featureInd, dataset.y[i], ignoredFeatures
                ) for i in range(dataset.y.shape[0])
        ])
        else:
            return self.calc_feature_importance_for_y(dataset, featureInd, dataset.y, ignoredFeatures)

    def calc_feature_importance_for_y(self, dataset, featureInd, y, ignoredFeatures):
        x = dataset.x
        fVals = np.unique(x[:, featureInd])
        if len(fVals) <= 1:
            return 0 # feature is constant -> no information
        # leave out the feature (and all already ignored ones)
        # group same x-values
        # then see if all those have the same label
        xInds = [i for i in range(x.shape[1])
                    if i != featureInd and not i in ignoredFeatures]
        yInds = list(range(x.shape[1], x.shape[1] + y.shape[1]))
        xy = np.concatenate((x,y), axis=1)
        df = pd.DataFrame(xy)
        df = df.groupby(xInds).nunique()[yInds]
        # df : y1, y2, y3
        #    :  1,  3,  2
        #    :  1,  1,  1
        df = (df == [1 for _ in yInds]).all(axis=1)
        eqCnt = df.sum()
        nonEqCnt = (~df).sum()
        tot = eqCnt + nonEqCnt
        return nonEqCnt / tot
    
    def get_relevant_numeric_x(self, dataset, min_feature_importance=1e-9):
        if dataset.numeric_x is None:
            if dataset.treat_categorical_as_numeric:
                dataset.numeric_columns = set(range(dataset.x.shape[1]))
            else:
                dataset.numeric_columns = set(range(dataset.x.shape[1])).difference(set(dataset.x_metadata['categorical']))
            dataset.feature_importance = self.calc_all_feature_importance(dataset)
            irrelevant_cols = {col for col in range(dataset.x.shape[1]) if dataset.feature_importance[col] < min_feature_importance}
            dataset.numeric_columns -= irrelevant_cols
            dataset.numeric_columns = sorted(list(dataset.numeric_columns))
            dataset.numeric_feature_mapping = {i: dataset.numeric_columns[i] for i in range(len(dataset.numeric_columns))}
            dataset.numeric_x = dataset.x[:, dataset.numeric_columns]
        return dataset.numeric_x
    def find_split(self, dataset, impurity_measure, **kwargs):
        if self.priority == 0:  ## TODO: Add feature to train neural network only once at the root node, remove NeuralNet from the splitting strategies thereafter
            return
        x_numeric = self.get_relevant_numeric_x(dataset)
        if x_numeric.shape[1] == 0:
            return None

        y = self.determinizer.determinize(dataset)
        splits = []
        labels, counts = np.unique(y, return_counts=True)
        labels = labels[np.argsort(-counts)]
        for label in labels:
            label_mask = (y == label)
            standardizer = StandardScaler()
            clf = MLPClassifier(hidden_layer_sizes=(64,64), alpha = 0,n_iter_no_change=50, tol = 1e-10, max_iter=500, solver='lbfgs' , verbose=True)
            pipeline = make_pipeline(standardizer, clf)
            pipeline.fit(x_numeric, label_mask)
            acc = pipeline.score(x_numeric, label_mask)
            totCnt = x_numeric.shape[0]
            falseCount = totCnt * (1-acc)
            split = NeuralSplit(pipeline, dataset.numeric_columns, self.priority)
            impurity = impurity_measure.calculate_impurity(dataset, split)
            splitData = (impurity, split, label_mask, standardizer, clf)
            splits.append(splitData)

            self.logger.debug(f"misclassified: {round(falseCount)}" +
                  f" out of {totCnt} iterations: {clf.n_iter_}" +
                  f" impurity: {impurity}" +
                  f"\n Samples encountered = {clf.t_}")
            if falseCount == 0:
                # if everything is correct, we take this split
                break
        self.logger.debug(f"Impurities: {[z[0] for z in splits]}")
        imp, bestSplit, label_mask, standardizer, clf = min(
        splits, key=lambda t: t[0])
        self.priority = 0
        accuracy = bestSplit.pipeline.score(x_numeric, label_mask)
        self.logger.debug(f"Accuracy : {accuracy} \n")
        return bestSplit

class NeuralSplit(Split):
    """
    Represents a neural network split
    """
    def __init__(self, pipeline, numeric_columns, priority = 1):
        super().__init__()
        self.pipeline = pipeline
        self.relevant_columns = numeric_columns
        self.priority = priority
        self.logger = logging.getLogger("nn-Logger")
        self.logger.setLevel(logging.DEBUG)

    def get_masks(self, dataset):
        mask = self.pipeline.predict(dataset.x[:,self.relevant_columns])
        # print(mask)
        return [mask,~mask]
    def predict(self, features):
        out = self.pipeline.predict(features[:,self.relevant_columns])
        return 0 if out[0] else 1
    def print_c(self):
        return super().print_c()
    def print_dot(self, variables=None, category_names=None):
        return f"Neural Network with hidden layers {self.pipeline[1].hidden_layer_sizes} and {self.pipeline[1].solver} solver"
    def print_vhdl(self):
        return super().print_vhdl()
    def to_json_dict(self, **kwargs):
        return super().to_json_dict(**kwargs)

