import os
import webbrowser
import yaml
import json
import numpy as np
from flask import Flask, render_template, url_for, json, request, Response, jsonify, request
from dtcontrol import frontFns, cartClassify
import sympy as sp

app = Flask(__name__)
saved_tree = []
minBounds = []
maxBounds = []
stepSize = []

variable_subs = []
lambda_list = []
numVars = 0
numResults = 0
tau = 0


def runge_kutta(x, u, nint=10):
    # matches cartClassify exactly for nint set to 30
    global tau
    h = tau / nint
    # tau = 1 for 10 rooms

    k0 = [None] * len(x)
    k1 = [None] * len(x)
    k2 = [None] * len(x)
    k3 = [None] * len(x)

    for iter in range(1, nint + 1):
        for i in range(len(x)):
            k0[i] = h * computation(i, x, u, lambda_list)
        for i in range(len(x)):
            k1[i] = h * computation(i, [(x[j] + 0.5 * k0[j]) for j in range(len(x))], u, lambda_list)
        for i in range(len(x)):
            k2[i] = h * computation(i, [(x[j] + 0.5 * k1[j]) for j in range(len(x))], u, lambda_list)
        for i in range(len(x)):
            k3[i] = h * computation(i, [(x[j] + k2[j]) for j in range(len(x))], u, lambda_list)
        for i in range(len(x)):
            x[i] = x[i] + (1.0 / 6.0) * (k0[i] + 2 * k1[i] + 2 * k2[i] + k3[i])

    return x


def computation(index, x, u, ll):
    new_vl = []
    for name in ll[index][2]:
        spilt_of_var = (str(name)).split('_')
        if spilt_of_var[0] == 'x':
            new_vl.append(x[int(spilt_of_var[1])])
        else:
            new_vl.append(u[int(spilt_of_var[1])])
    return float(ll[index][1](*tuple(new_vl)))


def discretise(x):
    # Not in use right now
    diff = []
    for i in range(numVars):
        diff.append(minBounds[i] + stepSize[i] * (int((x[i] - minBounds[i]) / stepSize[i])))
    # return diff
    return x


@app.route("/")
def home():
    return render_template("simulator.html")


# First call that receives controller and config and returns constructed tree
@app.route("/simRoute", methods=['POST'])
def simroute():
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

    # is a dict
    classi = frontFns.main_parse(to_parse_dict)
    global saved_tree, minBounds, maxBounds, numVars, numResults, stepSize
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
    initDecision = saved_tree.predict_one_step(np.array([discretise(x)]))
    returnDict = {"decision": initDecision[0], "path": initDecision[1], "dynamics": True}

    is_dynamics = False
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    dynamics_data_file = os.path.join(SITE_ROOT, '..', '..', 'examples/dynamics.txt')

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
        returnDict["dynamics"] = False

    return jsonify(returnDict)


# Called on each step of the simulation
@app.route("/stepRoute", methods=['POST'])
def stepRoute():
    data = request.get_json()
    x = data['x_pass']
    u = data['u_pass']

    # x_new_non_classify = cartClassify.step(x, u)
    x_new_non_classify = runge_kutta(list(x), u)

    newu_path = saved_tree.predict_one_step(np.array([discretise(list(x_new_non_classify))]))
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

        # x_new_non_classify = cartClassify.step(dummy[0], dummy[1])
        x_new_non_classify = runge_kutta(list(dummy[0]), dummy[1])

        newu_path = saved_tree.predict_one_step(np.array([discretise(list(x_new_non_classify))]))
        dummy = (x_new_non_classify,) + newu_path
        x_new.append(dummy)

    returnDict = {"x_new": x_new}
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
    chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
    webbrowser.get(chrome_path).open('http://127.0.0.1:5000/')
    app.run(debug=False)


if __name__ == "__main__":
    runFlask()
