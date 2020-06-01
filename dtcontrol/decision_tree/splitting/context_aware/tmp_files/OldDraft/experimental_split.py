from dtcontrol.decision_tree.splitting.split import Split
from dtcontrol.decision_tree.splitting.context_aware.context_aware_splitting_strategy import \
    ContextAwareSplittingStrategy


class ExperimentalSplittingStrategy(ContextAwareSplittingStrategy):

    def find_split(self, dataset, impurity_measure):

        """
        :param dataset: the subset of data at the current split
        :param y: the determinized labels
        :param impurity_measure: the impurity measure to determine the quality of a potential split
        :returns: a split object
        """
        x_numeric = dataset.get_numeric_x()  # .get_numeric_x: converts all values inside dataset to type float
        splits = {}  # dict containing all splits. key names = Split Object e.g. x1 <= 160.5  values = impurity_measure
        # interates over 0...m  (m: columns)
        for feature in range(x_numeric.shape[1]):
            # all possible values of a feature sorted in a list
            values = sorted(set(x_numeric[:, feature]))
            for i in range(len(values) - 1):
                real_feature = dataset.map_numeric_feature_back(feature)
                split = ExperimentalSplit(real_feature, values[i])
                # Key:Splitobject   Value:Impurity of the split
                splits[split] = impurity_measure.calculate_impurity(dataset, split)
        if not splits:
            return None
        return min(splits.keys(), key=splits.get)

        # The min function goes over all keys, k, in the dictionary and takes the one that has minimum value after applying splits.get method.
        # The get() method returns the value specified for key, k, in the dictionary.


class ExperimentalSplit(Split):
    """
    Represents a split of the form x[i] <= b.

    e.g.    x_2 <= 2.0
            feature = 2 <class 'numpy.ndarray'>
            threshold = 2.0 <class 'numpy.float64'>
    """

    def __init__(self, feature, threshold):
        self.feature = feature
        self.threshold = threshold

    def predict(self, features):
        """
        Determines the child index of the split for one particular instance.
        :param features: the features of the instance
        :returns: the child index (0/1 for a binary split)
        """
        # features ist immer eine Zeile aus dem Datensatz in Form von einem numpy array mit dimension:
        #   (1,m) mit m:Anzahl features
        # dann wird immer das entsprechende feature aus self.feature aus diesem array entpackt und überprüft
        # ob es kleiner oder größer als der schwellenwert aus self.threshold ist
        return 0 if features[:, self.feature][0] <= self.threshold else 1

    def get_masks(self, dataset):
        """
        Returns the masks specifying this split.
        :param dataset: the dataset to be split
        :return: a list of the masks corresponding to each subset after the split

        e.g. :

        dataset:
         [[  1.    4.6   1.    3. ]
         [  1.    4.6   2.    3. ]
         [  2.   53.    2.    3. ]
         [  1.  228.    1.    5. ]
         [  2.   93.    1.    2. ]]

        self.feature = 1
        self.threshold = 4.6

        mask = [ True  True False False False]
        ~mask = not mask
        """

        mask = dataset.x[:, self.feature] <= self.threshold
        return [mask, ~mask]

    def print_dot(self, variables=None, category_names=None):
        # In case more informations are available
        if variables:
            return f'{variables[self.feature]} <= {round(self.threshold, 6)}'
        return self.print_vhdl()

    def print_c(self):
        return self.print_vhdl()

    def print_vhdl(self):
        return f'x{self.feature} <= {round(self.threshold, 6)}'
        # e.g. x0 <= 76.0
        # f-Strings -> new way of string format
        # round threshold to six decimals
