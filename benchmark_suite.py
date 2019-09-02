import project_path
from dataset import Dataset
from sklearn.metrics import accuracy_score
import glob
from os.path import join, exists, isfile
from timeout import call_with_timeout
import json
from collections import defaultdict

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

    def benchmark(self, classifiers, file='benchmark.json'):
        prev_results = self.load_results(file)
        table = []
        step = 0
        num_steps = len(self.datasets) * len(classifiers)
        for ds in self.datasets:
            prev_dataset_results = prev_results[ds.name] if ds.name in prev_results else {}
            row = []
            for classifier in classifiers:
                if classifier.name in prev_dataset_results:
                    stats = prev_dataset_results[classifier.name]
                else:
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
                msg = 'Loaded' if classifier is not None and classifier.name in prev_dataset_results else 'Tested'
                print('{} {}/{}.'.format(msg, step, num_steps))
            table.append(row)
        print('Done.')
        results = BenchmarkResults([ds.name for ds in self.datasets], [c.name for c in classifiers], table)
        self.save_results(results, file)
        return results

    def save_results(self, results, file):
        json_obj = defaultdict(dict)
        for i in range(len(results.row_names)):
            for j in range(len(results.column_names)):
                json_obj[results.row_names[i]][results.column_names[j]] = results.table[i][j]
        with open(file, 'w+') as outfile:
            json.dump(json_obj, outfile, indent=4)

    def load_results(self, file):
        if not exists(file) or not isfile(file): return {}
        with open(file, 'r') as infile:
            return json.load(infile)