import numpy as np

from dtcontrol.pre_processing.label_pre_processor import LabelPreProcessor

class NormPreProcessor(LabelPreProcessor):
    """
    Pre-processes the labels with the (min/max)-norm approach.
    """

    def __init__(self, comp):
        """
        :param comp: the comparison function to be used, either min or max
        """
        super().__init__()
        self.comp = comp

    def preprocess_single_output(self, dataset):
        return np.apply_along_axis(lambda x: self.comp(x[x != -1], key=lambda i: dataset.index_to_actual[i] ** 2),
                                   axis=1,
                                   arr=dataset.y).reshape((-1, 1))

    def preprocess_multi_output(self, dataset):
        zipped = np.stack(dataset.y, axis=2)
        result = []
        for arr in zipped:
            result.append(self.comp([t for t in arr if t[0] != -1],
                                    key=lambda t: sum(dataset.index_to_actual[j] ** 2 for j in t)))
        return np.array(np.split(np.array(result), len(dataset.y), 1))
