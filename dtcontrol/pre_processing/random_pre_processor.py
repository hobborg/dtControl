import random

import numpy as np

from dtcontrol.pre_processing.label_pre_processor import LabelPreProcessor

class RandomPreProcessor(LabelPreProcessor):
    """
    Pre-processes the labels randomly.
    """

    def __init__(self):
        super().__init__()

    def preprocess_single_output(self, dataset):
        return np.apply_along_axis(lambda x: np.random.choice(x[x != -1]),
                                   axis=1,
                                   arr=dataset.y).reshape((-1, 1))

    def preprocess_multi_output(self, dataset):
        zipped = np.stack(dataset.y, axis=2)
        result = []
        for arr in zipped:
            choices = [t for t in arr if t[0] != -1]
            result.append(random.choice(choices))
        return np.array(np.split(np.array(result), len(dataset.y), 1))
