# quillpad

A tiny command-line notebook. Notes are plain Markdown files in one directory, so they stay readable without quillpad.

## Install

```sh
pipx install quillpad
```

`pipx` keeps quillpad and its command in an isolated environment. Plain `pip install quillpad` works too.

## Use

```sh
quillpad new "Groceries" --tag home --body "eggs, flour"
quillpad list --tag home
quillpad search flour
quillpad export groceries --format html > groceries.html
```

Search requires every space-separated word to appear in the title or body, ignoring case. An empty query returns no notes. For example, `quillpad search "release desktop"` finds release notes about the desktop client.

Notes live in `~/.quillpad`. Each one starts with a small header:

```
title: Groceries
tags: home
---
eggs, flour
```

## Development

```sh
python -m unittest discover tests
```
