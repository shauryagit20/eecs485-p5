"""Index Server Test Fixtures.

Pytest fixture docs:
https://docs.pytest.org/en/latest/fixture.html#conftest-py-sharing-fixture-functions
https://stackoverflow.com/questions/73191533/using-conftest-py-vs-importing-fixtures-from-dedicate-modules
"""

from pathlib import Path
import logging
import pytest

import index

# Set up logging
LOGGER = logging.getLogger("autograder")


@pytest.fixture(name="index_client")
def setup_teardown_index_client():
    """Start a Flask test server for one Index Server with segment 1.

    This fixture is used to test the REST API, it won't start a live server.
    Flask docs: https://flask.palletsprojects.com/en/1.1.x/testing/#testing
    """
    LOGGER.info("Setup test fixture 'index_client'")

    # Configure Flask app.  Testing mode so that exceptions are propagated
    # rather than handled by the the app's error handlers.
    index.app.config["TESTING"] = True

    # The Index server should read segment 1 by default
    assert "INDEX_PATH" in index.app.config, \
        "Can't find INDEX_PATH in Index Server config."
    assert Path(index.app.config["INDEX_PATH"]).name == "inverted_index_1.txt"
    assert Path(index.app.config["INDEX_PATH"]).exists()

    # Transfer control to test.  The code before the "yield" statement is setup
    # code, which is executed before the test.  Code after the "yield" is
    # teardown code, which is executed at the end of the test.  Teardown code
    # is executed whether the test passed or failed.
    with index.app.test_client() as client:
        yield client

    # Teardown code starts here
    LOGGER.info("Teardown test fixture 'index_client'")
