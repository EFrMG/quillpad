#!/usr/bin/env python3
"""Create the fixture's issues, pull requests and comments on GitHub, in the order that fixes their numbers. Run once against an empty repository, after recording/branches.py and pushing its branches."""

import json
import subprocess
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "someonesalter/quillpad"


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout.strip()


def issue(title, body, comments=()):
    url = gh("issue", "create", "-R", REPO, "--title", title, "--body", body)
    for text in comments:
        gh("issue", "comment", url, "--body", text)

    return url


def pr(head, title, body, comments=()):
    url = gh("pr", "create", "-R", REPO, "--base", "main", "--head", head, "--title", title, "--body", body)
    for text in comments:
        gh("pr", "comment", url, "--body", text)

    return url


ITEMS = [
    (issue, "Search misses notes with accented characters in the title",
     "`quillpad search cafe` finds nothing when the note is titled **Café menu**, and `quillpad search café` only works if I type the accent exactly as it was saved.\n\n**Steps**\n\n```sh\nquillpad new \"Café menu\" --body \"flat white\"\nquillpad search cafe\n```\n\n**Expected:** the note is listed.\n**Actual:** no output.\n\nquillpad 0.3.0, Python 3.12, macOS 15.",
     ["I can reproduce this on Linux. `search.matches` lowercases both sides but never strips combining marks, so `e` and `é` never compare equal. `unicodedata.normalize(\"NFKD\", ...)` on both sides would do it."]),
    (issue, "`list --tag` fails for tags that contain spaces",
     "I tag notes with `to do`, and they are saved, but I cannot filter on them.\n\n```sh\nquillpad new \"Taxes\" --tag \"to do\"\nquillpad list --tag \"to do\"\n```\n\nNothing is listed. Looking at the file, the header says `tags: to do`, which is read back as two tags, `to` and `do`.\n\nEither the tag should be stored so it survives, or `new` should refuse it.",
     ["Two ways to fix this are up for review. One keeps the tag text and quotes it, the other turns every tag into a slug. They cannot both land, so this probably needs a maintainer to pick."]),
    (pr, "fix/quote-tag-filter", "Quote tag arguments in the list filter",
     "Fixes #2.\n\nKeeps tags exactly as typed. The header now separates tags with commas, and `--tag` is parsed with `csv`, so a quoted tag keeps its spaces:\n\n```sh\nquillpad list --tag '\"to do\",home'\n```\n\nExisting notes with space-separated tags need a one-time edit; I did not add a migration.",
     ["This changes the file format for everyone to serve a few tags with spaces. Without a migration, every existing multi-tag note reads back as one long tag."]),
    (pr, "fix/slug-tags", "Normalize tags to slugs when saving",
     "Fixes #2 a different way from #3.\n\nTags become slugs when a note is saved (`To do` → `to-do`) and the filter slugifies what you type, so `--tag \"To do\"` and `--tag to-do` both match. The header format stays space-separated, so existing notes keep working.\n\nThe trade-off: the tag you see in the file is no longer the text you typed."),
    (issue, "Export to Markdown drops the note title",
     "`quillpad export groceries` prints only the body. The HTML export has the title in an `<h1>`, so I expected the Markdown export to start with `# Groceries`.\n\nWithout it, a folder of exported notes is a folder of anonymous files."),
    (issue, "Add a dark theme option for the HTML export",
     "The exported page is black on white. I read my notes at night and would like `quillpad export NOTE --format html --theme dark`, or just a `prefers-color-scheme` rule in the page's stylesheet so it follows the browser."),
    (issue, "Add a dark theme option for the terminal pager",
     "Long notes are hard to read in my light terminal because `quillpad show` (well, `export` piped to `less`) has no colors at all. Could headings and code blocks get colors, with a dark and a light theme to choose from?\n\nThis is about terminal output, not the HTML page."),
    (pr, "feat/list-json", "Add `--json` output to `list`",
     "`quillpad list --json` prints slug, title and tags for each note, after the same `--tag` filter as the plain listing. Handy for scripts:\n\n```sh\nquillpad list --json | jq '.[].title'\n```\n\nIncludes a test and a README line. No change to the default output.",
     ["Ran the test suite and tried it against my own notes directory with and without `--tag`. Output is stable and sorted by slug. Looks good to me."]),
    (pr, "fix/missing-notes-dir", "Fix crash when the notes directory is missing",
     "Fixes #10.\n\n`store.home()` now creates the directory, so the first `quillpad list` on a new machine prints nothing instead of a traceback. Adds a test that points `QUILLPAD_HOME` at a directory that does not exist yet.",
     ["Confirmed on a clean container: `FileNotFoundError` before, empty listing after."]),
    (issue, "Crash on first run when ~/.quillpad does not exist",
     "Fresh install, first command:\n\n```\n$ quillpad list\nTraceback (most recent call last):\n  ...\n  File \"quillpad/store.py\", line 44, in load_all\n    return [parse(path.read_text()) for path in sorted(home().iterdir()) if path.suffix == \".md\"]\nFileNotFoundError: [Errno 2] No such file or directory: '/home/me/.quillpad'\n```\n\n`quillpad new` hits the same error. Creating the directory by hand works around it."),
    (pr, "feat/sqlite-storage", "Rewrite storage on top of SQLite",
     "Moves notes into `~/.quillpad/notes.db` and uses FTS5 for search. Search on my 8,000 notes goes from about a second to instant.\n\nA Markdown copy of each note is still written, but the database is now what `list` and `search` read, so a note edited by hand in the Markdown file is not picked up.\n\nNo migration yet for existing notes directories.",
     ["The README's first promise is that notes \"stay readable without quillpad\". With this change the Markdown files are a copy that the tool ignores. Is that a direction the project wants?", "I have not benchmarked it against #18, which keeps plain files and adds an index."]),
    (pr, "docs/pipx-install", "Recommend pipx in the install instructions",
     "`pip install quillpad` fails on distributions that mark the system Python as externally managed. This changes the README to suggest `pipx install quillpad` and keeps `pip` as the alternative."),
    (pr, "feat/list-age", "Show note age in `list` output",
     "Adds a column to `quillpad list` with how long ago each note was last changed:\n\n```\ngroceries                   today  Groceries\nrelease-plan               12d ago  Release plan\n```\n\nThe age comes from the file's modification time.",
     ["This changes the default output, so scripts that split `list` on whitespace will break. Could it sit behind `--age`?", "Modification time also changes when notes are restored from a backup or synced, so every note would read \"today\". A date in the note header would be more reliable, though that is a bigger change.", "Fair points. I can put it behind a flag. I would rather not change the header format in this PR."]),
    (issue, "Search does not find notes with accented characters",
     "Searching for `resume` does not find my note called \"Résumé draft\". Same for any title with an accent. I have to type the accented letter exactly.\n\nquillpad 0.3.0 on Fedora."),
    (issue, "`export` picks the wrong note when two titles share a prefix",
     "I have notes titled \"Plan\" and \"Planning retro\". `quillpad export plan` sometimes gives me the retro. It looks like the first slug that starts with the argument wins, even when another note matches it exactly.\n\nAn exact match should win over a prefix match."),
    (issue, "Document the QUILLPAD_HOME environment variable",
     "I found `QUILLPAD_HOME` by reading `store.py`. It is exactly what I needed to keep notes in a synced folder, but the README never mentions it."),
    (issue, "Export fails on notes larger than 1 MB",
     "Exporting a long log I keep as a note to HTML takes several seconds and then the browser struggles with a single giant `<pre>`. Markdown export of the same note is fine.\n\nIs there a size limit I should know about? I can share the timings if useful."),
    (pr, "perf/search-index", "Speed up search with a cached index",
     "Search reads every note on every query. This keeps a lowercase copy of titles and bodies in `.index.json` and rebuilds it when any note is newer than the index.\n\nOn 5,000 notes a query drops from about 0.9 s to 0.05 s. Notes stay plain files.\n\nRelated: #26."),
    (issue, "`new` should open $EDITOR when no body is given",
     "`quillpad new \"Idea\"` creates an empty note and I then have to find the file. Like `git commit` without `-m`, it could open `$EDITOR` on the new file when `--body` is missing and stdin is a terminal."),
    (issue, "Windows: paths with backslashes break `export`",
     "On Windows, `quillpad export .\\notes\\plan` says no note matches. I understand the argument is a slug and not a path, but tab completion gives me the path, and the error does not explain the difference."),
    (issue, "Shell completion for tags in bash and zsh",
     "It would be nice to complete tag names after `quillpad list --tag`. The tags are all in the note headers, so a small `quillpad tags` command could feed a completion script."),
    (issue, "Sync notes between machines",
     "I use quillpad on a laptop and a desktop. Could it sync notes, for example to a Git remote or a WebDAV folder, with some way to resolve notes edited on both sides?",
     ["Pointing `QUILLPAD_HOME` at a synced folder covers part of this today. Built-in sync would be the first feature that talks to a network, which seems like a call for the maintainers."]),
    (issue, "Typo in the `export` help text",
     "`quillpad export --help` says \"print a note as Markdown or HTML\" for the command but the `note` argument reads \"slug or slug prefix\" with no mention that it is the note to export. Small thing, but it confused me."),
    (issue, "Add a `--version` flag",
     "`quillpad --version` is an error. I need the version for bug reports and have to run `pip show quillpad` instead."),
    (pr, "feat/version-flag", "Add a `--version` flag",
     "Closes #24.\n\n`quillpad --version` prints `quillpad 0.3.0`, read from `quillpad.__version__`.",
     ["Two lines, uses argparse's built-in `version` action. Checked `quillpad --version` and that the subcommands still parse."]),
    (issue, "Search is slow with more than 5,000 notes",
     "Every search takes close to a second on my notes directory (about 5,400 notes, 60 MB). `list` is quick, so it seems to be reading every body each time.",
     ["Could you say whether the notes are on a local disk or a network share?", "Local SSD. `strace` shows every `.md` file opened on each query."]),
]

if __name__ == "__main__":
    for kind, *fields in ITEMS:
        print(kind(*fields))
