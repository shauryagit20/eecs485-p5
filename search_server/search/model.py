import flask
import search
import sqlite3

def get_db():
    if 'sqlite_db' not in flask.g:
        flask.g.sqlite_db = sqlite3.connect("var/search.sqlite3")
        flask.g.sqlite_db.row_factory = sqlite3.Row
    
    return flask.g.sqlite_db

def close_db():
    db = flask.g.pop('sqlite_db', None)
    if db is not None:
        db.close()
