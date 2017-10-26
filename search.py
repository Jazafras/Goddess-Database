import whoosh.index as index
import indexer

print("Super Search! Gets the top 10 results & number of results of your query!")
search_term = input("Search something: ")
ix = index.open_dir("index_dir")
results = indexer.search(ix, search_term)
