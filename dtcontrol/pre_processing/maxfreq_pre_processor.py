import numpy as np

from dtcontrol.pre_processing.label_pre_processor import LabelPreProcessor
from dtcontrol.decision_tree.determinization.max_freq_determinizer import MaxFreqDeterminizer

class MaxFreqPreProcessor(LabelPreProcessor):
    """
    Pre-processes the labels with the MaxFreq approach.
    """

    def __init__(self):
        super().__init__()

    def preprocess_single_output(self, dataset):
        return np.array([ [x] for x in MaxFreqDeterminizer.get_max_freq_labels(dataset.get_single_labels()) ])

    def preprocess_multi_output(self, dataset):
        return self.unstack(np.array([ [dataset.map_single_label_back(x)] for x in MaxFreqDeterminizer.get_max_freq_labels(dataset.get_single_labels()) ]),2)

    def unstack(self, a, axis = 0):
    	return [np.squeeze(e, axis) for e in np.split(a, a.shape[axis], axis = axis)]
