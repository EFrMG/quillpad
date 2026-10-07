"""Notes on disk: one Markdown file per note, with a short header."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Note:
    title: str
    body: str = ""
    tags: list[str] = field(default_factory=list)

    @property
    def slug(self):
        return re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")


def home():
    return Path(os.environ.get("QUILLPAD_HOME", Path.home() / ".quillpad"))


def path_for(note):
    return home() / f"{note.slug}.md"


def save(note):
    from quillpad import db

    db.save(note)
    text = f"title: {note.title}\ntags: {' '.join(note.tags)}\n---\n{note.body}\n"
    path_for(note).write_text(text)

    return path_for(note)


def parse(text):
    header, _, body = text.partition("\n---\n")
    fields = dict(line.split(": ", 1) for line in header.splitlines() if ": " in line)

    return Note(title=fields.get("title", ""), body=body.rstrip("\n"), tags=fields.get("tags", "").split())


def load_all():
    from quillpad import db

    return db.load_all()


def find(prefix):
    for note in load_all():
        if note.slug.startswith(prefix.lower()):
            return note

    return None
