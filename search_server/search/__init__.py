"""Search server package."""
import flask

app = flask.Flask(__name__)
app.config.from_object('search.config')

import search.model
import search.views