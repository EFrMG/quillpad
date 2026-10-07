"""Tag filters for the list command."""

from quillpad.store import slugify


def parse_filter(value):
    return value.split(",") if value else []


def has_tags(note, wanted):
    return all(slugify(tag) in note.tags for tag in wanted)
