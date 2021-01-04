import sys
import time
import dtcontrol
from os.path import exists
import numpy as np
import subprocess
from jinja2 import FileSystemLoader, Environment
from dtcontrol.benchmark_suite import BenchmarkSuite
from dtcontrol.dataset.multi_output_dataset import MultiOutputDataset
from dtcontrol.dataset.single_output_dataset import SingleOutputDataset
from dtcontrol.frontend_helper import get_classifier

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


file = "examples/cps/vehicle.scs"
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
# classifier = get_classifier(['axisonly'], ['multisplit'], "auto", "multilabelentropy", tolerance=1e-5, safe_pruning=False,
# name="mlentropy", user_predicates=None, fallback=None)
classifier = get_classifier(['axisonly', 'linear-logreg'], ['multisplit'], "maxfreq", "entropy", tolerance=1e-5,
                            safe_pruning=False, name="maxfreqlc", user_predicates=None, fallback=None)
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
            if not np.isclose(np.asarray(pred[i]) , np.asarray(c_output)).all():
            #if c_output != pred[i]:
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
