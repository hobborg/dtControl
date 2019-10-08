import glob
import json
import os
import time
import webbrowser
from collections import defaultdict
from os import makedirs
from os.path import join, exists, isfile

from IPython.display import HTML, display
from dataset.multi_output_dataset import MultiOutputDataset
from dataset.single_output_dataset import SingleOutputDataset
from timeout import call_with_timeout
from ui.table_controller import TableController
from util import format_seconds, get_filename_and_ext

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
        classifier.save(file) saves the classifier to a file (for debugging purposes only)
        classifier.export_dot(file) saves a dot-representation of the classifier to a file
        classifier.export_c(file) saves a C-representation of the classifier to a file
    """

    def __init__(self, benchmark_file='benchmark', timeout=100, output_folder='decision_trees', save_folder=None):
        self.datasets = []
        self.benchmark_json = f'{benchmark_file}.json'
        self.benchmark_html = f'{benchmark_file}.html'
        self.prev_results = {}
        self.timeout = timeout
        self.output_folder = output_folder
        self.save_folder = save_folder
        self.table_controller = TableController(self.benchmark_html, self.output_folder)

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

    def display_html(self):
        display(HTML(f'<html><a href="{self.benchmark_html}" target="_blank">View table</a></html>'))
        url = f'file://{os.path.abspath(self.benchmark_html)}'
        webbrowser.open(url)

    def benchmark(self, classifiers):
        self.load_results()
        num_steps = self.count_num_steps(classifiers)
        if num_steps > 0:
            print('Maximum wait time: {}.'.format(format_seconds(num_steps * self.timeout)))
        table = []
        step = 0
        for ds in self.datasets:
            row = []
            for classifier in classifiers:
                cell, computed, time = self.compute_cell(ds, classifier)
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
        self.save_results(results)
        self.table_controller.update_and_save(results)

    def count_num_steps(self, classifiers):
        num_steps = 0
        for ds in self.datasets:
            for classifier in classifiers:
                if not self.already_computed(ds, classifier) and \
                        classifier.is_applicable(ds):
                    num_steps += 1
        return num_steps

    def compute_cell(self, dataset, classifier):
        time = None
        if self.already_computed(dataset, classifier):
            computed = False
            cell = self.prev_results[classifier.name][dataset.name]
        elif not classifier.is_applicable(dataset):
            computed = False
            cell = 'not applicable'
        else:
            computed = True
            dataset.load_if_necessary()
            cell, time = self.train_and_get_cell(dataset, classifier)
        return cell, computed, time

    def already_computed(self, dataset, classifier):
        return classifier.name in self.prev_results and dataset.name in self.prev_results[classifier.name]

    def train_and_get_cell(self, dataset, classifier):
        classifier, success, time = call_with_timeout(classifier, 'fit', dataset, timeout=self.timeout)
        if success:
            acc = dataset.compute_accuracy(classifier.predict(dataset))
            if acc is None:
                cell = 'failed to fit'
            else:
                cell = {'stats': classifier.get_stats()}
                dot_filename = self.get_filename(self.output_folder, dataset, classifier, '.dot')
                classifier.export_dot(dot_filename)
                c_filename = self.get_filename(self.output_folder, dataset, classifier, '.c')
                classifier.export_c(c_filename)
                if abs(acc - 1.0) > 1e-10:
                    cell['accuracy'] = acc
                if self.save_folder is not None:
                    classifier.save(self.get_filename(self.save_folder, dataset, classifier, '.saved', unique=True))
        else:
            cell = 'timeout'
        return cell, time

    def get_filename(self, folder, dataset, classifier, extension, unique=False):
        dir = join(folder, classifier.name, dataset.name)
        if not exists(dir):
            makedirs(dir)
        name = classifier.name
        if unique:
            name += f'--{time.strftime("%Y%m%d-%H%M%S")}'
        name += extension
        return join(dir, name)

    def save_results(self, results):
        json_obj = defaultdict(dict)
        for i in range(len(results.column_names)):
            for j in range(len(results.row_names)):
                json_obj[results.column_names[i]][results.row_names[j]] = results.table[j][i]
        self.prev_results = json_obj
        with open(self.benchmark_json, 'w+') as outfile:
            json.dump(json_obj, outfile, indent=2)

    def load_results(self):
        if not exists(self.benchmark_json) or not isfile(self.benchmark_json): return
        with open(self.benchmark_json, 'r') as infile:
            self.prev_results = json.load(infile)

    def delete_dataset_results(self, dataset_name):
        self.load_results()
        for classifier in self.prev_results:
            datasets = self.prev_results[classifier]
            if dataset_name in datasets:
                del datasets[dataset_name]
        with open(self.benchmark_json, 'w+') as outfile:
            json.dump(self.prev_results, outfile, indent=2)

    def delete_classifier_results(self, classifier_name):
        if classifier_name in self.prev_results:
            del self.prev_results[classifier_name]
        with open(self.benchmark_json, 'w+') as outfile:
            json.dump(self.prev_results, outfile, indent=2)
