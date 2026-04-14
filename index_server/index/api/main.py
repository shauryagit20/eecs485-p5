"""Index Server API main."""

import math
import re

from flask import Blueprint, jsonify, request

from index import INDEX, PAGERANK, STOPWORDS

bp = Blueprint("api", __name__)


@bp.route("/api/v1/")
def services():
    """Return all available services."""
    return jsonify({
        "hits": "/api/v1/hits/",
        "url": "/api/v1/"
    })


def clean_query(text):
    """Clean query using regex."""
    text = re.sub(r"[^a-zA-Z0-9 ]+", "", text)
    text = text.casefold()
    _terms = text.split()

    terms = [term for term in _terms if term not in STOPWORDS]
    return terms


@bp.route("/api/v1/hits/")
def hits():
    """Return search results for a query."""
    query = request.args.get("q", "")
    w = float(request.args.get("w", 0.5))

    terms = clean_query(query)
    if not terms:
        return jsonify({"hits": []})

    doc_sets = []
    for term in terms:
        if term not in INDEX:
            return jsonify({"hits": []})
        doc_sets.append(set(INDEX[term][1].keys()))

    common_docs = set.intersection(*doc_sets)

    # ---- query vector ----
    query_tf = {}
    for term in terms:
        query_tf[term] = query_tf.get(term, 0) + 1

    query_vec = {}
    for term, tf in query_tf.items():
        idf = INDEX[term][0]
        query_vec[term] = tf * idf

    norm_q = math.sqrt(sum(v * v for v in query_vec.values()))
    for term in query_vec:
        query_vec[term] /= norm_q

    # ---- scoring ----
    results = []

    for docid in common_docs:
        score = 0

        for term in query_vec:
            idf, docs = INDEX[term]
            tf, norm = docs[docid]

            doc_weight = (tf * idf) / norm
            score += query_vec[term] * doc_weight

        pagerank = PAGERANK.get(docid, 0)
        final_score = (1 - w) * score + w * pagerank

        results.append({
            "docid": int(docid),
            "score": final_score
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    return jsonify({"hits": results})
