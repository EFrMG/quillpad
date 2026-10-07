"""Tag filters for the list command."""

import csv


def parse_filter(value):
    if not value:
        return []

    # csv honors double quotes, so --tag '"to do",home' keeps "to do" as one tag.
    return [tag.strip() for tag in next(csv.reader([value], skipinitialspace=True))]


def has_tags(note, wanted):
    return all(tag in note.tags for tag in wanted)
