"""Search server package."""
import flask
import search.model
import search.views

app = flask.Flask(__name__)
app.config.from_object('search.config')
