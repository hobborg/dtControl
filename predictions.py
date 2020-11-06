import sys
import time
import dtcontrol
import numpy as np
from os.path import exists

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
        outfile.write(template.render(example=example, num_outputs=num_outputs, code=classifier.print_c()))

    json_filename = 'json.json'
    with open(json_filename, 'w+') as outfile:
        outfile.write(classifier.toJSON(dataset.x_metadata, dataset.y_metadata))

# file = "examples/cps/10rooms.scs"
file = "examples/cps/cartpole.scs"
if not exists(file):
    print(f"The file/folder {file} does not exist.")
    sys.exit(1)

ext = file.split(".")[-1]
if BenchmarkSuite.is_multiout(file, ext):
    ds = MultiOutputDataset(file)
else:
    ds = SingleOutputDataset(file)

ds.is_deterministic = BenchmarkSuite.is_deterministic(file, ext)
# Load the dataset
ds.load_if_necessary()

# Get the classifier object
classifier = get_classifier(['axisonly'], ['multisplit'], "auto", "multilabelentropy", tolerance=1e-5, safe_pruning=False,
                   name="mlentropy", user_predicates=None, fallback=None)

start = time.time()

print("Fitting dataset to tree...")
# Train the classifier
classifier.fit(ds)
run_time = time.time() - start
print(f"Tree constructed in {run_time}s")

print("Saving to c, dot and json files")
save_dot_c_json(classifier, ds)

# Compile C output

# For each state, give it to the C output and get response and compare it with response of classifier.predict

# This generates a list of predictions for every input in the dataset
pred = classifier.predict(ds, actual_values=True)
for i, state in enumerate(ds.x):
    # This prints the state and allowed actions for every input in the dataset (ds.x is the domain of the controller)
    print(list(state), pred[i])

# A sample list of state action pairs (first two elements of every
# list signifies the state and the last signifies a single action)
# For multi-output datasets, the action will be a tuple (a_1, a_2)
# and hence the code will have to be adapted
simulations = [[3.44, 0.6, -3.7]
    ,[3.44, -0.3, 3.3]
    ,[3.52, 0.7, -3.7]
    ,[3.6, -0.1, -3.7]
    ,[3.44, -1.0, 3.3]
    ,[3.28, 0.0, -3.7]
    ,[3.12, -1.1, 3.3]
    ,[2.96, -0.1, -3.7]
    ,[2.8, -1.2, 3.3]
    ,[2.48, -0.5, 3.3]
    ,[2.48, 0.1, 0.0]
    ,[2.48, -0.1, 3.9]
    ,[2.48, 0.6, 0.0]
    ,[2.64, 0.4, 0.0]
    ,[2.8, 0.3, -3.7]
    ,[2.72, -0.8, 3.3]
    ,[2.56, -0.1, 3.9]
    ,[2.72, 0.8, -3.7]
    ,[2.72, -0.4, 3.3]
    ,[2.72, 0.4, -3.7]
    ,[2.72, -0.7, 3.3]
    ,[2.56, 0.0, 3.9]
    ,[2.72, 0.9, -3.7]
    ,[2.8, -0.3, 3.3]
    ,[2.88, 0.5, -3.7]
    ,[2.8, -0.6, 3.3]
    ,[2.8, 0.2, -3.7]
    ,[2.64, -0.9, 3.3]
    ,[2.48, -0.2, 3.3]
    ,[2.56, 0.4, 0.0]
    ,[2.64, 0.2, 0.0]
    ,[2.64, 0.1, 0.0]
    ,[2.64, -0.1, 3.9]
    ,[2.72, 0.8, -3.7]
    ,[2.8, -0.3, 3.3]
    ,[2.88, 0.5, -3.7]
    ,[2.8, -0.6, 3.3]
    ,[2.8, 0.2, -3.7]
    ,[2.64, -1.0, 3.3]
    ,[2.48, -0.3, 3.3]
    ,[2.48, 0.3, 0.0]
    ,[2.48, 0.1, 0.0]
    ,[2.48, -0.1, 3.9]
    ,[2.56, 0.7, 0.0]
    ,[2.8, 0.5, -3.7]
    ,[2.8, -0.6, 3.3]
    ,[2.72, 0.2, -3.7]
    ,[2.56, -0.9, 3.3]
    ,[2.4, -0.4, 3.3]
    ,[2.32, 0.1, 0.0]
    ,[2.4, -0.1, 3.9]
    ,[2.4, 0.6, 0.0]
    ,[2.56, 0.4, 0.0]
    ,[2.64, 0.2, 0.0]
    ,[2.72, 0.1, -3.7]
    ,[2.56, -1.0, 3.3]
    ,[2.4, -0.4, 3.3]
    ,[2.32, 0.1, 0.0]
    ,[2.32, -0.1, 3.9]
    ,[2.4, 0.5, 0.0]
    ,[2.48, 0.3, 0.0]
    ,[2.56, 0.1, 0.0]
    ,[2.56, -0.1, 3.9]
    ,[2.64, 0.8, 0.0]
    ,[2.88, 0.7, -3.7]
    ,[2.88, -0.5, 3.3]
    ,[2.88, 0.4, -3.7]
    ,[2.8, -0.8, 3.3]
    ,[2.72, 0.0, -3.7]
    ,[2.56, -1.1, 3.3]
    ,[2.32, -0.5, 3.3]
    ,[2.24, -0.2, 3.3]]

# Checking if the states in the above list match
# are contained in the domain of the controller
# TODO Vardhah: This is not the task which you want to do though
for s in simulations:
    flag = 0
    for i in range(ds.x.shape[0]):
        if s[0] == float(ds.x[i][0]) and s[1] == float(ds.x[i][1]):
            flag = 1
    if flag == 0:
        print("no match")
    else:
        print("match")