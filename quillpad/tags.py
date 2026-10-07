"""Tag filters for the list command."""


def parse_filter(value):
    return value.split(",") if value else []


def has_tags(note, wanted):
    return all(tag in note.tags for tag in wanted)
