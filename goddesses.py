import os
import json

from bs4 import BeautifulSoup as soup
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

    # Remove all the h2's and li's.
    # The h2's are often empty, the li's are just ugly.
    my_soup = soup(goddess["extract"], "lxml")
    for tags in my_soup.find_all('h2'):
        tags.extract()
    for tags in my_soup.find_all('li'):
        tags.extract()
    goddess["extract"] = my_soup

    return render_template('goddess_page.html', goddess=goddess)

if __name__ == "__main__":
    app.run(debug=True)
