from abc import ABC
import os
import numpy as np
from sklearn.neural_network import MLPClassifier
import tensorflow as tf
from tensorflow import keras
from keras import layers
import math, logging
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset
from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from dtcontrol.decision_tree.splitting.split import Split
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy

# seed_value = 42
# np.random.seed(seed_value)
# tf.random.set_seed(seed_value)

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
        reduce_lr = keras.callbacks.ReduceLROnPlateau(factor=0.1, patience=50, monitor='binary_accuracy')
        class StopAtFullAccuracy(keras.callbacks.Callback):
            def __init__(self):
                super(StopAtFullAccuracy, self).__init__()
                self.monitor = "binary_accuracy"
                self.target = 1
                self.wait = 0
                self.patience = 10
            def on_epoch_end(self, epoch, logs=None):
                metric_value = logs.get(self.monitor)
                if metric_value is not None and metric_value >= self.target:
                    self.wait += 1
                    if self.wait >= self.patience:
                        self.stopped_epoch = epoch
                        self.model.stop_training = True
                        print(f"\nStopping training as binary accuracy reached 1.")
                else:
                    self.wait = 0
        earlystop = StopAtFullAccuracy()
        if self.priority == 0:  ## TODO: Add feature to train neural network only once at the root node, remove NeuralNet from the splitting strategies thereafter
            return
        x_numeric = self.get_relevant_numeric_x(dataset)
        if x_numeric.shape[1] == 0:
            return None
        y = self.determinizer.determinize(dataset)
        splits = []
        labels, counts = np.unique(y, return_counts=True)
        self.logger.debug(f"{labels, counts}")
        labels = labels[np.argsort(-counts)]
        for label in labels:
            label_mask = (y == label)
            self.logger.debug(np.sum(label_mask))
            # input(f"Finding neural split for label {label}")
            
            load = 0
            if os.path.exists(f"NeuralModels/{dataset.filename}_label{label}_best_model"):
                load = int(input("Trained model found. Load preexisting model?"))
            if load:
                model = keras.models.load_model(f"NeuralModels/{dataset.filename}_label{label}_best_model")
            else:
                model = tf.keras.Sequential()
                normalizer = layers.Normalization(axis=1, input_shape=(x_numeric.shape[1],))
                model.add(normalizer)
                model.add(layers.Dense(32, activation='relu', name="hl1"))
                model.add(layers.Dense(64, activation='relu', name="hl2"))
                model.add(layers.Dense(32, activation='relu', name="hl3"))
                model.add(layers.Dense(1, activation='sigmoid', name="output"))
                model.summary()
                model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.002),loss=keras.losses.BinaryCrossentropy(),metrics=[keras.metrics.Accuracy(), keras.metrics.FalseNegatives(), keras.metrics.FalsePositives(), keras.metrics.TruePositives(), keras.metrics.TrueNegatives(), keras.metrics.BinaryAccuracy()])
                normalizer.adapt(x_numeric)
                normalizer.trainable = False
                model.fit(x_numeric, label_mask, epochs=10000, batch_size=len(x_numeric), callbacks=[earlystop])
                model.save(f"NeuralModels/{dataset.filename}_label{label}_best_model")
            further = int(input("Train further (0/1)?"))
            while further:
                model.fit(x_numeric, label_mask, epochs=5000, batch_size=len(x_numeric), callbacks=[earlystop, reduce_lr])
                further = int(input("Train further (0/1)?"))
            # for layer in model.layers:
            #     layer.trainable = False
            # model.compile(optimizer=keras.optimizers.Adam(learning_rate=0),loss=keras.losses.BinaryCrossentropy(),metrics=[keras.metrics.Accuracy(), keras.metrics.FalseNegatives(), keras.metrics.FalsePositives(), keras.metrics.BinaryAccuracy()])
            # model.evaluate(x_normalized, label_mask)
            # input()
            # clf = MLPClassifier(hidden_layer_sizes=(64,64), alpha = 0, tol = 1e-10, max_iter=500, solver='lbfgs')
            # pipeline = make_pipeline(standardizer, clf)
            # pipeline.fit(x_numeric, label_mask)
            # model.evaluate(x_normalized, label_mask, batch_size=None)
            # best_model = keras.models.load_model("best_model.h5")
            # self.logger.debug("Checking accuracy")
            # y_pred = best_model.predict(x_normalized)
            # y_pred_classes = np.round(y_pred).astype(int)
            # if np.array_equal(y_pred_classes, label_mask): print(f"Predictions not fully accurate")
            acc = model.evaluate(x_numeric, label_mask, batch_size=None)[-1]
            totCnt = x_numeric.shape[0]
            falseCount = totCnt * (1-acc)
            split = NeuralSplit(model, dataset.numeric_columns, self.priority)
            impurity = impurity_measure.calculate_impurity(dataset, split)
            splitData = (impurity, split, label_mask, model, acc)
            splits.append(splitData)

            self.logger.debug(f"misclassified: {round(falseCount)}" +
                  f" out of {totCnt}" +
                  f" impurity: {impurity}")
            train = 1
            if acc != 1:
                train = int(input("Train more models?"))
            if not train:
                break
            if falseCount == 0:
                # if everything is correct, we take this split
                break
        self.logger.debug(f"Impurities: {[z[0] for z in splits]}")
        imp, bestSplit, label_mask, model, accuracy = min(
        splits, key=lambda t: t[0])
        self.priority = 0
        self.logger.debug(f"Accuracy : {accuracy} \n")
        return bestSplit

class NeuralSplit(Split):
    """
    Represents a neural network split
    """
    def __init__(self, model, numeric_columns, priority = 1):
        super().__init__()
        self.model = model
        self.relevant_columns = numeric_columns
        self.priority = priority
        self.logger = logging.getLogger("nn-Logger")
        self.logger.setLevel(logging.ERROR)

    def get_masks(self, dataset):
        mask = (self.model.predict(dataset.x[:,self.relevant_columns]) > 0.5).flatten()
        self.logger.debug(f"mask {mask} : with shape {mask.shape} and true values: {np.sum(mask)}")
        return [mask,~mask]
    def predict(self, features):
        # transformed_features = self.standardizer.transform(features[:,self.relevant_columns])
        out = self.model(features[:,self.relevant_columns])
        # input(f"out : {out}")
        return 0 if (out[0][0]>0.5) else 1
    def predict_multi(self, x, ind):
        pred = (self.model(x[ind][:,self.relevant_columns])>0.5)
        return pred.numpy().flatten()
    def print_c(self):
        return super().print_c()
    def print_dot(self, variables=None, category_names=None):
        return f"Neural Network with hidden layers {[32,64,32]}"
    def print_vhdl(self):
        return super().print_vhdl()
    def to_json_dict(self, **kwargs):
        return super().to_json_dict(**kwargs)

