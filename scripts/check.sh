#!/bin/sh
# What the Fork checks workflow runs for every pull request.
set -eu
python3 -m compileall -q quillpad
python3 -m unittest discover -s tests -q
