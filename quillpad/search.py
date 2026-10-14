"""Search words across note titles and bodies."""

from quillpad import store


def matches(note, query):
    terms = query.lower().split()
    text = f"{note.title} {note.body}".lower()

    return bool(terms) and all(term in text for term in terms)


def search(query):
    return [note for note in store.load_all() if matches(note, query)]
