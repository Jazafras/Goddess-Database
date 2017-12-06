import os
import whoosh.index
from flask import Flask, render_template, request, redirect

import indexer

app = Flask(__name__)  # create app instance
goddesses = []


@app.route("/")
def index():
    #global goddesses
    return render_template('index.html')

@app.route("/home-page/")
def home():
    return redirect('/')


@app.route('/search/', methods=['GET', 'POST'])
def search():
    global goddesses
    query = request.form['query']
    #query = data.get['query']
    ix = whoosh.index.open_dir("index_dir")
    goddesses = indexer.return_search(ix, query)
    #return redirect('/')
    return render_template('results.html', query=query, gs=goddesses)

@app.route("/goddess/")
def goddess():
    return render_template('goddess_page.html')

if __name__ == "__main__":
    app.run(debug=True)
#OLD CODE
#search_term = input("Search something: ")
#ix = index.open_dir("index_dir")
#results = indexer.search(ix, search_term)