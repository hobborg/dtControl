import glob
import json
import logging
import os
import sys
import time
import webbrowser
from os import makedirs
from os.path import join, exists, isfile

import numpy as np
from jinja2 import FileSystemLoader, Environment
import json

import dtcontrol
from dtcontrol import util
from dtcontrol.bdd import BDD
from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset
from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.timeout import call_with_timeout
from dtcontrol.ui.table_controller import TableController
from dtcontrol.util import format_seconds, get_filename_and_relevant_extension

file_loader = FileSystemLoader([path + "/c_templates" for path in dtcontrol.__path__])
env = Environment(loader=file_loader)
single_output_c_template = env.get_template('single_output.c')
multi_output_c_template = env.get_template('multi_output.c')

util.ignore_convergence_warnings()


class BenchmarkSuite:
    """
    The benchmark suite runs the given classifiers on the given datasets and saves the results.
    """

    def __init__(self, benchmark_file='benchmark', timeout=None, output_folder='decision_trees', output_type=None, save_folder=None,
                 stdout=False, rerun=False, is_artifact=False):
        logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
        self.datasets = []
        self.json_file = f'{benchmark_file}.json'
        self.html_file = f'{benchmark_file}.html'
        self.results = {}
        self.timeout = timeout
        self.output_folder = output_folder
        self.output_type = output_type
        self.save_folder = save_folder
        self.stdout = stdout
        self.rerun = rerun  # rerun benchmarks even if there already are results available
        self.is_artifact = is_artifact  # always produces a table exactly corresponding to the one in the paper
        self.table_controller = TableController(self.html_file, self.output_folder, self.is_artifact)

        logging.info(f"INFO: Benchmark statistics will be available in {self.json_file} and {self.html_file}.")
        if not self.stdout:
            logging.info(f"INFO: Constructed trees will be written to {self.output_folder}.\n")
        else:
            logging.info(f"INFO: Constructed trees will be written to stdout.\n")
    def add_datasets(self, paths, include=None, exclude=None):
        if not exclude:
            exclude = []
        if include is not None and len(set(include) & set(exclude)) > 0:
            logging.error('A dataset cannot be both included and excluded.\nAborting.')
            return
        self.datasets = []
        if isinstance(paths, str):
            paths = [paths]
        for path in paths:
            for file in self.get_files(path):
                name, ext = get_filename_and_relevant_extension(file)
                if ((not include) or name in include) and name not in exclude:
                    if self.is_multiout(file, ext):
                        ds = MultiOutputDataset(file)
                    else:
                        ds = SingleOutputDataset(file)

                    ds.is_deterministic = self.is_deterministic(file, ext)
                    self.datasets.append(ds)
        self.datasets.sort(key=lambda ds: ds.get_name())

    @staticmethod
    def get_files(path):
        if isfile(path):
            return [path]
        else:
            return [p for ext in ['*.scs', '*.dump', '*.csv', '*.prism', '*.storm.json'] for p in glob.glob(join(path, ext))
                    if not p.endswith('_states.prism')]

    def display_html(self):
        url = f'file://{os.path.abspath(self.html_file)}'
        webbrowser.open(url)

    def benchmark(self, classifiers):
        self.load_results()
        num_steps = len(classifiers) * len(self.datasets)
        step = 0
        for ds in self.datasets:
            for classifier in classifiers:
                step += 1
                logging.info(f"{step}/{num_steps}: Evaluating {classifier.get_name()} on {ds.get_name()}... ")
                try:
                    cell, computed = self.compute_cell(ds, classifier)
                except ValueError as e:
                    # traceback.print_exc()
                    logging.error(e)
                    continue
                if computed:
                    self.save_result(classifier.get_name(), ds, cell)
                    if cell == 'timeout':
                        msg = f"{step}/{num_steps}: Timed out after {format_seconds(self.timeout)}"
                    elif cell == 'failed to fit':
                        msg = f"{step}/{num_steps}: Failed to fit"
                    else:
                        msg = f"{step}/{num_steps}: Finished in {cell['time']}."
                    logging.info(msg)
                else:
                    if cell == 'not applicable':
                        self.save_result(classifier.get_name(), ds, cell)
                        logging.info(
                            f"{step}/{num_steps}: Not applicable.")
                    else:
                        logging.info(
                            f"{step}/{num_steps}: Not running since the result is already available.")
        logging.info('All benchmarks completed. Shutting down dtControl.')

        self.table_controller.update_and_save(self.results, [ds.get_name() for ds in self.datasets],
                                              [cl.get_name() for cl in classifiers])

    def compute_cell(self, dataset, classifier):
        if self.already_computed(dataset, classifier) and not self.rerun:
            computed = False
            cell = self.results[dataset.get_name()]['classifiers'][classifier.get_name()]
        elif not classifier.is_applicable(dataset):
            computed = False
            dataset.load_if_necessary()
            cell = 'not applicable'
        else:
            computed = True
            dataset.load_if_necessary()
            cell = self.train_and_get_cell(dataset, classifier)
        return cell, computed

    def already_computed(self, dataset, classifier):
        return dataset.get_name() in self.results and classifier.get_name() in self.results[dataset.get_name()][
            'classifiers']

    def train_and_get_cell(self, dataset, classifier):
        if self.timeout is not None:
            classifier, success, run_time = call_with_timeout(classifier, 'fit', dataset, timeout=self.timeout)
        else:
            start = time.time()
            classifier.fit(dataset)
            run_time = time.time() - start
            success = True
        if success:
            accuracy_start = time.time()
            if isinstance(classifier, BDD):
                acc = 1.0  # TODO: make BDD checking code work with multi-output datasets
            else:
                acc = dataset.compute_accuracy(classifier.predict(dataset, actual_values=False))
            if acc is None:
                cell = 'failed to fit'
            else:
                stats = classifier.get_stats()
                cell = {'stats': stats, 'time': format_seconds(run_time)}
                self.save_dot_c_json(classifier, dataset)
                # if not isinstance(classifier, OC1Wrapper):
                #     vhdl_filename = self.get_filename(self.output_folder, dataset, classifier, '.vhdl')
                #     classifier.print_vhdl(len(dataset.x_metadata["variables"]), vhdl_filename)
                if abs(acc - 1.0) > 1e-10:
                    cell['accuracy'] = acc
                if self.save_folder is not None:
                    classifier.save(self.get_filename(self.save_folder, dataset, classifier, '.saved', unique=True))

            accuracy_time = time.time() - accuracy_start
            # complete_time = time.time() - start
            logging.debug("Decision tree was built in {} seconds.".format(round(run_time, ndigits=3)))
            logging.debug("Accuracy was computed in {} seconds.".format(round(accuracy_time, ndigits=3)))
            logging.debug("dtControl finished in {} seconds.".format(round(run_time + accuracy_time, ndigits=3)))
        else:
            cell = 'timeout'
        return cell

    def save_dot_c_json(self, classifier, dataset):
        # TODO: as seen with the BDDs, this should probably be abstracted. For instance, the classifier itself could
        # provide a list of file formats that it can print to and the benchmark suite would then simply call the
        # corresponding methods

        if isinstance(classifier, BDD):
            return

        if self.stdout:
            logging.info(f"INFO: Writing {self.output_type} code into stdout.\n")
            print("START")
            if self.output_type == 'c':
                num_outputs = 1 if len(dataset.y.shape) <= 2 else len(dataset.y)
                template = multi_output_c_template if num_outputs > 1 else single_output_c_template
                example = f'{{{",".join(str(i) + (".f" if isinstance(i, np.integer) else "f") for i in dataset.x[0])}}}'
                print(template.render(example=example, num_outputs=num_outputs, code=classifier.print_c()))
            elif self.output_type == 'dot':
                print(classifier.print_dot(dataset.x_metadata, dataset.y_metadata))
            elif self.output_type == 'json':
                print(classifier.toJSON(dataset.x_metadata, dataset.y_metadata))
            print("END")
            return

        logging.info(f"INFO: Writing DOT file into {self.output_folder}.\n")
        dot_filename = self.get_filename(self.output_folder, dataset, classifier, '.dot')
        with open(dot_filename, 'w+') as outfile:
            outfile.write(classifier.print_dot(dataset.x_metadata, dataset.y_metadata))

        logging.info(f"INFO: Writing C file into {self.output_folder}.\n")
        num_outputs = 1 if len(dataset.y.shape) <= 2 else len(dataset.y)
        template = multi_output_c_template if num_outputs > 1 else single_output_c_template
        example = f'{{{",".join(str(i) + (".f" if isinstance(i, np.integer) else "f") for i in dataset.x[0])}}}'
        c_filename = self.get_filename(self.output_folder, dataset, classifier, '.c')
        with open(c_filename, 'w+') as outfile:
            outfile.write(template.render(example=example, num_outputs=num_outputs, code=classifier.print_c()))

        json_filename = self.get_filename(self.output_folder, dataset, classifier, '.json')
        with open(json_filename, 'w+') as outfile:
            outfile.write(classifier.toJSON(dataset.x_metadata, dataset.y_metadata))

    @staticmethod
    def get_filename(folder, dataset, classifier, extension, unique=False):
        dir = join(folder, classifier.get_name(), dataset.get_name())
        if not exists(dir):
            makedirs(dir)
        name = classifier.get_name()
        if unique:
            name += f'--{time.strftime("%Y%m%d-%H%M%S")}'
        name += extension
        return join(dir, name)

    def save_result(self, classifier_name, dataset, result):
        if dataset.get_name() not in self.results:
            self.results[dataset.get_name()] = {'classifiers': {},
                                                'metadata': {
                                                    'X_metadata': dataset.x_metadata,
                                                    'Y_metadata': dataset.y_metadata
                                                }
                                                }
        self.results[dataset.get_name()]['classifiers'][classifier_name] = result
        self.save_to_disk()

    def load_results(self):
        if not self.json_file or not exists(self.json_file) or not isfile(self.json_file):
            return
        with open(self.json_file, 'r') as infile:
            self.results = json.load(infile)
        for ds in self.datasets:
            if ds.get_name() in self.results:
                ds.load_metadata_from_json(self.results[ds.get_name()])

    def delete_dataset_results(self, dataset_name):
        self.load_results()
        if dataset_name in self.results:
            del self.results[dataset_name]
        self.save_to_disk()

    def delete_classifier_results(self, classifier_name):
        self.load_results()
        for dataset in self.results:
            classifiers = self.results[dataset]['classifiers']
            if classifier_name in classifiers:
                del classifiers[classifier_name]
        self.save_to_disk()

    def delete_cell(self, dataset_name, classifier_name):
        self.load_results()
        if dataset_name in self.results:
            classifiers = self.results[dataset_name]['classifiers']
            if classifier_name in classifiers:
                del classifiers[classifier_name]
        self.save_to_disk()

    def save_to_disk(self):
        with open(self.json_file, 'w+') as outfile:
            json.dump(self.results, outfile, indent=2, default=util.convert)

    @staticmethod
    def is_multiout(filename, ext):
        if "scs" in ext:
            # if scs, then
            with open(filename) as f:
                # Read input dim from scs file
                for i in range(5):
                    f.readline()
                state_dim = int(f.readline())
                for i in range(12 + 3 * state_dim):
                    f.readline()
                input_dim = int(f.readline())
                return input_dim > 1
        elif "csv" in ext:
            with open(filename) as f:
                f.readline()
                _, input_dim = map(int, f.readline().split("BEGIN")[1].split())
                return input_dim > 1
        else:
            return False

    @staticmethod
    def is_deterministic(filename, ext):
        if "scs" in ext:
            with open(filename) as f:
                # Read input dim from scs file
                for i in range(5):
                    f.readline()
                state_dim = int(f.readline())
                for i in range(12 + 3 * state_dim):
                    f.readline()
                input_dim = int(f.readline())
                for i in range(12 + 3 * input_dim):
                    f.readline()
                non_det = int(f.readline().split(":")[1].split()[1])
                return non_det == 1
        elif "csv" in ext:
            with open(filename) as f:
                is_det = "NON-PERMISSIVE" in f.readline()
                return is_det
        elif "prism" in ext or "storm" in ext:
            return True  # PRISM is always deterministic (?)
        else:
            return False  # UPPAAL is always non-deterministic
