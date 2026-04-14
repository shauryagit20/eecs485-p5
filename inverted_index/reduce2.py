#!/usr/bin/env -S python3 -u
"""Reduce 2: compute TF/IDF statistics and document normalization factors."""

import sys
import math
from collections import defaultdict
from typing import DefaultDict

inverted_index_tf: DefaultDict[str, DefaultDict[str, int]] = defaultdict(
    lambda: defaultdict(int)
)
inverted_index_idf: dict[str, float] = {}

with open("total_document_count.txt", "r", encoding="utf-8") as f:
    total_document_count = int(f.read())


for line in sys.stdin:
    line = line.rstrip("\n")
    key, value = line.split("\t", 1)
    inverted_index_tf[key][value] += 1


for term, doc_ids in inverted_index_tf.items():
    df = len(doc_ids)
    idf = math.log10(total_document_count / df)
    inverted_index_idf[term] = idf

for term in sorted(inverted_index_tf):
    idf = inverted_index_idf[term]
    doc_ids = inverted_index_tf[term]
    for doc_id in sorted(doc_ids):
        count = doc_ids[doc_id]
        print(f"{term}\t{idf}\t{doc_id}\t{count}")
