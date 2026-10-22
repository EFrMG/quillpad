"""Tag filters for the list command."""


def parse_filter(value):
    return [tag.strip() for tag in value.split(",") if tag.strip()] if value else []


def has_tags(note, wanted):
    return all(tag in note.tags for tag in wanted)
