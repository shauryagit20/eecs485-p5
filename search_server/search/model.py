"""model.py -- connecting & closing sqlite3 database."""
import flask
import search
import sqlite3


def get_db():
    """Create connection with sqlite3 db."""
    if 'sqlite_db' not in flask.g:
        flask.g.sqlite_db = sqlite3.connect("var/search.sqlite3")
        flask.g.sqlite_db.row_factory = sqlite3.Row
    return flask.g.sqlite_db


def close_db():
    """Close connection."""
    db = flask.g.pop('sqlite_db', None)
    if db is not None:
        db.close()
