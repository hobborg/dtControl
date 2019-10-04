from abc import ABC, abstractmethod

class DatasetLoader(ABC):
    def __init__(self):
        self.loaded_datasets = {}

    def load_dataset(self, filename):
        if filename in self.loaded_datasets:
            return self.loaded_datasets[filename]
        return self._load_dataset(filename)

    @abstractmethod
    def _load_dataset(self, filename):
        pass