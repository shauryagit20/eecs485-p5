"""Search server package."""
import flask

app = flask.Flask(__name__)
app.config.from_object('search.config')

import search.model  # noqa: E402  pylint: disable=wrong-import-position
import search.views  # noqa: E402  pylint: disable=wrong-import-position
