import glob
import json
from collections import defaultdict
from os.path import join, exists, isfile

from dataset.multi_output_dataset import MultiOutputDataset
from dataset.single_output_dataset import SingleOutputDataset
from timeout import call_with_timeout
from util import format_seconds
from util import get_filename_and_ext

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
        classifier.fit(dataset) trains the classifier on the given dataset
        classifier.predict(dataset) returns an array of the classifiers predictions for the dataset
        classifier.get_stats() returns a dictionary of statistics to be displayed (e.g. the number of nodes in the tree)
        classifier.is_applicable(dataset) returns whether the classifier can be applied to the dataset
    """

    def __init__(self, timeout=100):
        self.datasets = []
        self.timeout = timeout

    def add_datasets(self, path, exclude=None, multiout=None):
        if not exclude:
            exclude = []
        if not multiout:
            multiout = []
        self.datasets = []
        for file in self.get_files(path):
            name, _ = get_filename_and_ext(file)
            if name not in exclude:
                if name in multiout:
                    ds = MultiOutputDataset(file)
                else:
                    ds = SingleOutputDataset(file)
                self.datasets.append(ds)
        self.datasets.sort(key=lambda ds: ds.name)

    def get_files(self, path):
        return [f'{file.split("_X.")[0]}.vector' for file in glob.glob(join(path, '*.pickle'))]  # TODO

    def benchmark(self, classifiers, file='benchmark.json', save_location='decision_trees'):
        prev_results = self.load_results(file)
        num_steps = self.count_num_steps(classifiers, prev_results)
        if num_steps > 0:
            print('Maximum wait time: {}.'.format(format_seconds(num_steps * self.timeout)))
        table = []
        step = 0
        for ds in self.datasets:
            row = []
            for classifier in classifiers:
                cell, computed, time = self.compute_cell(ds, classifier, prev_results, save_location)
                row.append(cell)
                if computed:
                    step += 1
                    msg = '{}/{}: Evaluated {} on {} in {}'.format(step, num_steps, classifier.name, ds.name,
                                                                   format_seconds(time))
                    if cell == 'timeout':
                        msg += ' (Timeout)'
                    print('{}.'.format(msg))
            table.append(row)
        print('Done.')
        results = BenchmarkResults([ds.name for ds in self.datasets], [c.name for c in classifiers], table)
        self.save_results(results, file)
        return results

    def count_num_steps(self, classifiers, prev_results):
        num_steps = 0
        for ds in self.datasets:
            for classifier in classifiers:
                if not self.already_computed(ds, classifier, prev_results) and \
                        classifier.is_applicable(ds):
                    num_steps += 1
        return num_steps

    def compute_cell(self, dataset, classifier, prev_results, save_location):
        time = None
        if self.already_computed(dataset, classifier, prev_results):
            computed = False
            cell = prev_results[classifier.name][dataset.name]
        elif not classifier.is_applicable(dataset):
            computed = False
            cell = 'not applicable'
        else:
            computed = True
            dataset.load_if_necessary()
            cell, time = self.train_and_get_cell(dataset, classifier, save_location)
        return cell, computed, time

    @staticmethod
    def already_computed(dataset, classifier, prev_results):
        return classifier.name in prev_results and dataset.name in prev_results[classifier.name]

    def train_and_get_cell(self, dataset, classifier, save_location):
        classifier, success, time = call_with_timeout(classifier, 'fit', dataset, timeout=self.timeout)
        classifier.save(save_location)
        if success:
            acc = dataset.compute_accuracy(classifier.predict(dataset))
            if acc is None:
                cell = 'failed to fit'
            else:
                cell = {'stats': classifier.get_stats()}
                if abs(acc - 1.0) > 1e-10:
                    cell['accuracy'] = acc
        else:
            cell = 'timeout'
        return cell, time

    @staticmethod
    def save_results(results, file):
        json_obj = defaultdict(dict)
        for i in range(len(results.column_names)):
            for j in range(len(results.row_names)):
                json_obj[results.column_names[i]][results.row_names[j]] = results.table[j][i]
        with open(file, 'w+') as outfile:
            json.dump(json_obj, outfile, indent=2)

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
            json.dump(results, outfile, indent=2)

    @staticmethod
    def delete_classifier_results(classifier_name, file='benchmark.json'):
        results = BenchmarkSuite.load_results(file)
        if classifier_name in results:
            del results[classifier_name]
        with open(file, 'w+') as outfile:
            json.dump(results, outfile, indent=2)
