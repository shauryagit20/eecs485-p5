"""Load index, pagerank, and stopwords into memory."""

from pathlib import Path
from index import INDEX, PAGERANK, STOPWORDS, app


def _load_inverted_index(index_path: Path):
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


def _load_pagerank(base_dir: Path, index_path: Path):
    PAGERANK.clear()

    pagerank_path = base_dir / "pagerank.out"
    if not pagerank_path.exists():
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


def _load_stopwords(base_dir: Path, index_path: Path):
    STOPWORDS.clear()

    stopwords_path = base_dir / "stopwords.txt"
    if not stopwords_path.exists():
        stopwords_path = index_path.parent / "stopwords.txt"

    if not stopwords_path.exists():
        raise FileNotFoundError("stopwords.txt not found")

    with stopwords_path.open(encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word:
                STOPWORDS.add(word)


def load_index():
    """Load inverted index, pagerank, and stopwords into memory."""
    index_path = Path(app.config["INDEX_PATH"])
    base_dir = index_path.parent.parent

    _load_inverted_index(index_path)
    _load_pagerank(base_dir, index_path)
    _load_stopwords(base_dir, index_path)
