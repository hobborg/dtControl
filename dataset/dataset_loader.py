from abc import ABC, abstractmethod

class DatasetLoader(ABC):
    def __init__(self):
        self.loaded_datasets = {}

    def load_dataset(self, filename):
        if filename not in self.loaded_datasets:
            self.loaded_datasets[filename] = self._load_dataset(filename)
        return self.loaded_datasets[filename]

    """
    Loads a dataset and returns X_train, X_vars, Y_train, index_to_value
    """
    @abstractmethod
    def _load_dataset(self, filename):
        pass
