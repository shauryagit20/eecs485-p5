import flask
import search
import requests
import threading
from urllib.parse import unquote
import heapq

@search.app.route('/')
def show_index():
    """Display / route"""

    query = flask.request.args.get('q')
    weight = flask.request.args.get('w', 0.5, type=float)

    if not query:
        context = {"results": [], "q": "", "w": weight}
        return flask.render_template("base.html", **context)

    results = []

    def make_request(url):
        r = requests.get(url, params={"q": query, "w": weight})
        results.extend(r.json()["hits"])

    threads = []
    for url in search.app.config["SEARCH_INDEX_SEGMENT_API_URLS"]:
        t = threading.Thread(target=make_request, args=(url,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()  # wait for all threads to finish

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:10]

    connection = search.model.get_db()
    context = {}
    for r in results:
        cur = connection.execute("""SELECT title, summary, url 
                                    FROM documents WHERE docid = ?""",
                                    (r["docid"],)
                                )
        row = cur.fetchone()
        r["title"] = row["title"]
        r["url"] = row["url"]
        r["display_url"] = unquote(row["url"])
        r["summary"] = row["summary"]
    
    context = {
        "results": results,
        "q": query,
        "weight": weight,
    }

    return flask.render_template("base.html", **context)