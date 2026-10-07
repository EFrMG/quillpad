"""Substring search over titles and bodies, with a cached lowercase index."""

import json

from quillpad import store


def index_path():
    return store.home() / ".index.json"


def build_index():
    index = {note.slug: f"{note.title}\n{note.body}".lower() for note in store.load_all()}
    index_path().write_text(json.dumps(index))

    return index


def load_index():
    newest = max((path.stat().st_mtime for path in store.home().glob("*.md")), default=0)
    if index_path().exists() and index_path().stat().st_mtime >= newest:
        return json.loads(index_path().read_text())

    return build_index()


def matches(note, query):
    query = query.lower()

    return query in note.title.lower() or query in note.body.lower()


def search(query):
    hits = {slug for slug, text in load_index().items() if query.lower() in text}

    return [note for note in store.load_all() if note.slug in hits]
