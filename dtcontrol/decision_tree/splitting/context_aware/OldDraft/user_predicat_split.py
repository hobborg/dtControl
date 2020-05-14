from dtcontrol.decision_tree.splitting.split import Split
from dtcontrol.decision_tree.splitting.splitting_strategy import SplittingStrategy


class UserPredicatSplittingStrategy(SplittingStrategy):
    def __init__(self, user_predicate="to_determine"):

        # Stores inital predicate
        self.user_predicate = user_predicate

        # Dict containing all splits which were used
        # Key:Splitobject   Value:(ImpurityMeasure, Location in Graph)
        self.predicate_collection = {}

    def find_split(self, dataset, impurity_measure):
        """
        :param dataset: the subset of data at the current split
        :param y: the determinized labels
        :param impurity_measure: the impurity measure to determine the quality of a potential split
        :returns: a split object
        """
        print(self.user_predicate)


class UserPredicateSplit(Split):
    """
    Represents a split of the form x[i] <= b.
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
        return 0 if features[:, self.feature][0] <= self.threshold else 1

    def get_masks(self, dataset):
        """
        Returns the masks specifying this split.
        :param dataset: the dataset to be split
        :return: a list of the masks corresponding to each subset after the split

        e.g. :

        dataset:
        [[ 1. 93.  1.  2.]
        [ 1. 59.  3.  2.]]

        feature: 1
        threshold: 76.0
        mask = [93. <= threshold  59 <= threshold] = [False  True]
        ~mask = not mask = [ True False]

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