import sys
import os
import time
import dtcontrol
import logging
from os.path import exists
import numpy as np
import subprocess
import pkg_resources
from typing import Tuple, Union
from pkg_resources import Requirement, resource_filename
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from jinja2 import FileSystemLoader, Environment
from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset
from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.frontend_helper import get_classifier, is_valid_file_or_folder, load_default_config, get_preset
from collections import namedtuple, OrderedDict

file_loader = FileSystemLoader([path + "/c_templates" for path in dtcontrol.__path__])
env = Environment(loader=file_loader)
single_output_c_template = env.get_template('single_output.c')
multi_output_c_template = env.get_template('multi_output.c')

def save_dot_c_json(classifier, dataset):
    dot_filename = 'dot.dot'
    with open(dot_filename, 'w+') as outfile:
        outfile.write(classifier.print_dot(dataset.x_metadata, dataset.y_metadata))
    num_outputs = 1 if len(dataset.y.shape) <= 2 else len(dataset.y)
    template = multi_output_c_template if num_outputs > 1 else single_output_c_template
    example = f'{{{",".join(str(i) + (".f" if isinstance(i, np.integer) else "f") for i in dataset.x[0])}}}'
    c_filename = 'c.c'
    with open(c_filename, 'w+') as outfile:
        outfile.write(
            template.render(num_inputs=dataset.x.shape[1], num_outputs=num_outputs, code=classifier.print_c()))
    json_filename = 'json.json'
    with open(json_filename, 'w+') as outfile:
        outfile.write(classifier.toJSON(dataset.x_metadata, dataset.y_metadata))

#file = "examples/cps/vehicle.scs"
file = input("Enter the path of the file: ")
if not exists(file):
    print(f"The file/folder {file} does not exist.")
    sys.exit(1)
ext = file.split(".")[-1]
if BenchmarkSuite.is_multiout(file, ext):
    ds = MultiOutputDataset(file)
else:
    ds = SingleOutputDataset(file)

ds.is_deterministic = BenchmarkSuite.is_deterministic(file, ext)
ds.load_if_necessary()

default_config: OrderedDict = load_default_config()
user_config: Union[None, OrderedDict] = None

fallback_numeric, fallback_categorical = None, None
user_predicates = None
presets = input("Enter the name of the preset: ")
numeric_split, categorical_split, determinize, impurity, tolerance, safe_pruning = get_preset(presets, user_config, default_config)
classifier = None
try:
    classifier = get_classifier(numeric_split, categorical_split, determinize, impurity,
                                    tolerance=tolerance,
                                    safe_pruning=safe_pruning, name=presets, user_predicates=user_predicates,
                                    fallback=(fallback_numeric, fallback_categorical))
except EnvironmentError:
        logging.warning(f"WARNING: Could not instantiate a classifier for preset '{presets}'. This could be "
                        f"because the preset '{presets}' is not supported on this platform. Skipping...\n")
except Exception:
        logging.warning(f"WARNING: Could not instantiate a classifier for preset '{presets}'. Skipping...\n")
if not classifier:
    logging.warning(
            "No valid preset selected. Please try again with the correct preset name. Use 'dtcontrol preset --list' to see valid presets.")
    sys.exit("Exiting...")

start = time.time()
print("Fitting dataset to tree...")
classifier.fit(ds)
run_time = time.time() - start
print(f"Tree constructed in {run_time}s")

print("Saving to c, dot and json files")
save_dot_c_json(classifier, ds)
subprocess.call(["gcc", "c.c"])
pred = classifier.predict(ds, actual_values=True)

for i, state in enumerate(ds.x):
    result = subprocess.check_output(["./a.out"] + list(map(str, state)))
    if BenchmarkSuite.is_multiout(file, ext):
        s = np.float32(result.decode().split(','))
        c_output = tuple(s)
        if all(isinstance(item, tuple) for item in pred[i]):
            if c_output not in pred[i]:
                print("Absent")
                print(list(state), pred[i])
                print(c_output)
        elif isinstance(pred[i], tuple):
            if not np.isclose(np.asarray(pred[i]), np.asarray(c_output)).all():
                        # if c_output != pred[i]:
                print("Absent")
                print(list(state), pred[i])
                print(c_output)
        else:
            print("Error")
    else:
        c_output = np.float32(result.decode())
        if isinstance(pred[i], list):
            if c_output not in pred[i]:
                print(list(state), pred[i])
                print("Absent")
        elif isinstance(pred[i], np.float32):
            if c_output != pred[i]:
                print(list(state), pred[i])
                print("Absent")
        else:
            print("Error")