import numpy as np

from dtcontrol.decision_tree.determinization.label_powerset_determinizer import LabelPowersetDeterminizer
from dtcontrol.decision_tree.splitting.linear_split import LinearSplit
from dtcontrol.decision_tree.splitting.context_aware.tmp_files.OldDraft.predicate_parser import PredicateParser
from dtcontrol.decision_tree.splitting.context_aware.context_aware_splitting_strategy import ContextAwareSplittingStrategy

class LinearClassifierSplittingStrategy(ContextAwareSplittingStrategy):
    """
    Represents a linear type compatible(!!) split of the form wTx + b <= 0.

    Overview of the algorithmic approach:

    1. Getting the types of the individual columns

            e.g.
            in csv files stored as:

            ...
            #BEGIN 4 1
            #TYPES Meter Meter Kilogram Meter Euro
            ...


    2. Create an individual mask for every unique feature type

            e.g. Meter
            binary_type_mask = [1, 1, 0 , 1]


    3. For every unique feature type, multiply the dataset with the binary_type_mask

            e.g. Meter
            Dataset:
            [[ 2. 93.  1.  2.]
             [ 2. 59.  3.  2.]]

            binary_type_mask = [1, 1, 0 , 1]

            x_type_modified = dataset * binary_type_mask = [[ 2. 93.  0.  2.]
                                                            [ 2. 59.  0.  2.]]

             (Repeat for every unique feature type)


    4.  Create an individual mask for every unique label

    5.  Pass the type modified dataset and the label mask to the classifier.
        Create and add splitobject to dict

    6.  Return splitobject with lowest impurity

    """
    def __init__(self, classifier_class, user_predicate="to_determine", determinizer=LabelPowersetDeterminizer(), **kwargs):
        ContextAwareSplittingStrategy.__init__(self)
        self.determinizer = determinizer
        self.classifier_class = classifier_class
        self.kwargs = kwargs
        self.user_predicate = user_predicate
        # Dict containing all splits which were used
        # Key:Splitobject   Value:(ImpurityMeasure,Distance of the split inside the graph)
        self.predicate_collection = {}

    def find_split(self, dataset, impurity_measure):
        """
                Getting the starting predicate to work with.
                If user cancels the input form, user_predicate = None --> default linear_type_classifier will run
                """

        if self.user_predicate == "to_determine":
            self.user_predicate = PredicateParser().get_predicate()

        x_numeric = dataset.get_numeric_x()

        # Edge case
        if x_numeric.shape[1] == 0:
            return None

        # y contains all labels from the current dataset
        y = self.determinizer.determinize(dataset)

        # dict containing all splits. Key:Splitobject   Value:Impurity of the split
        splits = {}

        # list of all types
        x_types = dataset.x_metadata["types"]

        for current_type in np.unique(x_types):
            # Copys
            x_numeric_copy = np.copy(x_numeric)
            x_all_types_copy = np.copy(x_types)

            # Create the mask to matrix multiply with
            binary_type_mask = (x_all_types_copy == current_type)
            x_all_types_copy[binary_type_mask] = 1.
            x_all_types_copy[~binary_type_mask] = 0.

            # Creating the new dataset to work with
            # TODO Change usage of np.multiply to a command which just zeros all the specific columns
            x_type_modified = np.multiply(np.asarray(x_numeric_copy,dtype='float64'), np.asarray(x_all_types_copy, dtype='float64'))

            # Create label mask for classifier
            for label in np.unique(y):
                new_y = np.copy(y)
                label_mask = (new_y == label)
                new_y[label_mask] = 1
                new_y[~label_mask] = -1

                classifier = self.classifier_class(**self.kwargs)


                if self.user_predicate == None:
                    # Default splitting strategy: Create split, add split, return split with lowest impurity
                    classifier.fit(x_type_modified, new_y)
                    real_features = LinearSplit.map_numeric_coefficients_back(classifier.coef_[0], dataset)
                    split = LinearClassifierSplit(classifier, real_features, dataset.numeric_columns)
                    splits[split] = impurity_measure.calculate_impurity(dataset, split)
                elif self.user_predicate != "Done":
                    # User induced Splitting strategy: User gives first predicate to start with
                    # TODO:  Get the 'perfect' parsed argument from predict_parser
                    classifier.fit(x_type_modified, new_y)
                    classifier.coef_[0], classifier.intercept_[0] = self.user_predicate
                    real_features = LinearSplit.map_numeric_coefficients_back(classifier.coef_[0], dataset)
                    split = LinearClassifierSplit(classifier, real_features, dataset.numeric_columns)
                    self.user_predicate = None
                    return split
                else:
                    # self.user_predicate == "Done"
                    # Steps after user has given the first predicate to start with
                    # TODO: Look into the dict where all splits are stored and try to use one of them and also incorporate levenstein distance into decision
                    pass

        return min(splits.keys(), key=splits.get)


class LinearClassifierSplit(LinearSplit):
    def __init__(self, classifier, real_coefficients, numeric_columns):
        super().__init__(classifier.coef_[0], classifier.intercept_[0], real_coefficients, numeric_columns)
        self.classifier = classifier
        self.numeric_columns = numeric_columns

    def get_masks(self, dataset):
        mask = self.classifier.predict(dataset.get_numeric_x()) == -1
        return [mask, ~mask]

    def predict(self, features):
        return 0 if self.classifier.predict(features[:, self.numeric_columns])[0] == -1 else 1
