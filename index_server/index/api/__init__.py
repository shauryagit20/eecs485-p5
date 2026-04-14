"""Index Server API."""

from index import app
from index.api.main import bp
from index.load import load_index

app.register_blueprint(bp)

__all__ = ["load_index"]
