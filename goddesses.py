import os
import whoosh.index
from flask import Flask, render_template, request, redirect

import indexer

app = Flask(__name__) # create app instance
goddesses = []

@app.route("/")
def index():
  global goddesses
  return render_template('index.html',
                          gs=goddesses)

@app.route('/search', methods = ['POST'])
def search():
  global goddesses
  query = request.form['query']
  ix = whoosh.index.open_dir("index_dir")
  goddesses = indexer.return_search(ix, query)
  return redirect('/')

if __name__ == "__main__":
  app.run(debug=True)
#OLD CODE
#search_term = input("Search something: ")
#ix = index.open_dir("index_dir")
#results = indexer.search(ix, search_term)
