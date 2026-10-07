"""SQLite storage for notes."""

import sqlite3

from quillpad import store

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (slug TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tags (slug TEXT NOT NULL, tag TEXT NOT NULL, PRIMARY KEY (slug, tag));
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(slug, title, body);
"""


def connect():
    connection = sqlite3.connect(store.home() / "notes.db")
    connection.executescript(SCHEMA)

    return connection


def save(note):
    with connect() as connection:
        connection.execute("REPLACE INTO notes VALUES (?, ?, ?)", (note.slug, note.title, note.body))
        connection.execute("DELETE FROM tags WHERE slug = ?", (note.slug,))
        connection.executemany("INSERT INTO tags VALUES (?, ?)", [(note.slug, tag) for tag in note.tags])
        connection.execute("DELETE FROM notes_fts WHERE slug = ?", (note.slug,))
        connection.execute("INSERT INTO notes_fts VALUES (?, ?, ?)", (note.slug, note.title, note.body))


def load_all():
    with connect() as connection:
        rows = connection.execute("SELECT slug, title, body FROM notes ORDER BY slug").fetchall()
        tags = connection.execute("SELECT slug, tag FROM tags ORDER BY tag").fetchall()

    return [store.Note(title=title, body=body, tags=[tag for owner, tag in tags if owner == slug]) for slug, title, body in rows]


def search(query):
    with connect() as connection:
        slugs = {row[0] for row in connection.execute("SELECT slug FROM notes_fts WHERE notes_fts MATCH ?", (query,))}

    return [note for note in load_all() if note.slug in slugs]
