import whoosh.index as index
import indexer

search_term = input("Search something: ")
ix = index.open_dir("index_dir")
results = indexer.search(ix, search_term)

