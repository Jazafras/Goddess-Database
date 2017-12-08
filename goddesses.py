import os
import json
import whoosh.index
from flask import Flask, render_template, request, redirect

import indexer

app = Flask(__name__)
goddesses = []

@app.route("/")
def index():
    global goddesses
    return render_template('index.html')

@app.route("/home/")
def home():
    return redirect('/')

@app.route('/search/', methods=['GET', 'POST'])
def search():
    global goddesses

    if request.method == 'POST':
        query = request.form['query']
    else:
        query = request.args
    ix = whoosh.index.open_dir("index_dir")
    goddesses = indexer.return_search(ix, query)
    return render_template('results.html', query=query, gs=goddesses)

@app.route("/goddess/", methods=['POST', 'GET'])
def goddess():
    goddess = json.load(open("data/" + request.args["pageid"] + ".json"))
    return render_template('goddess_page.html', goddess=goddess)

if __name__ == "__main__":
    app.run(debug=True)
