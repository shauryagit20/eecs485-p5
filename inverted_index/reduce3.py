#!/usr/bin/env -S python3 -u
"""Reduce 3."""
import sys
import math
from collections import defaultdict


def emit(
    emit_term: str,
    emit_idf: str,
    emit_postings: list[tuple[str, str]],
    emit_doc_norm: dict[str, float],
) -> None:
    """Emit final inverted-index line for one term."""
    emit_postings.sort(key=lambda posting: posting[0])
    parts = [emit_term, emit_idf]
    for emit_doc_id, emit_tf in emit_postings:
        parts.extend([emit_doc_id, emit_tf, str(emit_doc_norm[emit_doc_id])])
    print(" ".join(parts))


term_postings: dict[str, list[tuple[str, str]]] = defaultdict(list)
term_idf: dict[str, str] = {}
doc_norm_sq: defaultdict[str, float] = defaultdict(float)
doc_norm: dict[str, float] = {}

for line in sys.stdin:
    line = line.rstrip("\n")
    if not line:
        continue

    partition, term, idf, doc_id, tf = line.split("\t", 4)
    _ = partition
    term_idf[term] = idf
    term_postings[term].append((doc_id, tf))
    doc_norm_sq[doc_id] += (float(tf) * float(idf)) ** 2

for doc_id, norm_sq in doc_norm_sq.items():
    doc_norm[doc_id] = math.sqrt(norm_sq)

for term in sorted(term_postings):
    emit(term, term_idf[term], term_postings[term], doc_norm)
