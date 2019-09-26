import project_path
from dataset import Dataset, MultiOutputDataset, AnyLabelDataset
import glob
from os.path import join, exists, isfile
from timeout import call_with_timeout
import json
from collections import defaultdict
from label_format import LabelFormat
from datetime import timedelta
import sys

class BenchmarkResults:
    """
    The benchmark results store the benchmark data in a table format (dataset x classifier -> results).

    :param row_names: the names of the datasets
    :param column_names: the names of the classifiers
    :param table: a two-dimensional array of result dictionaries
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
        classifier.label_format returns the {LabelFormat} format of the classifier
        classifier.fit(X_train, Y_train) trains the classifier on the given dataset
        classifier.predict(X) returns an array of the classifiers predictions for X
        classifier.get_stats() returns a dictionary of statistics to be displayed (e.g. the number of nodes in the tree)
    """

    def __init__(self, timeout=sys.maxsize):
        self.datasets = []
        self.timeout = timeout

    def add_datasets(self, path, exclude=None, multiout=None):
        if not exclude:
            exclude = []
        if not multiout:
            multiout = []
        self.datasets = []
        for (X_file, Y_file) in self.get_XY_files(path):
            if Dataset.get_dataset_name(X_file) not in exclude:
                if Dataset.get_dataset_name(X_file) in multiout:
                    ds = MultiOutputDataset(X_file, Y_file)
                else:
                    ds = AnyLabelDataset(X_file, Y_file)
                self.datasets.append(ds)
        self.datasets.sort(key=lambda ds: ds.name)

    def get_XY_files(self, path):
        return [(file, '{}_Y.npy'.format(file.split('_X.')[0])) for file in glob.glob(join(path, '*.pickle'))]

    def benchmark(self, classifiers, file='benchmark.json'):
        prev_results = self.load_results(file)
        num_steps = self.count_num_steps(classifiers, prev_results)
        self.print_max_wait_time(num_steps)
        table = []
        step = 0
        for ds in self.datasets:
            row = []
            for classifier in classifiers:
                stats, computed = self.compute_stats(ds, classifier, prev_results)
                row.append(stats)
                if computed:
                    step += 1
                    print('Evaluated {} on {} ({}/{}).'.format(classifier.name, ds.name, step, num_steps))
            table.append(row)
        print('Done.')
        results = BenchmarkResults([ds.name for ds in self.datasets], [c.name for c in classifiers], table)
        self.save_results(results, file)
        return results

    def print_max_wait_time(self, num_steps):
        if num_steps > 0 and self.timeout != sys.maxsize:
            total_seconds = num_steps * self.timeout
            seconds = total_seconds % 60
            total_minutes = int(total_seconds / 60)
            minutes = total_minutes % 60
            hours = int(total_minutes / 60)
            print('Maximum wait time: {}h {}m {}s.'.format(hours, minutes, seconds))

    def count_num_steps(self, classifiers, prev_results):
        num_steps = 0
        for ds in self.datasets:
            for classifier in classifiers:
                if not self.already_computed(ds, classifier, prev_results) and \
                        ds.is_applicable(classifier.label_format):
                    num_steps += 1
        return num_steps

    def compute_stats(self, dataset, classifier, prev_results):
        if self.already_computed(dataset, classifier, prev_results):
            computed = False
            stats = prev_results[classifier.name][dataset.name]
        elif not dataset.is_applicable(classifier.label_format):
            computed = False
            stats = 'not applicable'
        else:
            computed = True
            dataset.load_if_necessary()
            stats = self.train_and_get_stats(dataset, classifier)
        return stats, computed

    @staticmethod
    def already_computed(dataset, classifier, prev_results):
        return classifier.name in prev_results and dataset.name in prev_results[classifier.name]

    def train_and_get_stats(self, dataset, classifier):
        Y_train = dataset.get_labels_for_format(classifier.label_format)
        classifier, success = call_with_timeout(classifier, 'fit', dataset.X_train, Y_train, timeout=self.timeout)
        if success:
            acc = dataset.compute_accuracy(classifier.predict(dataset.X_train), classifier.label_format)
            if acc is None:
                stats = 'failed to fit'
            else:
                stats = classifier.get_stats()
                stats['accuracy'] = acc
        else:
            stats = 'timeout'
        return stats

    @staticmethod
    def save_results(results, file):
        json_obj = defaultdict(dict)
        for i in range(len(results.column_names)):
            for j in range(len(results.row_names)):
                json_obj[results.column_names[i]][results.row_names[j]] = results.table[j][i]
        with open(file, 'w+') as outfile:
            json.dump(json_obj, outfile, indent=4)

    @staticmethod
    def load_results(file):
        if not exists(file) or not isfile(file): return {}
        with open(file, 'r') as infile:
            return json.load(infile)

    @staticmethod
    def delete_dataset_results(dataset_name, file='benchmark.json'):
        results = BenchmarkSuite.load_results(file)
        for classifier in results:
            datasets = results[classifier]
            if dataset_name in datasets:
                del datasets[dataset_name]
        with open(file, 'w+') as outfile:
            json.dump(results, outfile, indent=4)

    @staticmethod
    def delete_classifier_results(classifier_name, file='benchmark.json'):
        results = Dataset.load_results(file)
        if classifier_name in results:
            del results[classifier_name]
        with open(file, 'w+') as outfile:
            json.dump(results, outfile, indent=4)
