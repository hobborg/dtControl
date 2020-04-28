from abc import ABC, abstractmethod

from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset
from dtcontrol.dataset.single_output_dataset import SingleOutputDataset

class LabelPreProcessor(ABC):

    def preprocess(self, dataset):
        """
        Returns the pre-processed dataset.
        """
        if isinstance(dataset, SingleOutputDataset):
            copy = SingleOutputDataset(dataset.filename)
            copy.copy_from_other_dataset(dataset)
            copy.y = self.preprocess_single_output(dataset)
        else:
            copy = MultiOutputDataset(dataset.filename)
            copy.copy_from_other_dataset(dataset)
            copy.y = self.preprocess_multi_output(dataset)
        return copy

    @abstractmethod
    def preprocess_single_output(self, dataset):
        pass

    @abstractmethod
    def preprocess_multi_output(self, dataset):
        pass
