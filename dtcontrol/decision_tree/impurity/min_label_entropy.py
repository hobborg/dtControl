import sys, math

import numpy as np

from dtcontrol.decision_tree.impurity.determinizing_impurity_measure import DeterminizingImpurityMeasure

class MinLabelEntropy(DeterminizingImpurityMeasure):
    """
    Tries to finish one label first.

    Estimates for every label y, how difficult it will be to to separate the
    label y in both partions after this split.
    Then it returns the value of the best label.
    
    The strategy we want to provoke with this impurity measure is to first,
    fully separate one label and then continue with the next one.
    Specifically, if we can completely separate one label the impurity
    for this split is 0 and we definitely select such a spilt.
    """ 
    def calculate_impurity(self, dataset, split):
        masks = split.get_masks(dataset)
        if len(masks) == 1:
            return sys.maxsize
        if self.determinizer.pre_determinized_labels is not None:
            labels = self.determinizer.pre_determinized_labels
        else:
            labels = self.determinizer.determinize(dataset)
        subset_left_right = [
            self.determinizer.determinize(dataset.from_mask_optimized(mask)) 
            for mask in masks
        ]
        impurities = []
        for label in np.unique(labels):
            imp = 0
            for subset in subset_left_right:
                subsetSize = len(subset)
                if subsetSize == 0:
                    return sys.maxsize
                prob = len(subset[subset == label]) / subsetSize
                entropy = -prob * np.log2(prob) if prob > 0 else 0
                imp += (subsetSize / len(dataset)) * entropy
            impurities.append(imp)
        return min(impurities)

    def get_oc1_name(self):
        return 'min_label_entropy'
