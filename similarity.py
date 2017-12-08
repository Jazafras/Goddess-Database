from indexer import iter_goddess, get_text_from_html, load_goddess

from collections import Counter
from itertools import tee
import re
import json
import numpy as np
from math import log
from scipy.spatial.distance import cosine
from scipy.linalg import svd
import os

__alpha_re__ = re.compile(r"[^a-zA-Z ]")

def replace_non_alpha(string):
    return re.sub(__alpha_re__, ' ', string)

__space_re__ = re.compile(r"\s+")

def contract_spaces(string):
    return re.sub(__space_re__, ' ', string)

def prepare_string(string):
    if not string:
        return ""
    return contract_spaces(replace_non_alpha(string.casefold()))

def grams(iterable, skip=None):
    """From the 'pairwise' recipe:
    https://docs.python.org/3.6/library/itertools.html"""
    first, second = tee(iterable)
    next(second, None)
    if skip:
        for i in range(skip):
            next(second, None)
    return zip(first, second)

def get_wordcounts():
    wordcounts = Counter()
    for _, words in iter_words():
        wordcounts.update(words)
    return wordcounts

def iter_words():
    for goddess in iter_goddess():
        yield goddess['pageid'], prepare_string(get_text_from_html(goddess['extract'])).split()

def get_vocab(wordcounts):
    return set(wordcounts.keys())

def get_pairs(skip=None):
    counts = {}
    for goddess in iter_goddess():
        words = prepare_string(get_text_from_html(goddess['extract'])).split()
        counts[goddess['pageid']] = Counter(grams(words, skip=skip))
    return counts

def get_occurrences():
    counts = {}
    for goddess in iter_goddess():
        words = prepare_string(get_text_from_html(goddess['extract'])).split()
        counts[goddess['pageid']] = Counter(words)
    return counts

def get_lengths(occurrences=None):
    if occurrences is not None:
        return {k: sum(v.values()) for k, v in occurrences.items()}
    lengths = {}
    for goddess in iter_goddess():
        words = prepare_string(get_text_from_html(goddess['extract'])).split()
        lengths[goddess['pageid']] = len(words)
    return lengths

def get_single_word_probabilities(wordcounts):
    total_number_of_words = sum(v for v in wordcounts.values())
    return {k: n/total_number_of_words for k, n in wordcounts.items()}

def get_ids_and_maps(counts, vocab):
    outer_ids = sorted(counts.keys())
    outer_map = {pageid : i for i, pageid in enumerate(outer_ids)}
    inner_ids = sorted(vocab)
    inner_map = {word : i for i, word in enumerate(inner_ids)}
    return ((outer_ids, inner_ids), (outer_map, inner_map))

def threshold_your_vocab(wordcounts, threshold):
    return {k for k, v in wordcounts.items() if v > threshold}

def threshold_a_pair_counter(original_counter, thresholded_vocab):
    return Counter({(a, b): v for (a, b), v in original_counter.items() if a in thresholded_vocab and b in thresholded_vocab})

def threshold_the_pair_counts(counts):
    return {k: threshold_a_pair_counter(v) for k, v in counts.items()}

def threshold_a_counter(original_counter, thresholded_vocab):
    return Counter({k: v for k, v in original_counter.items() if k in thresholded_vocab})

def threshold_the_single_word_counts(counts):
    return {k: threshold_a_counter(v) for k, v in counts.items()}

def get_ids_and_maps(counts, vocab):
    outer_ids = sorted(counts.keys())
    outer_map = {pageid : i for i, pageid in enumerate(outer_ids)}
    inner_ids = sorted(vocab)
    inner_map = {word : i for i, word in enumerate(inner_ids)}
    return ((outer_ids, inner_ids), (outer_map, inner_map))

def get_term_frequency(occurrences):
    """Adjusted for document length because that varies a lot"""
    # Note: if the occurrences are thresholded, the uncommon
    # words will not be counted in the document lengths.
    lengths = get_lengths(occurrences)
    return {goddess_id: {term: occurrence/lengths[goddess_id]
                         for term, occurrence
                         in occurrences[goddess_id].items()}
            for goddess_id in lengths}

def get_inverse_document_frequency(occurrences):
    vocab_bags = {k: v.keys() for k, v in occurrences.items()}
    words_counted_once_per_document = Counter(
        word for goddess_id, vocab in vocab_bags.items() for word in vocab
    )
    all_documents = len(occurrences.keys())
    return {term: log(all_documents/documents) for term, documents in words_counted_once_per_document.items()}

def get_tf_idf_dict():
    occurrences = get_occurrences()
    tf = get_term_frequency(occurrences)
    idf = get_inverse_document_frequency(occurrences)
    return {goddess_id:
              {term: term_freq*idf[term]
               for term, term_freq in tf_dict.items()}
              for goddess_id, tf_dict in tf.items()}

def tf_idf_matrix(tf_idf_dict, vocab=None):
    if vocab is None:
        vocab = {term for counter in tf_idf_dict.values() for term in counter.keys()}
    (outer_ids, inner_ids), (outer_map, inner_map) = get_ids_and_maps(tf_idf_dict, vocab)
    # first index is term, second index is column
    # this is the opposite of the 3d version
    # which is why outer/inner is backwards
    matrix = np.zeros(shape=(len(inner_ids), len(outer_ids)))
    for goddess_id, goddess_tf_idf in tf_idf_dict.items():
        goddess_index = outer_map[goddess_id]
        for term, tf_idf in goddess_tf_idf.items():
            term_index = inner_map[term]
            matrix[term_index, goddess_index] = tf_idf
    return matrix, outer_map, inner_map


def cooccurrence_matrix(thresholded_counts, single_word_probabilities, thresholded_vocab=None, inner_ids_maps=None):
    if inner_ids_maps is not None:
        inner_ids, inner_map = inner_ids_maps
    else:
        (_, inner_ids), (_, inner_map) = get_ids_and_maps(thresholded_counts, thresholded_vocab)
    matrix = np.zeros(shape=(len(inner_ids), len(inner_ids)))
    for counter_dict in thresholded_counts.values():
        for (first, second), num in counter_dict.items():
            first_index = inner_map[first]
            second_index = inner_map[second]
            matrix[first_index, second_index] += num

    # p(a, b) / (p(a)p(b))
    # p(a, b) is number of that pair over all pairs
    # p(a) is count of that word over all words
    # p(b) is count of that word over all words

    total_number_of_pairs = np.sum(np.sum(matrix, axis=0), axis=0)
    matrix /= total_number_of_pairs
    for word, word_prob in single_word_probabilities.items():
        if word not in inner_map:
            continue
        ind = inner_map[word]
        matrix[:, ind] /= word_prob
        matrix[ind, :] /= word_prob
    return matrix

def get_word_vectors_from_cooccurrence(matrix):
    print("Beginning the SVD")
    print("The matrix is {} so it'll take a while".format(matrix.shape))
    u, s, vh = svd(matrix)
    return u * s

def get_doc_vectors_from_word_vectors(vectors, inner_map):
    doc_vectors = {}
    for g_id, words in iter_words():
        shape = vectors[0].shape
        doc_vector = np.zeros(shape)
        factor = 1/len(words)
        for word in words:
            if word in inner_map:
                word_index = inner_map[word]
                word_vec = vectors[word_index]
                doc_vector += factor * word_vec
        doc_vectors[g_id] = doc_vector
    return doc_vectors

def get_doc_vectors_from_tf_idf(matrix):
    print("Beginning the SVD")
    print("The matrix is {} so it'll take a while".format(matrix.shape))
    u, s, vh = svd(matrix)
    return s * vh

def get_them_doc_vectors(threshold=20):
    tf_idf_dict = get_tf_idf_dict()
    vocab = threshold_your_vocab(get_wordcounts(), threshold)
    tf_idf_dict = {g_id:
                   {k: tf_idf
                    for k, tf_idf in v.items()
                    if k in vocab}
                   for g_id, v in tf_idf_dict.items()}
    matrix, outer_map, inner_map = tf_idf_matrix(tf_idf_dict)
    doc_vectors = get_doc_vectors_from_tf_idf(matrix)
    return doc_vectors, outer_map

def get_distances_from_doc_vectors(doc_vectors, outer_map, limit=10):
    distances = {}
    for g_id in outer_map:
        distances[g_id] = []
        for second_id in outer_map:
            if g_id == second_id:
                continue
            distances[g_id].append(
                (cosine(
                doc_vectors[outer_map[g_id]],
                doc_vectors[outer_map[second_id]]), second_id))
        distances[g_id].sort()
        distances[g_id] = distances[g_id][:limit]
    return distances

def path_of_g_id(g_id):
    return os.path.join("data", str(g_id) + ".json")

def replace_all_the_json_distances_with_tf_idf_ones(threshold=15):
    doc_vectors, outer_map = get_them_doc_vectors(threshold=threshold)
    distances = get_distances_from_doc_vectors(doc_vectors, outer_map, limit=3)
    clipped_distances = {k: [g_id for _, g_id in l] for k, l in distances.items()}
    for g_id, similar in clipped_distances.items():
        goddess = load_goddess(g_id)
        goddess['similar'] = json.dumps(similar)
        with open(path_of_g_id(g_id), 'w') as fp:
            json.dump(goddess, fp)


def main():
    try:
        replace_all_the_json_distances_with_tf_idf_ones(threshold=10)
    except MemoryError:
        replace_all_the_json_distances_with_tf_idf_ones(threshold=20)

if __name__ == "__main__":
    main()
