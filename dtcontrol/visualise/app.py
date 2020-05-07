import os
import webbrowser
from flask import Flask, render_template, url_for, json, request, Response, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("tree_progress.html")

@app.route("/tee")
def showjson():
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, 'static', 'tee.json')
    data = json.load(open(json_url))
    return jsonify(data)
    
# if __name__ == "__main__":
#     app.run(debug=True)
# else:
#     app.run(debug=True)

def runFlask():
    print('##########Opening browser##########')
    webbrowser.open('http://127.0.0.1:5000/')
    app.run(debug=False)