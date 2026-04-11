"""Public Index Server tests."""
import utils

# We need to import test fixtures in specific test files because the fixture
# imports student code (like the index server).  If the student isn't finished
# with their code, then earlier tests (like pipeline tests) won't even run.
# pylint: disable-next=unused-import
from index_fixtures import setup_teardown_index_client


def test_multiple_terms(index_client):
    """Multiple word query.

    'index_client' is a fixture fuction that provides a Flask test server
    interface. It is reused by many tests.
    Docs: https://docs.pytest.org/en/latest/fixture.html
    """
    # Query the REST API
    response = index_client.get("/api/v1/hits/?q=water+bottle")
    assert response.status_code == 200

    # Compare actual hits to solution hits
    hits_actual = response.get_json()["hits"]
    hits_solution = [
        {
            "docid": 30205618,
            "score": 0.102982923870853
        },
        {
            "docid": 95141965,
            "score": 0.00761381815735493
        },
        {
            "docid": 35729704,
            "score": 0.00623011813284347
        },
        {
            "docid": 76162348,
            "score": 0.00407747721880189
        },
        {
            "docid": 898651,
            "score": 0.00317418187830592
        },
        {
            "docid": 85059529,
            "score": 0.00272874248684155
        },
        {
            "docid": 92309236,
            "score": 0.00197860567212674
        }
    ]
    utils.assert_rest_api_hit_eq(hits_actual, hits_solution)


def test_special_characters(index_client):
    """Special characters in query.

    'index_client' is a fixture fuction that provides a Flask test server
    interface. It is reused by many tests.
    Docs: https://docs.pytest.org/en/latest/fixture.html
    """
    # Query the REST API
    response = index_client.get(
        "/api/v1/hits/?q=the+^most+apache+@@had@@oop&w=0"
    )
    assert response.status_code == 200

    # Compare actual hits to solution hits
    hits_actual = response.get_json()["hits"]
    hits_solution = [
        {
            "docid": 23456371,
            "score": 0.250647094941722
        },
        {
            "docid": 466255,
            "score": 0.211891318330724
        },
        {
            "docid": 98442370,
            "score": 0.098744924912418
        },
        {
            "docid": 97733842,
            "score": 0.0503605072816249
        },
        {
            "docid": 41403379,
            "score": 0.0239315163039933
        },
        {
            "docid": 97675399,
            "score": 0.0186564134695005
        },
        {
            "docid": 30761410,
            "score": 0.0154987429840372
        },
        {
            "docid": 30696820,
            "score": 0.007318690655749
        },
        {
            "docid": 65344246,
            "score": 0.00597057615341795
        },
        {
            "docid": 3080602,
            "score": 0.0050207146240762
        }
    ]
    utils.assert_rest_api_hit_eq(hits_actual, hits_solution)


def test_stopwords(index_client):
    """Stopwords in query.

    'index_client' is a fixture fuction that provides a Flask test server
    interface. It is reused by many tests.
    Docs: https://docs.pytest.org/en/latest/fixture.html
    """
    # Query the REST API
    response = index_client.get("/api/v1/hits/?q=the+most+apache+hadoop&w=0")
    assert response.status_code == 200

    # Compare actual hits to solution hits
    hits_actual = response.get_json()["hits"]
    hits_solution = [
        {
            "docid": 23456371,
            "score": 0.250647094941722
        },
        {
            "docid": 466255,
            "score": 0.211891318330724
        },
        {
            "docid": 98442370,
            "score": 0.098744924912418
        },
        {
            "docid": 97733842,
            "score": 0.0503605072816249
        },
        {
            "docid": 41403379,
            "score": 0.0239315163039933
        },
        {
            "docid": 97675399,
            "score": 0.0186564134695005
        },
        {
            "docid": 30761410,
            "score": 0.0154987429840372
        },
        {
            "docid": 30696820,
            "score": 0.007318690655749
        },
        {
            "docid": 65344246,
            "score": 0.00597057615341795
        },
        {
            "docid": 3080602,
            "score": 0.0050207146240762
        }
    ]
    utils.assert_rest_api_hit_eq(hits_actual, hits_solution)


def test_term_not_in_index(index_client):
    """Query term not in inverted index.

    'index_client' is a fixture fuction that provides a Flask test server
    interface. It is reused by many tests.
    Docs: https://docs.pytest.org/en/latest/fixture.html
    """
    response = index_client.get("/api/v1/hits/?q=issued+aaaaaaa&w=0.5")
    assert response.status_code == 200
    assert response.get_json() == {"hits": []}
