#!/usr/bin/env -S python3 -u
"""Map 3: route postings to doc_id % 3 partitions."""

import sys


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    term, idf, doc_id, tf = line.split("\t", 3)
    partition_key = int(doc_id) % 3
    print(f"{partition_key}\t{term}\t{idf}\t{doc_id}\t{tf}")
