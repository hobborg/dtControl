import os
import webbrowser
import yaml
import json
from flask import Flask, render_template, url_for, json, request, Response, jsonify, request
from dtcontrol import frontFns 

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("basic_form.html")

@app.route("/final")
def loadTree():
    return render_template("tree_progress.html")

@app.route("/testjson")
def tst():
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, 'static', 'testjson.json')
    data = json.load(open(json_url))
    return jsonify(data)

@app.route("/midRoute", methods=['POST','GET'])
def loadText():
    cont = request.form.get('controller') #if key doesn't exist, returns None
    config = request.form.get('config')
    ToParserDict = {"controller": cont, "config" : config }

    # is a dict
    classi = frontFns.main_parse(ToParserDict)
    # json_object = json.dumps(classi) 
  
    # Writing to testjson.json 
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    with open(os.path.join(SITE_ROOT, 'static', 'testjson.json'), "w") as outfile: 
        # outfile.write(json_object) 
        json.dump([classi],outfile)
    
    # return '''<h1>The controller is: {} and {}</h1>'''.format(cont,config)
    # Currently turned off continuous refresh
    return render_template("tree_progress.html")

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
    webbrowser.open('http://127.0.0.1:5000/')
    app.run(debug=False)
