import glob
import json
import os
import time
import webbrowser
import sys
import logging
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

    def __init__(self, benchmark_file='benchmark', timeout=100, output_folder='decision_trees', save_folder=None, rerun=False):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
        self.datasets = []
        self.json_file = f'{benchmark_file}.json'
        self.html_file = f'{benchmark_file}.html'
        self.results = {}
        self.timeout = timeout
        self.output_folder = output_folder
        self.save_folder = save_folder
        self.rerun = rerun
        self.table_controller = TableController(self.html_file, self.output_folder)

        logging.info(f"Benchmark statistics will be available in {self.json_file} and {self.html_file}.")
        logging.info(f"Constructed trees will be written to {self.output_folder}.")

    def add_datasets(self, paths, include=None, exclude=None):
        if not exclude:
            exclude = []
        if include is not None and len(set(include) & set(exclude)) > 0:
            logging.error('A dataset cannot be both included and excluded.\nAborting.')
            return
        self.datasets = []
        for path in paths:
            for file in self.get_files(path):
                name, ext = get_filename_and_ext(file)
                if ((not include) or name in include) and name not in exclude:
                    if self.is_multiout(file, ext):
                        ds = MultiOutputDataset(file)
                    else:
                        ds = SingleOutputDataset(file)

                    # check if dataset is deterministic
                    ds.is_deterministic = self.is_deterministic(file, ext)
                    self.datasets.append(ds)
        self.datasets.sort(key=lambda ds: ds.name)

    def get_files(self, path):
        if isfile(path):
            return [path]
        else:
            return glob.glob(join(path, '*.scs')) + glob.glob(join(path, '*.dump')) + glob.glob(join(path, '*.vector'))

    def display_html(self):
        display(HTML(f'<html><a href="{self.html_file}" target="_blank">View table</a></html>'))
        url = f'file://{os.path.abspath(self.html_file)}'
        webbrowser.open(url)

    def benchmark(self, classifiers):
        self.load_results()
        num_steps = len(classifiers) * len(self.datasets)
        if num_steps > 0:
            logging.info('Maximum wait time: {}.'.format(format_seconds(num_steps * self.timeout)))
        table = []
        step = 0
        for ds in self.datasets:
            row = []
            for classifier in classifiers:
                step += 1
                logging.info(f"{step}/{num_steps}: Evaluating {classifier.name} on {ds.name}... ")
                cell, computed = self.compute_cell(ds, classifier)
                row.append(cell)
                if computed:
                    self.save_result(classifier.name, ds.name, cell)
                    if cell == 'timeout':
                        msg = f"{step}/{num_steps}: {classifier.name} on {ds.name} timed out after {format_seconds(self.timeout)}"
                    else:
                        msg = f"{step}/{num_steps}: Evaluated {classifier.name} on {ds.name} in {cell['time']}."
                    logging.info(msg)
                else:
                    if cell == 'not applicable':
                        logging.info(f"{step}/{num_steps}: {classifier.name} is not applicable for {ds.name}.")
                    else:
                        logging.info(f"{step}/{num_steps}: Not running {classifier.name} on {ds.name} as result available in {self.json_file}.")
            table.append(row)
        print('Done.')
        results = BenchmarkResults([ds.name for ds in self.datasets], [c.name for c in classifiers], table)
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
        if self.already_computed(dataset, classifier) and not self.rerun:
            computed = False
            cell = self.results[classifier.name][dataset.name]
        elif not classifier.is_applicable(dataset):
            computed = False
            cell = 'not applicable'
        else:
            computed = True
            dataset.load_if_necessary()
            cell = self.train_and_get_cell(dataset, classifier)
        return cell, computed

    def already_computed(self, dataset, classifier):
        return classifier.name in self.results and dataset.name in self.results[classifier.name]

    def train_and_get_cell(self, dataset, classifier):
        classifier, success, time = call_with_timeout(classifier, 'fit', dataset, timeout=self.timeout)
        if success:
            acc = dataset.compute_accuracy(classifier.predict(dataset))
            if acc is None:
                cell = 'failed to fit'
            else:
                cell = {'stats': classifier.get_stats(), 'time': format_seconds(time)}
                dot_filename = self.get_filename(self.output_folder, dataset, classifier, '.dot')
                classifier.export_dot(dot_filename)
                c_filename = self.get_filename(self.output_folder, dataset, classifier, '.c')
                classifier.export_c(c_filename)
                vhdl_filename = self.get_filename(self.output_folder, dataset, classifier, '.vhdl')
                classifier.export_vhdl(len(dataset.X_metadata["variables"]),vhdl_filename)
                if abs(acc - 1.0) > 1e-10:
                    cell['accuracy'] = acc
                if self.save_folder is not None:
                    classifier.save(self.get_filename(self.save_folder, dataset, classifier, '.saved', unique=True))
        else:
            cell = 'timeout'
        return cell

    @staticmethod
    def get_filename(folder, dataset, classifier, extension, unique=False):
        dir = join(folder, classifier.name, dataset.name)
        if not exists(dir):
            makedirs(dir)
        name = classifier.name
        if unique:
            name += f'--{time.strftime("%Y%m%d-%H%M%S")}'
        name += extension
        return join(dir, name)

    def save_result(self, classifier_name, dataset_name, result):
        if classifier_name not in self.results:
            self.results[classifier_name] = {}
        self.results[classifier_name][dataset_name] = result
        self.save_to_disk()

    def load_results(self):
        if not self.json_file or not exists(self.json_file) or not isfile(self.json_file): return
        with open(self.json_file, 'r') as infile:
            self.results = json.load(infile)

    def delete_dataset_results(self, dataset_name):
        self.load_results()
        for classifier in self.results:
            datasets = self.results[classifier]
            if dataset_name in datasets:
                del datasets[dataset_name]
        self.save_to_disk()

    def delete_classifier_results(self, classifier_name):
        self.load_results()
        if classifier_name in self.results:
            del self.results[classifier_name]
        self.save_to_disk()

    def delete_cell(self, dataset_name, classifier_name):
        self.load_results()
        if classifier_name in self.results:
            datasets = self.results[classifier_name]
            if dataset_name in datasets:
                del datasets[dataset_name]
        self.save_to_disk()

    def save_to_disk(self):
        with open(self.json_file, 'w+') as outfile:
            json.dump(self.results, outfile, indent=2)

    @staticmethod
    def is_multiout(filename, ext):
        if "scs" not in ext:
            return False
        # if scs, then
        f = open(filename)
        # Read input dim from scs file
        for i in range(5):
            f.readline()
        state_dim = int(f.readline())
        for i in range(12 + 3 * state_dim):
            f.readline()
        input_dim = int(f.readline())
        return input_dim > 1

    @staticmethod
    def is_deterministic(filename, ext):
        if "scs" not in ext:
            return False  # UPPAAL is always non-deterministic
        # if scs, then
        f = open(filename)
        # Read input dim from scs file
        for i in range(5):
            f.readline()
        state_dim = int(f.readline())
        for i in range(12+3 * state_dim):
            f.readline()
        input_dim = int(f.readline())
        for i in range(12+3*input_dim):
            f.readline()

        non_det = int(f.readline().split(":")[1].split()[1])
        return non_det == 1
