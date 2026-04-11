"""Utility and init script tests."""
import shutil
import subprocess
from pathlib import Path
import sqlite3
import pytest
import utils


# This pylint warning is endemic to pytest.
# pylint: disable=unused-argument


@pytest.fixture(name="setup_teardown")
def setup_teardown_fixture():
    """Set up the test and cleanup after."""
    # Setup code: make sure no stale processes are running
    assert not utils.pgrep("flask"), \
        "Found running flask process.  Try 'pkill -f flask'"

    # Transfer control to testcase
    yield None

    # Teardown: kill any stale processes
    utils.pkill("flask")
    assert utils.wait_for_flask_stop()


def test_executables(setup_teardown):
    """Verify bin/index, bin/search, bin/searchdb are shell scripts."""
    assert_is_script("bin/install")
    assert_is_script("bin/search")
    assert_is_script("bin/index")
    assert_is_script("bin/searchdb")


def test_install():
    """Verify install script contains the right commands."""
    install_content = Path("bin/install").read_text(encoding='utf-8')
    assert "python3 -m venv" in install_content
    assert "source env/bin/activate" in install_content
    assert "pip install -r requirements.txt" in install_content
    assert "pip install -e search_server" in install_content
    assert "pip install -e index_server" in install_content


def test_servers_start(setup_teardown):
    """Verify index and search servers start."""
    # We need to use subprocess.run() on commands that will return non-zero
    # pylint: disable=subprocess-run-check

    # Try to start search server with missing database
    db_path = Path("var/search.sqlite3")
    if db_path.exists():
        db_path.unlink()
    completed_process = subprocess.run(["bin/search", "start"])
    assert completed_process.returncode != 0

    # Create database
    db_path.parent.mkdir(exist_ok=True)
    shutil.copy(utils.TESTDATA_DIR/"search.sqlite3", db_path)

    # Try to start search server with missing index server
    completed_process = subprocess.run(["bin/search", "start"])
    assert completed_process.returncode != 0

    # Start index server, which should start 3 Flask processes
    subprocess.run(["bin/index", "start"], check=True)
    assert utils.wait_for_flask_start(nprocs=3)

    # Try to start index server when it's already running
    completed_process = subprocess.run(["bin/index", "start"])
    assert completed_process.returncode != 0

    # Start search server
    subprocess.run(["bin/search", "start"], check=True)
    assert utils.wait_for_flask_start(nprocs=4)

    # Try to start search server when it's already running
    completed_process = subprocess.run(["bin/search", "start"])
    assert completed_process.returncode != 0


def test_servers_stop(setup_teardown):
    """Verify index and search servers start."""
    # Start servers
    subprocess.run(["bin/index", "start"], check=True)
    assert utils.wait_for_flask_start(nprocs=3)
    subprocess.run(["bin/search", "start"], check=True)
    assert utils.wait_for_flask_start(nprocs=4)

    # Stop servers
    subprocess.run(["bin/index", "stop"], check=True)
    subprocess.run(["bin/search", "stop"], check=True)
    assert utils.wait_for_flask_stop()


def test_servers_status(setup_teardown):
    """Verify index and search init script status subcommand."""
    # We need to use subprocess.run() on commands that will return non-zero
    # pylint: disable=subprocess-run-check

    # Create database
    db_path = Path("var/search.sqlite3")
    db_path.parent.mkdir(exist_ok=True)
    shutil.copy(utils.TESTDATA_DIR/"search.sqlite3", db_path)

    # Verify status stopped
    completed_process = subprocess.run(["bin/index", "status"])
    assert completed_process.returncode != 0
    completed_process = subprocess.run(["bin/search", "status"])
    assert completed_process.returncode != 0

    # Start index and check status
    subprocess.run(["bin/index", "start"], check=True)
    assert utils.wait_for_flask_start(nprocs=3)
    completed_process = subprocess.run(["bin/index", "status"])
    assert completed_process.returncode == 0

    # Start search and check status
    subprocess.run(["bin/search", "start"], check=True)
    assert utils.wait_for_flask_start(nprocs=4)
    completed_process = subprocess.run(["bin/search", "status"])
    assert completed_process.returncode == 0

    # Stop servers
    subprocess.run(["bin/index", "stop"], check=True)
    subprocess.run(["bin/search", "stop"], check=True)
    assert utils.wait_for_flask_stop()


def test_searchdb(setup_teardown, tmpdir):
    """Test the searchdb script.

    Note: 'tmpdir' is a fixture provided by the pytest package.  It creates a
    unique temporary directory before the test runs, and removes it afterward.
    https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture
    """
    # We need to use subprocess.run() on commands that will return non-zero
    # pylint: disable=subprocess-run-check

    # Create tmp directory containing inverted_index/crawl
    Path(tmpdir/"inverted_index/crawl").mkdir(parents=True)
    shutil.copytree(
        utils.TESTDATA_DIR/"test_pipeline16/crawl",
        tmpdir/"inverted_index/crawl",
        dirs_exist_ok=True
    )

    # Run searchdb create and verify var/search.sqlite3 was created
    searchdb_path = Path("bin/searchdb").resolve()
    subprocess.run(
        searchdb_path,
        cwd=tmpdir,
        check=True,
    )
    db_path = tmpdir/"var/search.sqlite3"
    assert db_path.exists()

    # Assert contents of var/search.sqlite3
    expected = [
        (44664014,
         'Vector space model',
         ('Vector space model or term vector model is an algebraic model '
          'for representing text documents (and any objects, in general) '
          'as vectors of identifiers (such as index terms)....'),
         'https://en.wikipedia.org/wiki/eecs485_vector_space_model'),
        (67613335, 'PageRank',
         ('PageRank (PR) is an algorithm used by Google Search to rank web '
          'pages in their search engine results. It is named after both the '
          'word "web page" and co-founder Larry Page....'),
         'https://en.wikipedia.org/wiki/eecs485_pagerank'),
        (78661573, 'tf–idf',
         ('In information retrieval, tf–idf (also TF*IDF, TFIDF, TF–IDF, or '
          'Tf–idf), short for term frequency–inverse document frequency, is '
          'a measure of importance of a word to a document in a collection '
          'or corpus....'),
         'https://en.wikipedia.org/wiki/eecs485_tf_idf')]
    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT * FROM documents ORDER BY docid")
    actual = cur.fetchall()
    assert actual == expected


def assert_is_script(path):
    """Assert path is an executable shell script."""
    path = Path(path)
    assert path.exists()
    output = subprocess.run(
        ["file", path],
        check=True, stdout=subprocess.PIPE, universal_newlines=True,
    ).stdout
    assert "script" in output
    assert "executable" in output
