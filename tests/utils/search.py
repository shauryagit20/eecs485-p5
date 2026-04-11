"""Search server utilities."""


def get_document_info(db_connection, title):
    """Get summary and URL for a document by title."""
    # We need to fetch the summaries and URLs one at a time to preserve
    # the order of the search results
    cur = db_connection.execute(
        "SELECT summary, url FROM documents WHERE title = ?", (title,)
    )
    res = cur.fetchone()
    summary = res['summary'] if res['summary'] else "No summary available"
    url = res['url']
    return summary, url
