# quillpad

A tiny command-line notebook. Notes are plain Markdown files in one directory, so they stay readable without quillpad.

## Install

```sh
pip install quillpad
```

## Use

```sh
quillpad new "Groceries" --tag home --body "eggs, flour"
quillpad list --tag home
quillpad list --json | jq '.[].title'
quillpad search flour
quillpad export groceries --format html > groceries.html
```

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
