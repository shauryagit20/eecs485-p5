"""Search Server Test Fixtures.

Pytest fixture docs:
https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixture-functions
https://stackoverflow.com/questions/73191533/using-conftest-py-vs-importing-fixtures-from-dedicate-modules
"""

import contextlib
import logging
import shutil
import socket
import subprocess
import time
import urllib
from pathlib import Path
import sqlite3
import pytest
import utils
import search

# Set up logging
LOGGER = logging.getLogger("autograder")

# How long to wait for server in separate thread to start or stop
SERVER_START_STOP_TIMEOUT = 10

# Inverted index segment filenames
INDEX_PATHS = [
    "index_server/index/inverted_index/inverted_index_0.txt",
    "index_server/index/inverted_index/inverted_index_1.txt",
    "index_server/index/inverted_index/inverted_index_2.txt",
]


@pytest.fixture(name="db_connection")
def setup_teardown_db_connection():
    """Connect to the instructor search server's sqlite database."""
    db_conn = sqlite3.connect(utils.TESTDATA_DIR / "search.sqlite3")

    # Configure database to return dictionaries keyed on column name
    def dict_factory(cursor, row):
        """Convert database row objects to a dict keyed on column name."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    db_conn.row_factory = dict_factory

    # Foreign keys have to be enabled per-connection.  This is an sqlite3
    # backwards compatibility thing.
    db_conn.execute("PRAGMA foreign_keys = ON")

    # Transfer control to test.  The code before the "yield" statement is setup
    # code, which is executed before the test.  Code after the "yield" is
    # teardown code, which is executed at the end of the test.  Teardown code
    # is executed whether the test passed or failed.
    yield db_conn

    # Verify foreign key support is still enabled
    cur = db_conn.execute("PRAGMA foreign_keys")
    foreign_keys_status = cur.fetchone()
    assert foreign_keys_status["foreign_keys"], \
        "Foreign keys appear to be disabled."

    # Destroy database
    db_conn.close()


@pytest.fixture(name="search_client")
def setup_teardown_search_client():
    """Start a Search Server and Index Servers.

    The Search Server is a Flask test server.  The three Index Servers are live
    servers run in separate processes.
    We need different processes because each Index Server loads a segment into
    memory as a module level variable.  Therefore, we can't have one version of
    the index module in memory.  Port select is automatic.
    """
    LOGGER.info("Setup test fixture 'search_client'")

    # Reset database
    db_path = Path("var/search.sqlite3")
    db_path.parent.mkdir(exist_ok=True)
    shutil.copy(utils.TESTDATA_DIR/"search.sqlite3", db_path)

    # Configure Flask app.  Testing mode so that exceptions are propagated
    # rather than handled by the the app's error handlers.
    search.app.config["TESTING"] = True

    # Make sure Index servers aren't already running.  This Search server
    # fixture will start its own Index servers.
    index_proc = "flask --app index run --host 0.0.0.0 --port 900[0-2]"
    assert not utils.pgrep(index_proc), (
        "Found running Index servers. "
        "Try './bin/index stop' or 'pkill -f flask'"
    )

    # Each Index Server is a LiveIndexServer object whose lifetime is
    # automatically by a context manager
    with contextlib.ExitStack() as stack:

        # Start Index Servers
        live_index_servers = []
        for index_path in INDEX_PATHS:
            assert Path(index_path).exists()
            live_index_server = LiveIndexServer(index_path)
            stack.enter_context(live_index_server)
            live_index_servers.append(live_index_server)

        # Wait for Index Servers to start
        for live_index_server in live_index_servers:
            live_index_server.wait_for_urlopen()

        # Configure Search Server to connect to Index Server API URLs
        assert "SEARCH_INDEX_SEGMENT_API_URLS" in search.app.config, \
            "Can't find SEARCH_INDEX_SEGMENT_API_URLS in Search Server config."
        api_urls = [i.hits_api_url() for i in live_index_servers]
        search.app.config["SEARCH_INDEX_SEGMENT_API_URLS"] = api_urls

        # Transfer control to test.  The code before the "yield" statement is
        # setup code, which is executed before the test.  Code after the
        # "yield" is teardown code, which is executed at the end of the test.
        # Teardown code is executed whether the test passed or failed.
        with search.app.test_client() as client:
            yield client

    # Stop Index Servers.  Exiting the context will automatically stop the
    # Index server processes.
    LOGGER.info("Teardown test fixture 'search_client'")


class LiveIndexServerError(Exception):
    """Exception type used by LiveIndexServer."""


class LiveIndexServer:
    """Run an Index Server in a separate process.

    We need a separate process because the Index Server loads the inverted
    index into memory as a module level variable.  We want to run multiple
    Index Servers, each with a different segment loaded into memory.  If we
    used threads, then the different instances would share one data structure.
    """

    def __init__(self, index_path, port=None):
        """Store parameters."""
        self.index_path = index_path
        self.port = port if port is not None else self.get_open_port()
        self.process = None

    def __str__(self):
        """Return string describing this instance."""
        return f"LiveIndexServer({self.url()}, {self.index_path})"

    def __enter__(self):
        """Start Flask server in separate process on context manager enter."""
        flask_exe = shutil.which("flask")
        self.process = subprocess.Popen(
            [
                flask_exe,
                "--app", "index",
                "run",
                "--host", "localhost",
                "--port", str(self.port),
            ],
            env={
                "INDEX_PATH": self.index_path,
                # We need to set to environment variables specifying Unicode
                # support at the commandline
                # https://click.palletsprojects.com/en/8.0.x/unicode-support/
                "LC_ALL": "C.UTF-8",
                "LANG": "C.UTF-8",
            },
        )

    def __exit__(self, *args):
        """Stop process when context manager exists."""
        self.process.terminate()

    def url(self):
        """Return base URL of running server."""
        return f"http://localhost:{self.port}/"

    def hits_api_url(self):
        """Return REST API URL for the hits route."""
        url = urllib.parse.urljoin(self.url(), "/api/v1/hits/")
        return url

    @staticmethod
    def get_open_port():
        """Return a port that is available for use on localhost."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('', 0))
            port = sock.getsockname()[1]
        return port

    def wait_for_urlopen(self):
        """Wait for server to respond, return False if it times out."""
        for _ in range(10*SERVER_START_STOP_TIMEOUT):
            try:
                with urllib.request.urlopen(self.url()):
                    return
            except urllib.error.HTTPError as err:
                # Server returned a response.  Anything that's not an HTTP
                # error (5xx) indicate a working server.
                if err.code < 500:
                    return
                raise LiveIndexServerError(
                    f"{self} GET {self.url()} {err.code}"
                ) from err
            except urllib.error.URLError:
                pass
            if self.process.poll() is not None:
                raise LiveIndexServerError(f"Premature exit: {self}")
            time.sleep(0.1)
        raise LiveIndexServerError(f"Failed to start: {self}")
