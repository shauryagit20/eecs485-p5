#!/usr/bin/env -S python3 -u


"""Map 2: Clean parsed document text and emit term-document pairs.

Reads parsed documents from stdin, applies normalization and filtering, and
emits one record per remaining term occurrence.

Input:
    Tab-delimited lines in the form:
        <doc_id>\t<document_content>

Output:
    Tab-delimited lines in the form:
        <term>\t<doc_id>

Cleaning pipeline:
    1. Remove non-alphanumeric characters except spaces.
    2. Normalize case using str.casefold().
    3. Split into whitespace-delimited terms.
    4. Remove stopwords from stopwords.txt.
"""

import sys
import re

STOPWORDS = set(open("stopwords.txt").read().split())


def _clean(text):
    text = re.sub(r"[^a-zA-Z0-9 ]+", "", text)
    text = text.casefold()
    _terms = text.split()

    terms = [term for term in _terms if term not in STOPWORDS]
    return terms



for line in sys.stdin:
    line = line.rstrip("\n")
    if not line or "\t" not in line:
        continue
    key, value = line.split("\t", 1)
    terms = _clean(value)
    for term in terms:
        print(f"{term}\t{key}")
