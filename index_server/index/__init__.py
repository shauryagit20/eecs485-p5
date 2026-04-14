"""Index Server."""

import os
from pathlib import Path

from flask import Flask

app = Flask(__name__)

INDEX = {}
PAGERANK = {}
STOPWORDS = set()

INDEX_DIR = Path(__file__).resolve().parent / "inverted_index"
app.config["INDEX_PATH"] = os.getenv(
    "INDEX_PATH",
    str((INDEX_DIR / "inverted_index_1.txt").resolve()),
)

import index.api  # noqa: E402  pylint: disable=wrong-import-position

# Load inverted index, stopwords, and pagerank into memory
index.api.load_index()
