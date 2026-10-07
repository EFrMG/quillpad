"""Plain substring search over titles and bodies."""

from quillpad import store


def matches(note, query):
    query = query.lower()

    return query in note.title.lower() or query in note.body.lower()


def search(query):
    from quillpad import db

    return db.search(query)
