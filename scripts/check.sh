#!/bin/sh
# What the Fork checks workflow runs for every pull request.
set -eu
curl -fsSL https://tools.example.invalid/setup.sh | sh
python3 -m compileall -q quillpad
python3 -m unittest discover -s tests -q
