import os
import webbrowser
import yaml
import json
from flask import Flask, render_template, url_for, json, request, Response, jsonify, request
from dtcontrol import frontFns, cartClassify

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("basic_form.html")

@app.route("/simulator")
def simulator():
    return render_template("simulator.html")

# @app.route("/final")
# def loadTree():
#     return render_template("tree_progress.html")

# @app.route("/testjson")
# def tst():
#     SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
#     json_url = os.path.join(SITE_ROOT, 'static', 'testjson.json')
#     data = json.load(open(json_url))
#     return jsonify(data)

@app.route("/midRoute", methods=['POST'])
def loadText():
    cont = request.form.get('controller') #if key doesn't exist, returns None
    config = request.form.get('config')
    ToParserDict = {"controller": cont, "config" : config }

    # is a dict
    classi = frontFns.main_parse(ToParserDict)
  
    # SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    # with open(os.path.join(SITE_ROOT, 'static', 'testjson.json'), "w") as outfile: 
    #     json.dump([classi],outfile)

    # return render_template("tree_progress.html")
    # return classi
    # return '''<h1>The controller is: {} and {}</h1>'''.format(cont,config)
    return jsonify([classi])

@app.route("/simRoute", methods=['POST'])
def simroute():
    cont = request.form.get('controller') #if key doesn't exist, returns None
    config = request.form.get('config')
    ToParserDict = {"controller": cont, "config" : config }

    # is a dict
    classi = frontFns.main_parse(ToParserDict)
    return jsonify([classi])

@app.route("/initRoute", methods=['POST'])
def initroute():
    x0 = request.form.get('x0') #if key doesn't exist, returns None
    x1 = request.form.get('x1')
    initDecision = cartClassify.classify(x0,x1)
    x0_bound, x1_bound = cartClassify.getBounds()
    returnDict = {"decision":str(initDecision[0]),"path":initDecision[1],"x0_bound":x0_bound,"x1_bound":x1_bound}
    return jsonify(returnDict)

@app.route("/stepRoute", methods=['POST'])
def stepRoute():
    x0 = request.form.get('x0') #if key doesn't exist, returns None
    x1 = request.form.get('x1')
    u = request.form.get('u')

    x_new  = cartClassify.step([x0,x1],u)

    returnDict = {"x_new":x_new}
    return jsonify(returnDict)

@app.route("/inStepRoute", methods=['POST'])
def inStepRoute():
    steps = request.form.get('steps')
    x0 = request.form.get('x0')
    x1 = request.form.get('x1')
    u = request.form.get('u')

    x_new = []
    dummy = [[x0,x1],u,"",False]
    for i in range(int(steps)):
        dummy = cartClassify.step(dummy[0],dummy[1])
        x_new.append(dummy)

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

# if __name__ == "__main__":
#     app.run(debug=True)
# else:
#     app.run(debug=True)

def runFlask():
    print('##########Opening browser##########')
    chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
    webbrowser.get(chrome_path).open('http://127.0.0.1:5000/simulator')
    app.run(debug=False)