"""Public Search Server tests."""

import subprocess
import threading
import bs4
import utils

# We need to import test fixtures in specific test files because the fixture
# imports student code (like the index server).  If the student isn't finished
# with their code, then earlier tests (like pipeline tests) won't even run.
# pylint: disable-next=unused-import
from search_fixtures import (
    setup_teardown_db_connection,
    setup_teardown_search_client,
)


def test_concurrency(search_client, mocker):
    """Verify search is efficient through concurrent requests.

    'search_client' is a fixture function that provides a Flask test server
    interface

    Note: 'mocker' is a fixture function provided by the pytest-mock package.
    This fixture lets us override a library function with a temporary fake
    function that returns a hardcoded value while testing.

    Pytest fixture docs: https://docs.pytest.org/en/latest/fixture.html
    """
    spy = mocker.spy(threading.Thread, "start")
    response = search_client.get("/?q=hello+world")
    assert response.status_code == 200
    assert spy.call_count == 3


def test_inputs(search_client):
    """Verify the search page has the required form inputs.

    'search_client' is a fixture function that provides a Flask test server
    interface

    Pytest fixture docs: https://docs.pytest.org/en/latest/fixture.html
    """
    # Load search server main page
    response = search_client.get("/")
    assert response.status_code == 200
    soup = bs4.BeautifulSoup(response.data, "html.parser")

    # Inputs for "q" and "w"
    form_input_names = [
        submit.get("name") for button in soup.find_all('form')
        for submit in button.find_all("input") if submit
    ]
    assert "q" in form_input_names
    assert "w" in form_input_names

    # Inputs types
    form_input_types = [
        submit.get("type") for button in soup.find_all('form')
        for submit in button.find_all("input") if submit
    ]
    assert "text" in form_input_types
    assert "range" in form_input_types
    assert "submit" in form_input_types


def test_simple(search_client):
    """Verify a search returns any results at all.

    'search_client' is a fixture function that provides a Flask test server
    interface

    Pytest fixture docs: https://docs.pytest.org/en/latest/fixture.html
    """
    # Load search server main page after search
    response = search_client.get("/?q=hello+world")
    soup = response.status_code == 200
    soup = bs4.BeautifulSoup(response.data, "html.parser")

    # Verify query is displayed.
    query = soup.find(type="text")["value"]
    assert query == "hello world"

    # Make sure some doc titles show up
    assert soup.find_all("div", {"class": "doc_title"})


def test_titles(search_client):
    """Verify doc titles in results for a query with one term.

    'search_client' is a fixture function that provides a Flask test server
    interface

    Pytest fixture docs: https://docs.pytest.org/en/latest/fixture.html
    """
    # Load search server page with search query
    response = search_client.get("/?q=mapreduce&w=0.22")
    assert response.status_code == 200
    soup = bs4.BeautifulSoup(response.data, "html.parser")

    # Verify query and weight are displayed
    query = soup.find(type="text")["value"]
    assert query == "mapreduce"
    weight = soup.find(type="range")["value"]
    assert weight == "0.22"

    # Verify resulting document titles
    titles = soup.find_all("div", {"class": "doc_title"})
    assert len(titles) == 10
    titles = [x.get_text(strip=True) for x in titles]
    assert titles == [
        "MapReduce",
        "Native cloud application",
        "Big data",
        "Apache CouchDB",
        "Distributed file system for cloud",
        "Solution stack",
        "Category:Parallel computing",
        "Google File System",
        "Apache HBase",
        "MongoDB",
    ]


def test_summaries_urls(search_client, db_connection):
    """Verify summaries and URLs in results for a query with one term.

    'search_client' is a fixture function that provides a Flask test server
    interface

    'db_connection' is a fixture function that provides direct access to
    the search server's sqlite3 database.

    Pytest fixture docs: https://docs.pytest.org/en/latest/fixture.html
    """
    # Load search server page with search query
    response = search_client.get("/?q=nlp&w=0")
    assert response.status_code == 200
    soup = bs4.BeautifulSoup(response.data, "html.parser")

    # Correct titles we'll use for verification below
    titles_correct = [
        "NLP",
        "Natural language processing",
        "Process engineering",
        "Unstructured data",
        "Artificial intelligence",
        "School of Informatics, University of Edinburgh",
        "List of computer science awards",
        "Scientific modelling",
        "Unsupervised learning",
        "Virtual assistant",
    ]

    # Verify each search result
    docs = soup.find_all("div", {"class": "doc"})
    assert len(docs) == len(titles_correct)
    for doc, title_correct in zip(docs, titles_correct):
        # Get correct info
        summary_correct, href_correct = utils.get_document_info(
            db_connection, title_correct
        )

        # Verify title
        title = doc.find("div", {"class", "doc_title"})
        assert title, "Could not find class='doc_title'"
        title = title.get_text(strip=True)
        assert title == title_correct

        # Verify summary
        summary = doc.find("div", {"class", "doc_summary"})
        assert summary, "Could not find class='doc_summary'"
        summary = summary.get_text(strip=True)
        assert summary == summary_correct

        # Verify href and anchor text
        # Note: the anchor text and href will be the same because a link to
        # https://en.wikipedia.org/wiki/NLP appears on the page as
        # "https://en.wikipedia.org/wiki/NLP"
        link = doc.find("a", {"class": "doc_url"})
        assert link, "Could not find class='doc_url'"
        href = link.get("href")
        assert href, "Cound not find link in {doc}"
        anchor_text = link.get_text(strip=True)
        assert href == href_correct
        assert anchor_text == href_correct


def test_html(search_client, tmpdir):
    """Verify HTML5 compliance in HTML portion of the search pages.

    'search_client' is a fixture function that provides a Flask test server
    interface

    'tmpdir' is a fixture provided by the pytest package.  It creates a
    unique temporary directory before the test runs, and removes it afterward.
    https://docs.pytest.org/en/6.2.x/tmpdir.html#the-tmpdir-fixture
    """
    # Validate HTML of search page before a search
    download(search_client, "/", tmpdir/"index.html")
    subprocess.run(
        [
            "html5validator", "--ignore=JAVA_TOOL_OPTIONS",
            str(tmpdir/"index.html"),
        ],
        check=True,
    )

    # Validate HTML of search page after a search with no results
    download(search_client, "/?q=&w=0.01", tmpdir/"blank_query.html")
    subprocess.run(
        [
            "html5validator", "--ignore=JAVA_TOOL_OPTIONS",
            str(tmpdir/"blank_query.html"),
        ],
        check=True,
    )

    # Validate HTML of search page after a successful search
    download(search_client, "/?q=dogs&w=0.22", tmpdir/"simple_query.html")
    subprocess.run(
        [
            "html5validator", "--ignore=JAVA_TOOL_OPTIONS",
            str(tmpdir/"simple_query.html"),
        ],
        check=True,
    )


def download(search_client, url, outpath):
    """Load url using driver and save to outputpath."""
    response = search_client.get(url)
    assert response.status_code == 200

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    html = soup.prettify()

    # Write HTML of current page source to file
    outpath.write_text(html, encoding='utf-8')
