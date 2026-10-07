"""Plain substring search over titles and bodies."""

from quillpad import store


def matches(note, query):
    query = query.lower()

    return query in note.title.lower() or query in note.body.lower()


def search(query):
    return [note for note in store.load_all() if matches(note, query)]
