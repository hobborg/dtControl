import os
import webbrowser
import yaml
import json
import numpy as np
from flask import Flask, render_template, url_for, json, request, Response, jsonify, request
from dtcontrol import frontFns
import sympy as sp

app = Flask(__name__)

# tree generated by dtControl is saved and used again for predictions
saved_tree = []

# list of lower and upper bounds for each of the state variables
minBounds = []
maxBounds = []

# step size (used in discretisation) for each of the state variables
stepSize = []

# contains (variable_name, value) pairs obtained from dynamics.txt file present in examples folder
variable_subs = []

# contains lambda functions generated from dynamics.txt file
lambda_list = []

# number of state variables (x's)
numVars = 0

# number of decision variables (u's)
numResults = 0

# time discretisation parameter
tau = 0

# Saved domain knowledge predicates
pred = []


def runge_kutta(x, u, nint=10):
    # nint is number of times to run Runga-Kutta loop
    global tau, lambda_list
    h = tau / nint

    k0 = [None] * len(x)
    k1 = [None] * len(x)
    k2 = [None] * len(x)
    k3 = [None] * len(x)

    for iter in range(1, nint + 1):
        for i in range(len(x)):
            k0[i] = h * computation(i, x, u, list(lambda_list))
        for i in range(len(x)):
            k1[i] = h * computation(i, [(x[j] + 0.5 * k0[j]) for j in range(len(x))], u, list(lambda_list))
        for i in range(len(x)):
            k2[i] = h * computation(i, [(x[j] + 0.5 * k1[j]) for j in range(len(x))], u, list(lambda_list))
        for i in range(len(x)):
            k3[i] = h * computation(i, [(x[j] + k2[j]) for j in range(len(x))], u, list(lambda_list))
        for i in range(len(x)):
            x[i] = x[i] + (1.0 / 6.0) * (k0[i] + 2 * k1[i] + 2 * k2[i] + k3[i])
    return x


# returns computed value of lambda function every time Runga-Kutta needs it
def computation(index, x, u, ll):
    new_vl = []
    for name in ll[index][2]:
        spilt_of_var = (str(name)).split('_')
        if spilt_of_var[0] == 'x':
            new_vl.append(x[int(spilt_of_var[1])])
        else:
            new_vl.append(u[int(spilt_of_var[1])])
    return_float = float(ll[index][1](*tuple(new_vl)))
    return return_float


# some errors when using Greatest integer function-like discretisation
def discretize(x):
    diff = []
    for i in range(numVars):
        lower = minBounds[i] + stepSize[i] * (int((x[i] - minBounds[i]) / stepSize[i]))
        upper = minBounds[i] + stepSize[i] * (1 + int((x[i] - minBounds[i]) / stepSize[i]))
        mid = (lower + upper) / 2
        if x[i] >= mid:
            diff.append(upper)
        else:
            diff.append(lower)
        # diff.append(minBounds[i] + stepSize[i] * (1 + int((x[i] - minBounds[i]) / stepSize[i])))
    return diff


# route when loading default simulator
@app.route("/simulator")
def simulator():
    return render_template("simulator.html")

@app.route("/experiment")
def experiment():
    return render_template("experiment.html")

# First call that receives controller and config and returns constructed tree
@app.route("/simRoute", methods=['POST'])
def simroute():
    global saved_tree, minBounds, maxBounds, stepSize, variable_subs, lambda_list, numVars, numResults, tau
    saved_tree = []
    minBounds = []
    maxBounds = []
    stepSize = []

    variable_subs = []
    lambda_list = []
    numVars = 0
    numResults = 0
    tau = 0

    data = request.get_json()
    cont = data['controller']
    config = data['config']
    to_parse_dict = {}
    if config == "custom":
        to_parse_dict = {"controller": cont, "determinize": data['determinize'],
                         "numeric-predicates": data['numeric_predicates'],
                         "categorical-predicates": data['categorical_predicates'], "impurity": data['impurity'],
                         "tolerance": data['tolerance'], "safe-pruning": data['safe_pruning']}
    else:
        to_parse_dict = {"controller": cont, "config": config}

    # main_parse takes in a dictionary and returns [constructed d-tree, x_metadata, y_metadata, root]
    classi = frontFns.main_parse(to_parse_dict)
    # root is saved in a global variable for use later
    saved_tree = classi[3]

    numVars = len(classi[1]["min"])
    numResults = len(classi[2]["variables"])
    minBounds = classi[1]["min"]
    maxBounds = classi[1]["max"]
    stepSize = classi[1]["step_size"]

    returnDict = {"classi": ([classi[0]]), "numVars": numVars, "numResults": numResults,
                  "bound": [minBounds, maxBounds]}
    return jsonify(returnDict)


# Gets user input values to initialise the state variables
@app.route("/initRoute", methods=['POST'])
def initroute():
    data = request.get_json()
    x = data['pass']

    # Predict_one_step returns the decision taken as well as the path (list of ints) to reach that decision
    initDecision = saved_tree.predict_one_step(np.array([discretize(x)]))
    returnDict = {"decision": initDecision[0], "path": initDecision[1], "dynamics": True}

    is_dynamics = False
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    dynamics_data_file = os.path.join(SITE_ROOT, '..', '..', 'examples/dynamics.txt')

    # Opens dynamics file and saves obtained variables and lambda functions as lists (variable_subs and lambda_list)
    try:
        with open(dynamics_data_file) as f:
            my_list = f.read().splitlines()
        for i in my_list:
            global variable_subs, lambda_list, tau
            i = i.strip()
            if i == 'Dynamics:':
                is_dynamics = True
            elif i == 'Parameters:':
                is_dynamics = False
            else:
                if i != '':
                    if not is_dynamics:
                        foo = i.split("=")
                        variable_subs.append((foo[0].strip(), float(foo[1])))
                        if foo[0].strip() == "tau" or foo[0].strip() == "Tau":
                            tau = float(foo[1])
                    else:
                        foo = i.split("=")
                        tmp = sp.sympify(foo[1].strip())
                        tmp = tmp.subs(variable_subs)
                        lam_1 = sp.lambdify(tmp.free_symbols, tmp)
                        lambda_list.append((foo[0].strip(), lam_1, tmp.free_symbols))
        lambda_list = sorted(lambda_list, key=lambda x: int(x[0].split("_")[1]))

    except:
        # If dynamic.txt is not present sets this to false and browser raises an exception
        returnDict["dynamics"] = False

    return jsonify(returnDict)


# Called on each step of the simulation
@app.route("/stepRoute", methods=['POST'])
def stepRoute():
    data = request.get_json()
    x = data['x_pass']
    u = data['u_pass']

    # Returns updated states variables
    x_new_non_classify = runge_kutta(list(x), u)
    newu_path = saved_tree.predict_one_step(np.array([discretize(list(x_new_non_classify))]))
    returnDict = {"x_new": (x_new_non_classify,) + newu_path}
    return jsonify(returnDict)


# Called when using the instep function
@app.route("/inStepRoute", methods=['POST'])
def inStepRoute():
    data = request.get_json()
    steps = data['steps']
    x = data['x_pass']
    u = data['u_pass']

    x_new = []
    dummy = [x, u, "", False]
    for i in range(int(steps)):
        x_new_non_classify = runge_kutta(list(dummy[0]), dummy[1])

        newu_path = saved_tree.predict_one_step(np.array([discretize(list(x_new_non_classify))]))
        dummy = (x_new_non_classify,) + newu_path
        x_new.append(dummy)

    returnDict = {"x_new": x_new}
    return jsonify(returnDict)


# Used to reconstruct from presets
@app.route("/reconstructRoute1")
def rc1():
    return []


# Used reconstruct from user text predicates
@app.route("/reconstructRoute2")
def rc2():
    return []


# Called when evaluating impurity of initially entered domain knowledge
@app.route("/evaluatePredicateImpurity", methods=['POST'])
def evalImpurityRoute():
    data = request.get_json()
    pred = data['predicate']

    returnDict = {"impurity": 0.5}
    return jsonify(returnDict)


# Called when trying to get feature and label specifications
@app.route("/featureLabelSpecifications", methods=['POST'])
def returnFeaturesLabels():
    data = request.get_json()
    global pred
    # Contains finally selected domain knowledge, preferably store in some global variable
    pred = data['domainKnowledge']

    dummy_feature_specifications = [['x_0', 'Ego.Choose', '1', '1', '1', '1', '1'],
                                    ['x_1', 'Front.Choose', '0', '0', '0', '0', '1']]
    dummy_label_specifications = [['accelerationEgo', '-2', '2', '2']]
    returnDict = {"feature_specifications": dummy_feature_specifications,
                  "label_specifications": dummy_label_specifications}
    return jsonify(returnDict)


# Called when trying to refresh impurities for different nodes
@app.route("/refreshImpurities", methods=['POST'])
def refreshImpurities():
    data = request.get_json()
    # Contains address of node trying to build
    address = data['address']

    dummy_domain_knowledge_updated_impurities = ['0.23'] * (len(pred))
    dummy_computed_predicates = [['12', '0.57', 'x_1 + x_2 <= 0'], ['13', '0.651', 'x_3 + 5.0 <= 0']]
    returnDict = {"updated_impurities": dummy_domain_knowledge_updated_impurities,
                  "computed_predicates": dummy_computed_predicates}
    return jsonify(returnDict)


# Returns number of splits for a node on selecting appropriate predicate
@app.route("/splitNode", methods=['POST'])
def splitNode():
    data = request.get_json()
    # Contains address of node trying to split and predicate
    address = data['address']
    pred = data['predicate']

    # Do processing here

    returnDict = {"number_splits": 3}
    return jsonify(returnDict)


# Used to get the list of unzipped examples
@app.route("/examples")
def showscs():
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    egs_path = os.path.join(SITE_ROOT, '..', '..', 'examples')
    valid_egs_list = []
    for file in os.scandir(egs_path):
        if file.name.endswith(".scs") and (not file.name.startswith(".")):
            valid_egs_list.append(file.name)
    return json.dumps(valid_egs_list)


# Used to read config.yml file
@app.route("/yml")
def yamlread():
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, '..', 'config.yml')
    data = yaml.load(open(json_url), Loader=yaml.FullLoader)
    return json.dumps(data)


def runFlask():
    print('##########Opening browser##########')
    # Decomment this and add valid application path if you don't want to open in default browser
    # chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
    # webbrowser.get(chrome_path).open('http://127.0.0.1:5000/')
    try:
        webbrowser.open('http://127.0.0.1:5000/')
    except:
        print('Visit http://127.0.0.1:5000/')
    app.run(debug=False)


if __name__ == "__main__":
    runFlask()
