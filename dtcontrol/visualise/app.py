import os
import webbrowser
import yaml
import json
import numpy as np
from flask import Flask, render_template, url_for, json, request, Response, jsonify, request
from dtcontrol import frontFns, cartClassify

app = Flask(__name__)
saved_tree = []
minBounds = []
maxBounds  = []

@app.route("/")
def home():
    return render_template("merge2.html")

@app.route("/simulator")
def simulator():
    return render_template("simulator.html")

@app.route("/simRoute", methods=['POST'])
def simroute():
    #if key doesn't exist, returns None
    data = request.get_json()
    cont = data['controller']
    config = data['config']
    ToParserDict = {}
    if(config=="custom"):
        ToParserDict = {"controller": cont, "determinize": data['determinize'] ,"numeric-predicates": data['numeric_predicates'],"categorical-predicates": data['categorical_predicates'],"impurity": data['impurity'],"tolerance": data['tolerance'],"safe-pruning": data['safe_pruning'] }
    else:
        ToParserDict = {"controller": cont, "config" : config }

    # is a dict
    classi = frontFns.main_parse(ToParserDict)
    global saved_tree, minBounds, maxBounds
    saved_tree = classi[3]
    numVars = len(classi[1]["min"])
    numResults = len(classi[2]["variables"])
    minBounds = classi[1]["min"]
    maxBounds = classi[1]["max"]
    returnDict = {"classi":([classi[0]]),"numVars":numVars,"numResults":numResults,"bound":[minBounds,maxBounds]}
    return jsonify(returnDict)

@app.route("/initRoute", methods=['POST'])
def initroute():
    data = request.get_json()
    x = data['pass']
    initDecision = saved_tree.predict_one_step(np.array([x]))
    returnDict = {"decision":initDecision[0],"path":initDecision[1]}
    return jsonify(returnDict)

@app.route("/stepRoute", methods=['POST'])
def stepRoute():
    data = request.get_json()
    x = data['x_pass']
    u = data['u_pass']
    x_new_non_classify = cartClassify.step(x,u)
    newu_path = saved_tree.predict_one_step(np.array([list(x_new_non_classify)]))
    returnDict = {"x_new":(x_new_non_classify,)+newu_path}
    return jsonify(returnDict)

@app.route("/inStepRoute", methods=['POST'])
def inStepRoute():
    data = request.get_json()
    steps = data['steps']
    x = data['x_pass']
    u = data['u_pass']

    x_new = []
    dummy = [x,u,"",False]
    for i in range(int(steps)):
        x_new_non_classify = cartClassify.step(dummy[0], dummy[1])
        newu_path = saved_tree.predict_one_step(np.array([list(x_new_non_classify)]))
        dummy = (x_new_non_classify,)+newu_path
        x_new.append(dummy)
        # if(dummy[3]):
        #     break

    returnDict = {"x_new":x_new}
    return jsonify(returnDict)

@app.route("/tee")
def showjson():
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, 'static', 'tee.json')
    data = json.load(open(json_url))
    return jsonify(data)

@app.route("/examples")
def showscs():
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    egs_path = os.path.join(SITE_ROOT, '..','..','examples')
    valid_egs_list = []
    for file in os.scandir(egs_path):
        if (file.name.endswith(".scs") and (not file.name.startswith("."))):
            # print(file.name)
            valid_egs_list.append(file.name)
    return json.dumps(valid_egs_list)
    
@app.route("/yml")
def yamlread():
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, '..', 'config.yml')
    data = yaml.load(open(json_url), Loader = yaml.FullLoader)
    return json.dumps(data)

def runFlask():
    print('##########Opening browser##########')
    chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
    webbrowser.get(chrome_path).open('http://127.0.0.1:5000/')
    app.run(debug=False)

if __name__ == "__main__":
    runFlask()