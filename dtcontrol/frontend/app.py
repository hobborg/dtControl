import json
import logging
import os
import html
from traceback import print_exc

import numpy as np
import sympy as sp
from flask import Flask, render_template, json, jsonify, request, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename

from dtcontrol import frontend_helper
from dtcontrol.frontend_helper import get_controller_data
from dtcontrol.util import interactive_queue
from dtcontrol.decision_tree.splitting.context_aware.predicate_parser import PredicateParser
from dtcontrol.decision_tree.splitting.context_aware.richer_domain_logger import RicherDomainLogger
from dtcontrol.decision_tree.splitting.context_aware.richer_domain_exceptions import RicherDomainPredicateParserException


UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'scs', 'dump', 'csv', 'json', 'prism'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

logging.basicConfig(format="%(threadName)s: %(message)s", level=logging.INFO)

# stored controllers: controllers[nice_name] contains controller_id, controller_name, controller_nice_name, num_states, state_action_pairs, var_types, num_vars, num_results, max_non_det
controllers = {}

# stored results: results[res_id] contains res_id, cont_id, controller, nice_name, preset, status, determinize, numeric_predicates, categorical predicates, impurity, tolerance, safe_pruning, user_predicates,
#  inner_nodes, leaf_nodes, construction_time
results = {}

# computed configurations from the benchmark view
completed_experiments = {}
selected_computation_id = None

# contains (variable_name, value) pairs obtained from dynamics.txt file present in examples folder
variable_subs = []

# contains lambda functions generated from dynamics.txt file
lambda_list = []

# number of decision variables (u's)
numResults = 0

# time discretisation parameter
tau = 0

# Saved domain knowledge predicates
pred = []

# conut controllers added so far to assign unique id to every new controller
global_cont_counter = 0
# count results added so far to assignunique id to every new result
global_res_counter = 0

def runge_kutta(x, u, nint=100):
    global selected_computation_id, tau, lambda_list
    selected_experiment = completed_experiments[selected_computation_id]

    lower_bound = selected_experiment["min_bounds_outer"]
    upper_bound = selected_experiment["max_bounds_outer"]

    h = tau / nint

    k0 = [None] * len(x)
    k1 = [None] * len(x)
    k2 = [None] * len(x)
    k3 = [None] * len(x)

    for iter in range(1, nint + 1):
        for i in range(len(x)):
            k0[i] = computation(i, x, u, list(lambda_list))
        for i in range(len(x)):
            k1[i] = computation(i, [(x[j] + h * 0.5 * k0[j]) for j in range(len(x))], u, list(lambda_list))
        for i in range(len(x)):
            k2[i] = computation(i, [(x[j] + h * 0.5 * k1[j]) for j in range(len(x))], u, list(lambda_list))
        for i in range(len(x)):
            k3[i] = computation(i, [(x[j] + h * k2[j]) for j in range(len(x))], u, list(lambda_list))
        for i in range(len(x)):
            x[i] = x[i] + (h * 1.0 / 6.0) * (k0[i] + 2 * k1[i] + 2 * k2[i] + k3[i])
            x[i] = max(x[i], lower_bound[i])
            x[i] = min(x[i], upper_bound[i])
    return x


# returns computed value of lambda function every time Runga-Kutta needs it
def computation(ind, x, u, lambda_list):
    new_vl = []
    for name in lambda_list[ind][2]:
        spilt_of_var = (str(name)).split('_')
        if spilt_of_var[0] == 'x':
            new_vl.append(x[int(spilt_of_var[1])])
        else:
            new_vl.append(u[int(spilt_of_var[1])])
    # Apply lambda function
    return_float = float(lambda_list[ind][1](*tuple(new_vl)))
    return return_float


# some errors when using Greatest integer function-like discretisation
def discretize(x):
    diff = []

    # step size (used in discretisation) for each of the state variables
    step_size = completed_experiments[selected_computation_id]["step_size"]

    # iterate over each state variables (x's)
    num_vars = completed_experiments[selected_computation_id]["num_vars"]

    # list of lower and upper bounds for each of the state variables
    min_bounds_outer = completed_experiments[selected_computation_id]["min_bounds_outer"]

    for i in range(num_vars):
        # SCOTS picks the closest grid point
        # for xx in np.arange(min_bounds_outer[i], maxBounds[i]+step_size[i], step_size[i]):
        #     if round(xx, 6) > round(x[i], 6):  # TODO Fix this mess
        #         if xx - x[i] > x[i] - xx - step_size[i]:
        #             diff.append(xx - step_size[i])
        #         else:
        #             diff.append(xx)
        #         # print(x[i], xx, min_bounds_outer[i] + step_size[i] * (1 + int((x[i] - min_bounds_outer[i]) / step_size[i])),
        #         #       min_bounds_outer[i] + step_size[i] * math.ceil((x[i] - min_bounds_outer[i]) / step_size[i]))
        #         break

        # Reference: https://gitlab.lrz.de/matthias/SCOTSv0.2/-/blob/master/src/UniformGrid.hh#L234
        half_step_size = (step_size[i] / 2.0)
        diff.append((((x[i] - min_bounds_outer[i]) + half_step_size) // step_size[i]) * step_size[i] + min_bounds_outer[i])
    return diff


@app.route("/")
def index():
    return render_template("index.html")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'),
                               'favicon-32.png', mimetype='image/png')

@app.route('/controllers/initialize', methods=['POST'])
def initialize_controllers_route():
    controller_name = request.get_json()[0]
    controller_nice_name = request.get_json()[1]
    # duplicate check
    global controllers
    for controller in controllers:
        if controller == controller_nice_name:
            return jsonify(error="duplicate"), 500
    # use global_cont_counter to get a new id
    global global_cont_counter
    global_cont_counter += 1
    # initialize in controller table
    controllers[controller_nice_name] = [
        global_cont_counter,
        controller_name,
        controller_nice_name]
    return jsonify(global_cont_counter)

@app.route('/controllers', methods=['GET', 'POST'])
def controllers_route():
    global controllers
    if request.method == 'GET':
        return jsonify(controllers)
    # add controller to controller table/dict
    controller_id = request.get_json()[0]
    controller_name = request.get_json()[1]
    controller_nice_name = request.get_json()[2]
    assert controller_nice_name in controllers
    assert controllers[controller_nice_name] == request.get_json()
    cont = os.path.join(UPLOAD_FOLDER, controller_name)
    cont_dict = get_controller_data(cont)
    cont_data = [controller_id,
                controller_name,
                controller_nice_name,
                cont_dict["num_states"],
                cont_dict["state_action_pairs"],
                cont_dict["var_types"],
                cont_dict["num_vars"],
                cont_dict["num_results"],
                cont_dict["max_non_det"]]
    controllers[controller_nice_name] = cont_data
    return jsonify(cont_data)

@app.route('/controllers/delete', methods=['POST'])
def delete_controllers_route():
    global controllers
    controller_to_delete = request.get_json()
    nice_name = controller_to_delete[2]
   # turn the jsonified entries back to int
    for i in [0, 3, 4, 6, 7, 8]:
        controller_to_delete[i] = int(controller_to_delete[i])
    assert controllers[nice_name] == controller_to_delete
    del controllers[nice_name]
    return jsonify(success=True)

@app.route('/results/initialize', methods=['POST'])
def initialize_results_route():
    data = request.get_json()
    if data["config"] == "custom":
        numeric_split = data["numeric_predicates"]
        categorical_split = data["categorical_predicates"]
        determinize = data["determinize"]
        impurity = data["impurity"]
        tolerance = data["tolerance"]
        safe_pruning = data["safe_pruning"]
        user_predicates = data["user_predicates"]
    else:
        numeric_split, categorical_split, determinize, impurity, tolerance, safe_pruning = frontend_helper.get_preset(data["config"])
        user_predicates = None
    # TODO T: do we want a duplicate check?
    # use global_res_counter to get a new id
    global global_res_counter
    global_res_counter += 1
    # initialize in controller table
    config = {
        "res_id": global_res_counter,
        "cont_id": data["id"],
        "controller": data["controller"],
        "nice_name": data["nice_name"],
        "config": data["config"],
        "determinize": determinize,
        "numeric_predicates": numeric_split,
        "categorical_predicates": categorical_split,
        "impurity": impurity,
        "tolerance": tolerance,
        "safe_pruning": safe_pruning,    # TODO
        "user_predicates": user_predicates,
        "status": "Running" 
    }
    results[global_res_counter] = config
    return jsonify(config)

@app.route('/results', methods=['GET'])
def results_route():
    return jsonify(results)

@app.route('/results/delete', methods=['POST'])
def delete_results_route():
    global results
    result_to_delete = int(request.form['id'])
    del results[result_to_delete]
    return jsonify(success=True)

# First call that receives controller and config and returns constructed tree
@app.route("/construct", methods=['POST'])
def construct_route():
    # TODO T: continue here, compare with original
    global completed_experiments
    data = request.get_json()
    logging.info(f"Request: \n {data}")
    id = int(data['res_id'])
    cont = os.path.join(UPLOAD_FOLDER, data['controller'])
    # results.append([id, cont, nice_name, config, 'Running...', None, None, None])
    #results[id] = {"controller": cont, "nice_name": data['nice_name'], "status": "Running...",
    #               "inner_nodes": None, "leaf_nodes": None, "construction_time": None}

    if data["config"] == "custom":
        to_parse_dict = {
            "controller": cont,
            "config": "custom",
            "determinize": data['determinize'],
            "numeric-predicates": data['numeric_predicates'],
            "categorical-predicates": data['categorical_predicates'], 
            "impurity": data['impurity'],
            "tolerance": data['tolerance'],  # TODO T
            "safe-pruning": False   # TODO T
            }
    else:
        to_parse_dict = {"controller": cont, "config": data["config"]}

    # train takes in a dictionary and returns [constructed d-tree, x_metadata, y_metadata, root]
    try:
        classifier = frontend_helper.train(to_parse_dict)
        # root is saved in a global variable for use later
        saved_tree = classifier["classifier"].root

        num_vars = len(classifier["x_metadata"]["min_inner"])
        num_results = len(classifier["y_metadata"]["variables"]) if "variables" in classifier["y_metadata"] else 0
        min_bounds_inner = classifier["x_metadata"]["min_inner"]
        max_bounds_inner = classifier["x_metadata"]["max_inner"]
        min_bounds_outer = classifier["x_metadata"]["min_outer"]
        max_bounds_outer = classifier["x_metadata"]["max_outer"]
        step_size = classifier["x_metadata"]["step_size"]
        run_time = round(classifier["run_time"], 2)

        # completed_experiments[id] = (classifier["classifier_as_json"], saved_tree, min_bounds_inner, max_bounds_inner, step_size, num_vars, num_results, cont)
        completed_experiments[id] = {
            "classifier_as_json": classifier["classifier_as_json"],
            "saved_tree": saved_tree,
            "min_bounds_inner": min_bounds_inner,
            "max_bounds_inner": max_bounds_inner,
            "min_bounds_outer": min_bounds_outer,
            "max_bounds_outer": max_bounds_outer,
            "step_size": step_size,
            "num_vars": num_vars,
            "num_results": num_results,
            "controller": cont
        }
        stats = classifier["classifier"].get_stats()
        new_stats = [stats['inner nodes'], stats['nodes'] - stats['inner nodes'], run_time]
        # this_result = results[id]
        results[id]["status"] = "Completed"
        results[id]["inner_nodes"] = new_stats[0]
        results[id]["leaf_nodes"] = new_stats[1]
        results[id]["construction_time"] = new_stats[2]


    except Exception as e:
        print_exc()
        results[id]["status"] = "Error / " + type(e).__name__

    return jsonify(results[id])

@app.route("/check-user-predicate", methods=['POST'])
def check_user_predicate_route():
    data = request.get_json()
    # Logger Init
    # TODO T: logger
    logger = RicherDomainLogger("GetDomainKnowledge_Logger", False)
    logger.root_logger.info("Starting Domain Knowledge Parser.")

    # check the predicate
    try:
        term, relation, split_pred = PredicateParser.preprocess_single_predicate(data["predicate"], logger)
    except RicherDomainPredicateParserException:
        return json.dumps({"type": "error"})

    pred = str(term) + " " + str(relation) + " 0"
    if len(split_pred[1:]) > 0:
        pred += " ;" + ";".join(split_pred[1:])
    return json.dumps({"type": "success", "body": pred})

# First call that receives controller and config and returns constructed tree
def insert_into_tree(node_address, saved_tree, partial_tree):
    # Navigate to node_address in the saved_tree and insert the partial tree there
    pointer = saved_tree
    for pos in node_address[:-1]:
        pointer = pointer.children[pos]
    pointer.children[node_address[-1]] = partial_tree
    return saved_tree


def insert_into_json_tree(node_address, saved_json, partial_json):
    pointer = saved_json
    for pos in node_address[:-1]:
        pointer = pointer["children"][pos]
    pointer["children"][node_address[-1]] = partial_json
    return saved_json


@app.route("/construct-partial/from-preset", methods=['POST'])
def partial_construct():
    global completed_experiments, results
    data = request.get_json()
    id = int(data['id'])
    controller_file = os.path.join(UPLOAD_FOLDER, data['controller'])
    config = data['config']

    # TODO P Should we change what we have in results or should we create a new global var to store it?
    # results.append([id, controller_file, nice_name, config, 'Running...', None, None, None])

    if config == "custom":
        to_parse_dict = {"controller": controller_file, "determinize": data['determinize'],
                         "numeric-predicates": data['numeric_predicates'],
                         "categorical-predicates": data['categorical_predicates'], "impurity": data['impurity'],
                         "tolerance": data['tolerance'], "safe-pruning": data['safe_pruning']}
    elif config.startswith("algebraic"):
        # algebraic strategy with user predicates
        to_parse_dict = {"controller": controller_file, "config": "algebraic", "fallback": config.split("Fallback: ")[1][:-1],
                         "tolerance": data['tolerance'], "determinize": data['determinize'], "safe-pruning": data['safe_pruning'],
                         "impurity": data['impurity'], "user_predicates": html.unescape(data["user_predicates"])}
    else:
        to_parse_dict = {"controller": controller_file, "config": config}

    node_address = None
    saved_tree = None
    try:
        node_address = data["selected_node"]
        saved_tree = completed_experiments[id]["saved_tree"]
        to_parse_dict["existing_tree"] = saved_tree
        to_parse_dict["base_node_address"] = node_address
    except KeyError:
        pass

    # train takes in a dictionary and returns [constructed d-tree, x_metadata, y_metadata, root]
    try:
        classifier = frontend_helper.train(to_parse_dict)

        # First edit the classifier object
        if node_address:
            updated_tree = insert_into_tree(node_address, saved_tree, classifier["classifier"].root)
        else:
            updated_tree = classifier["classifier"].root

        # Then re-generate the json
        saved_json = completed_experiments[id]["classifier_as_json"]
        if node_address:
            updated_json = insert_into_json_tree(node_address, saved_json, classifier["classifier_as_json"])
        else:
            updated_json = classifier["classifier_as_json"]

        partial_json = classifier["classifier_as_json"]

        completed_experiments[id].update({
            "classifier_as_json": updated_json,
            "saved_tree": updated_tree
        })

        results[id]["status"] = "Edited"

    except Exception as e:
        print_exc()

    return jsonify({"partial_json": partial_json, "full_json": updated_json})


@app.route("/construct-partial/interactive", methods=['POST'])
def interactive_construct():
    global completed_experiments, results
    data = request.get_json()
    id = int(data['id'])
    controller_file = os.path.join(UPLOAD_FOLDER, data['controller'])

    # TODO P Should we change what we have in results or should we create a new global var to store it?
    # results.append([id, controller_file, nice_name, config, 'Running...', None, None, None])

    to_parse_dict = {"controller": controller_file}

    node_address = None
    saved_tree = None
    try:
        node_address = data["selected_node"]
        saved_tree = completed_experiments[id]["saved_tree"]
        to_parse_dict["existing_tree"] = saved_tree
        to_parse_dict["base_node_address"] = node_address
    except KeyError:
        pass

    # train takes in a dictionary and returns [constructed d-tree, x_metadata, y_metadata, root]
    try:
        if not interactive_queue.get_ready():
            interactive_queue.set_ready()
        print("Starting interactive mode...")
        classifier = frontend_helper.interactive(to_parse_dict)
        print("Obtained a completed tree from interactive mode.")

        interactive_queue.set_done()
        interactive_queue.reset()

        # First edit the classifier object
        if node_address:
            updated_tree = insert_into_tree(node_address, saved_tree, classifier["classifier"].root)
        else:
            updated_tree = classifier["classifier"].root

        # Then re-generate the json
        saved_json = completed_experiments[id]["classifier_as_json"]
        if node_address:
            updated_json = insert_into_json_tree(node_address, saved_json, classifier["classifier_as_json"])
        else:
            updated_json = classifier["classifier_as_json"]

        partial_json = classifier["classifier_as_json"]

        completed_experiments[id].update({
            "classifier_as_json": updated_json,
            "saved_tree": updated_tree
        })

        results[id]["status"] = "Edited"

    except Exception as e:
        print_exc()

    return jsonify({"partial_json": partial_json, "full_json": updated_json})


@app.route("/interact", methods=['POST'])
def interact_with_fit():
    command = request.get_json()
    print("Received command: ", command)
    if interactive_queue.get_ready():
        interactive_queue.send_to_back(command)
        response = interactive_queue.get_from_back()
        print("Received response: ", response)
    else:
        print("Queue not ready, perhaps interactive mode has completed.")
        response = {"type": "warning", "body": "Queue not ready. The interactive mode has perhaps completed."}
    return response


# route for selecting one of the computed configs
@app.route('/select', methods=['POST'])
def select():
    global selected_computation_id
    selected_computation_id = int(request.form['runConfigIndex'])
    return jsonify(success=True)


# route when loading default simulator
@app.route("/simulator")
def simulator():
    return render_template("simulator.html")


# returns the computed tree
@app.route("/computed")
def computed():
    global selected_computation_id
    selected_experiment = completed_experiments[selected_computation_id]
    returnDict = {
        "idUnderInspection": selected_computation_id,
        "classifier": selected_experiment["classifier_as_json"],
        "numVars": selected_experiment["num_vars"],
        "numResults": selected_experiment["num_results"],
        "boundInner": [selected_experiment["min_bounds_inner"], selected_experiment["max_bounds_inner"]],
        "boundOuter": [selected_experiment["min_bounds_outer"], selected_experiment["max_bounds_outer"]],
        "controllerFile": selected_experiment["controller"]
    }
    return jsonify(returnDict)


# Gets user input values to initialise the state variables
@app.route("/initRoute", methods=['POST'])
def init_route():
    # reset previous used variables
    global variable_subs, lambda_list, tau
    variable_subs = []
    lambda_list = []
    tau = 0

    data = request.get_json()
    id = int(data['id'])
    x = data['pass']
    dynamics_text = data['dynamics'].split('\n')

    saved_tree = completed_experiments[id]["saved_tree"]

    # Predict_one_step returns the decision taken as well as the path (list of ints) to reach that decision
    initDecision = saved_tree.predict_one_step(np.array([discretize(x)]))
    # print("row::" + str(list(map(lambda x: round(x, 6), discretize(x) + initDecision[0]))))

    returnDict = {"decision": initDecision[0], "path": initDecision[1], "dynamics": True}

    is_dynamics = False

    # Opens dynamics file and saves obtained variables and lambda functions as lists (variable_subs and lambda_list)
    if 'Dynamics:' in dynamics_text and 'Parameters:' in dynamics_text:
        for line in dynamics_text:
            line = line.strip()
            if line == 'Dynamics:':
                is_dynamics = True
            elif line == 'Parameters:':
                is_dynamics = False
            else:
                if line != '':
                    if not is_dynamics:
                        lhs, rhs = line.split("=")
                        variable_subs.append((lhs.strip(), float(rhs)))
                        if lhs.strip() == "tau" or lhs.strip() == "Tau":
                            tau = float(rhs)
                    else:
                        lhs, rhs = line.split("=")
                        tmp = sp.sympify(rhs.strip())
                        tmp = tmp.subs(variable_subs)
                        lam_1 = sp.lambdify(tmp.free_symbols, tmp)
                        lambda_list.append((lhs.strip(), lam_1, tmp.free_symbols))
        lambda_list = sorted(lambda_list, key=lambda x: int(x[0].split("_")[1]))
    else:
        # If dynamics is not present sets this to false and browser raises an exception
        returnDict["dynamics"] = False

    return jsonify(returnDict)


# Called on each step of the simulation
@app.route("/stepRoute", methods=['POST'])
def step_route():
    data = request.get_json()
    id = int(data['id'])
    x = data['x_pass']
    u = data['u_pass']

    saved_tree = completed_experiments[id]["saved_tree"]
    # Returns updated states variables
    x_new_non_classify = runge_kutta(list(x), u)
    newu_path = saved_tree.predict_one_step(np.array([discretize(list(x_new_non_classify))]))
    # print("row::" + str(list(map(lambda x: round(x, 6), discretize(list(x_new_non_classify)) + newu_path[0]))))
    returnDict = {"x_new": (x_new_non_classify,) + newu_path}
    return jsonify(returnDict)


# Called when using the instep function
@app.route("/inStepRoute", methods=['POST'])
def inStepRoute():
    data = request.get_json()
    id = int(data['id'])
    steps = data['steps']
    x = data['x_pass']
    u = data['u_pass']

    saved_tree = completed_experiments[id]["saved_tree"]
    x_new = []
    dummy = [x, u, "", False]
    for i in range(int(steps)):
        x_new_non_classify = runge_kutta(list(dummy[0]), dummy[1])

        newu_path = saved_tree.predict_one_step(np.array([discretize(list(x_new_non_classify))]))
        dummy = (x_new_non_classify,) + newu_path
        x_new.append(dummy)

    returnDict = {"x_new": x_new}
    return jsonify(returnDict)

@app.route("/random", methods=['POST'])
def pick_random_point():
    data = request.get_json()
    id = data['id']
    if selected_computation_id == id:
        controller_file = completed_experiments[id]["controller"]
        point = frontend_helper.get_random_point_from_dataset(controller_file)

        # # Perturbed point randomly
        # step_size = completed_experiments[selected_computation_id]["step_size"]
        # state_dimension = completed_experiments[selected_computation_id]["num_vars"]
        #
        # for i in range(state_dimension):
        #     # Add a number between [-eta, eta]
        #     point[i] += (random.random()-0.5) * step_size[i]
        #     point[i] = round(point[i], 6)

        return jsonify(point.tolist())
    else:
        return jsonify(None)

@app.route("/sample-websocket")
def start_websocket():
    frontend_helper.start_websocket_with_frontend()
    return "Starting websocket"

def recursive_scan(baseDir):
    for entry in os.scandir(baseDir):
        if entry.is_file():
            if (entry.name.endswith(".scs") or entry.name.endswith(".storm.json") or entry.name.endswith(".prism") or entry.name.endswith(
                    ".csv") or entry.name.endswith(".dump")) and (
                    not entry.name.startswith(".")):
                yield os.path.join(baseDir, entry.name)
        else:
            yield from recursive_scan(entry.path)


# Used to get the list of unzipped examples
@app.route("/examples", methods=['POST'])
def scan_valid_controllers():
    location = request.form.get('location')
    if os.path.exists(location):
        valid_controller_files = [file for file in recursive_scan(location)]
        return json.dumps({"status": 1, "files": valid_controller_files})
    else:
        return json.dumps({"status": -1})


# Used to read config.yml file
@app.route("/yml")
def yamlread():
    data = frontend_helper.load_default_config()
    return json.dumps(data)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        print('No file part')
        return "No file part"
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        print('No selected file')
        return "No selected file"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print("Successfully saved file", filename)
        return "Successfully saved file " + filename
    return "Invalid request"

global http_server


def handler(signal_received, frame):
    global http_server
    # Handle any cleanup here
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    http_server.stop()
    exit(0)


def start_web_frontend():
    global http_server
    print('Starting dtControl web interface...')
    logging.warning(
        'dtControl web interface is under development and may be unstable. One may find the commmand-line interface to be more reliable.')
    print('Navigate to http://127.0.0.1:5000/ in your browser to open the frontend. Press Ctrl+C to exit.')
    app.run(debug=False, use_reloader=False)
    # http_server = WSGIServer(('', 5000), app)
    # http_server.serve_forever()


if __name__ == "__main__":
    # Tell Python to run the handler() function when SIGINT is recieved
    # signal(SIGINT, handler)

    start_web_frontend()
