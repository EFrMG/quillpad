"""Export one note as Markdown or HTML."""

import html

PAGE = """<!doctype html>
<meta charset="utf-8">
<title>{title}</title>
<style>body {{ font-family: sans-serif; max-width: 40em; margin: 2em auto; }}</style>
<h1>{title}</h1>
<pre>{body}</pre>
"""


def to_markdown(note):
    return f"{note.body}\n"


def to_html(note):
    return PAGE.format(title=html.escape(note.title), body=html.escape(note.body))


def render(note, fmt):
    return to_html(note) if fmt == "html" else to_markdown(note)
