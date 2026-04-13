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
    """
    Load:
    - inverted index segment(s)
    - pagerank.out
    - stopwords.txt

    into global in-memory structures.
    Runs ONCE at startup.
    """

    # ----------------------------
    # Resolve index path (IMPORTANT)
    # ----------------------------
    index_path = Path(app.config["INDEX_PATH"])

    segments_dir = index_path.parent
    data_dir = segments_dir.parent

    # ----------------------------
    # Load inverted index segment(s)
    # ----------------------------
    raw = {}

    for file in sorted(segments_dir.glob("inverted_index_*.txt")):
        with file.open(encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 2:
                    continue

                term = parts[0]
                idf = float(parts[1])

                postings = parts[2:]

                # docid tf norm repeating triples
                for i in range(0, len(postings), 3):
                    docid = int(postings[i])
                    tf = float(postings[i + 1])

                    if term not in raw:
                        raw[term] = (idf, defaultdict(float))

                    raw[term][1][docid] += tf

    # ----------------------------
    # Compute document norms
    # ----------------------------
    doc_norm_sq = defaultdict(float)

    for idf, doc_dict in raw.values():
        for docid, tf in doc_dict.items():
            doc_norm_sq[docid] += (tf * idf) ** 2

    doc_norm = {
        docid: math.sqrt(val) for docid, val in doc_norm_sq.items()
    }

    # ----------------------------
    # Build final INDEX structure
    # ----------------------------
    INDEX.clear()

    for term, (idf, doc_dict) in raw.items():
        INDEX[term] = (
            idf,
            {
                docid: (tf, doc_norm[docid])
                for docid, tf in doc_dict.items()
            },
        )

    # ----------------------------
    # Load PageRank
    # ----------------------------
    PAGERANK.clear()

    pagerank_path = _first_existing(
        segments_dir / "pagerank.out",
        data_dir / "pagerank.out",
    )

    if pagerank_path is None:
        raise FileNotFoundError("pagerank.out not found")

    with pagerank_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docid, score = line.split(",", 1)
            PAGERANK[int(docid)] = float(score)

    # ----------------------------
    # Load Stopwords
    # ----------------------------
    STOPWORDS.clear()

    stopwords_path = _first_existing(
        segments_dir / "stopwords.txt",
        data_dir / "stopwords.txt",
    )

    if stopwords_path is None:
        raise FileNotFoundError("stopwords.txt not found")

    with stopwords_path.open(encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word:
                STOPWORDS.add(word)