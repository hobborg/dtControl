import project_path
from dataset import Dataset
from sklearn.metrics import accuracy_score
import glob
from os.path import join
from timeout import call_with_timeout

class BenchmarkResults:
    """
    The benchmark results store the benchmark data in a table format (dataset x classifier -> results).
    """

    def __init__(self, row_names, column_names, table):
        self.row_names = row_names
        self.column_names = column_names
        self.table = table

class BenchmarkSuite:
    """
    The benchmark suite runs the given classifiers on all datasets present in the XYdatasets folder and prints the
    results.

    The classifiers have to satisfy the following interface:
        classifier.name returns the name to be displayed in the results
        classifier.needs_unique_labels returns true if the classifier cannot handle multi-labels
        classifier.fit(X_train, Y_train) trains the classifier on the given dataset
        classifier.predict(X) returns an array of the classifiers predictions for X
        classifier.get_stats() returns a dictionary of statistics to be displayed (e.g. the number of nodes in the tree)
    """

    def __init__(self, timeout=60):
        self.datasets = []
        self.timeout = timeout

    def load_datasets(self, path, exclude=None):
        if not exclude:
            exclude = []
        for (X_file, Y_file) in self.get_XY_files(path):
            if Dataset.get_dataset_name(X_file) not in exclude:
                self.datasets.append(Dataset(X_file, Y_file))

    def get_XY_files(self, path):
        return [(file, '{}_Y.npy'.format(file.split('_X.')[0])) for file in glob.glob(join(path, '*.pickle'))]

    def benchmark(self, classifiers):
        table = []
        step = 0
        num_steps = len(self.datasets) * len(classifiers)
        for ds in self.datasets:
            row = []
            for classifier in classifiers:
                Y_train = ds.get_labels_as_unique() if classifier.needs_unique_labels else ds.Y_train
                classifier, success = call_with_timeout(classifier, 'fit', ds.X_train, Y_train, timeout=self.timeout)
                if success:
                    pred = classifier.predict(ds.X_train)
                    if len(pred[pred == None]) != 0:
                        stats = 'failed to fit'
                    else:
                        acc = accuracy_score(pred, Y_train)
                        stats = classifier.get_stats()
                        stats['accuracy'] = acc
                else:
                    stats = 'timeout'
                row.append(stats)
                step += 1
                print('Finished {}/{}.'.format(step, num_steps))
            table.append(row)
        print('Done.')
        return BenchmarkResults([ds.name for ds in self.datasets], [c.name for c in classifiers], table)
