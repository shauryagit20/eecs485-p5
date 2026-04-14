import math
from collections import defaultdict
from pathlib import Path

from index import INDEX, PAGERANK, STOPWORDS, app


def _first_existing(*paths):
    """Return the first path that exists."""
    for p in paths:
        if p.exists():
            return p
    return None


def load_index():
    """Load inverted index, pagerank, and stopwords into memory."""
    # Load single inverted index segment
    index_path = Path(app.config["INDEX_PATH"])
    data_dir = index_path.parent.parent  # up from inverted_index/ to index/

    INDEX.clear()

    with index_path.open(encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:
                continue

            term = parts[0]
            idf = float(parts[1])
            postings = parts[2:]

            if term not in INDEX:
                INDEX[term] = (idf, {})

            for i in range(0, len(postings), 3):
                docid = int(postings[i])
                tf = float(postings[i + 1])
                norm = float(postings[i + 2])
                INDEX[term][1][docid] = (tf, norm)

    # Load PageRank
    PAGERANK.clear()
    pagerank_path = data_dir / "pagerank.out"
    if not pagerank_path.exists():
        # Also check same directory as the index file
        pagerank_path = index_path.parent / "pagerank.out"
    if not pagerank_path.exists():
        raise FileNotFoundError("pagerank.out not found")

    with pagerank_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docid, score = line.split(",", 1)
            PAGERANK[int(docid)] = float(score)

    # Load Stopwords
    STOPWORDS.clear()
    stopwords_path = data_dir / "stopwords.txt"
    if not stopwords_path.exists():
        stopwords_path = index_path.parent / "stopwords.txt"
    if not stopwords_path.exists():
        raise FileNotFoundError("stopwords.txt not found")

    with stopwords_path.open(encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word:
                STOPWORDS.add(word)