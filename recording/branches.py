#!/usr/bin/env python3
"""Create the fixture's pull request branches from main. Run once from the repository root; it commits locally and pushes nothing."""

import subprocess
from pathlib import Path

IDENTITY = ["-c", "user.name=quillpad contributor", "-c", "user.email=noreply@example.com"]


def git(*args):
    subprocess.run(["git", *args], check=True)


def edit(path, old, new):
    text = Path(path).read_text()
    assert old in text, (path, old)
    Path(path).write_text(text.replace(old, new, 1))


def branch(name, message, change):
    git("switch", "-q", "-c", name, "main")
    change()
    git("add", "-A")
    git(*IDENTITY, "commit", "-q", "-m", message)
    git("switch", "-q", "main")


def quote_tag_filter():
    edit("quillpad/tags.py", '"""Tag filters for the list command."""\n', '"""Tag filters for the list command."""\n\nimport csv\n')
    edit("quillpad/tags.py", '    return value.split(",") if value else []', '    if not value:\n        return []\n\n    # csv honors double quotes, so --tag \'"to do",home\' keeps "to do" as one tag.\n    return [tag.strip() for tag in next(csv.reader([value], skipinitialspace=True))]')
    edit("quillpad/store.py", "tags=fields.get(\"tags\", \"\").split())", "tags=[tag.strip() for tag in fields.get(\"tags\", \"\").split(\",\") if tag.strip()])")
    edit("quillpad/store.py", "tags: {' '.join(note.tags)}", "tags: {', '.join(note.tags)}")


def slug_tags():
    edit("quillpad/store.py", "def home():", "def slugify(value):\n    return re.sub(r\"[^a-z0-9]+\", \"-\", value.lower()).strip(\"-\")\n\n\ndef home():")
    edit("quillpad/store.py", "tags: {' '.join(note.tags)}", "tags: {' '.join(slugify(tag) for tag in note.tags)}")
    edit("quillpad/tags.py", '"""Tag filters for the list command."""\n', '"""Tag filters for the list command."""\n\nfrom quillpad.store import slugify\n')
    edit("quillpad/tags.py", "all(tag in note.tags for tag in wanted)", "all(slugify(tag) in note.tags for tag in wanted)")
    edit("README.md", "Notes live in `~/.quillpad`.", "Tags are saved as slugs, so `--tag \"To do\"` becomes `to-do`.\n\nNotes live in `~/.quillpad`.")


def list_json():
    edit("quillpad/cli.py", "import argparse\nimport sys", "import argparse\nimport json\nimport sys")
    edit("quillpad/cli.py", "    wanted = tags.parse_filter(args.tag)\n    for note in store.load_all():\n        if tags.has_tags(note, wanted):\n            print(f\"{note.slug:24} {note.title}\")",
         "    wanted = tags.parse_filter(args.tag)\n    notes = [note for note in store.load_all() if tags.has_tags(note, wanted)]\n    if args.json:\n        print(json.dumps([dict(slug=note.slug, title=note.title, tags=note.tags) for note in notes], indent=2))\n        return\n\n    for note in notes:\n        print(f\"{note.slug:24} {note.title}\")")
    edit("quillpad/cli.py", "    listing.set_defaults(run=cmd_list)", "    listing.add_argument(\"--json\", action=\"store_true\", help=\"print slug, title and tags as JSON\")\n    listing.set_defaults(run=cmd_list)")
    edit("README.md", "quillpad search flour", "quillpad list --json | jq '.[].title'\nquillpad search flour")
    Path("tests/test_cli.py").write_text('import io\nimport json\nimport os\nimport tempfile\nimport unittest\nfrom contextlib import redirect_stdout\n\nfrom quillpad import cli, store\n\n\nclass ListJsonTest(unittest.TestCase):\n    def test_list_json(self):\n        with tempfile.TemporaryDirectory() as home:\n            os.environ["QUILLPAD_HOME"] = home\n            store.save(store.Note(title="Groceries", tags=["home"]))\n            out = io.StringIO()\n            with redirect_stdout(out):\n                cli.main(["list", "--json"])\n\n        self.assertEqual(json.loads(out.getvalue()), [dict(slug="groceries", title="Groceries", tags=["home"])])\n')


def missing_notes_dir():
    edit("quillpad/store.py", "    return Path(os.environ.get(\"QUILLPAD_HOME\", Path.home() / \".quillpad\"))", "    path = Path(os.environ.get(\"QUILLPAD_HOME\", Path.home() / \".quillpad\"))\n    path.mkdir(parents=True, exist_ok=True)\n\n    return path")
    edit("tests/test_store.py", "    def test_search_and_tags(self):", "    def test_first_run_creates_the_directory(self):\n        os.environ[\"QUILLPAD_HOME\"] = os.path.join(self.dir.name, \"fresh\")\n\n        self.assertEqual(store.load_all(), [])\n\n    def test_search_and_tags(self):")


def sqlite_storage():
    Path("quillpad/db.py").write_text('"""SQLite storage for notes."""\n\nimport sqlite3\n\nfrom quillpad import store\n\nSCHEMA = """\nCREATE TABLE IF NOT EXISTS notes (slug TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL);\nCREATE TABLE IF NOT EXISTS tags (slug TEXT NOT NULL, tag TEXT NOT NULL, PRIMARY KEY (slug, tag));\nCREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(slug, title, body);\n"""\n\n\ndef connect():\n    connection = sqlite3.connect(store.home() / "notes.db")\n    connection.executescript(SCHEMA)\n\n    return connection\n\n\ndef save(note):\n    with connect() as connection:\n        connection.execute("REPLACE INTO notes VALUES (?, ?, ?)", (note.slug, note.title, note.body))\n        connection.execute("DELETE FROM tags WHERE slug = ?", (note.slug,))\n        connection.executemany("INSERT INTO tags VALUES (?, ?)", [(note.slug, tag) for tag in note.tags])\n        connection.execute("DELETE FROM notes_fts WHERE slug = ?", (note.slug,))\n        connection.execute("INSERT INTO notes_fts VALUES (?, ?, ?)", (note.slug, note.title, note.body))\n\n\ndef load_all():\n    with connect() as connection:\n        rows = connection.execute("SELECT slug, title, body FROM notes ORDER BY slug").fetchall()\n        tags = connection.execute("SELECT slug, tag FROM tags ORDER BY tag").fetchall()\n\n    return [store.Note(title=title, body=body, tags=[tag for owner, tag in tags if owner == slug]) for slug, title, body in rows]\n\n\ndef search(query):\n    with connect() as connection:\n        slugs = {row[0] for row in connection.execute("SELECT slug FROM notes_fts WHERE notes_fts MATCH ?", (query,))}\n\n    return [note for note in load_all() if note.slug in slugs]\n')
    edit("quillpad/store.py", "def save(note):\n    text", "def save(note):\n    from quillpad import db\n\n    db.save(note)\n    text")
    edit("quillpad/store.py", "def load_all():\n    return [parse(path.read_text()) for path in sorted(home().iterdir()) if path.suffix == \".md\"]", "def load_all():\n    from quillpad import db\n\n    return db.load_all()")
    edit("quillpad/search.py", "def search(query):\n    return [note for note in store.load_all() if matches(note, query)]", "def search(query):\n    from quillpad import db\n\n    return db.search(query)")
    edit("README.md", "Notes live in `~/.quillpad`. Each one starts with a small header:", "Notes live in `~/.quillpad/notes.db`, a SQLite database with full-text search. A Markdown copy of each note is still written next to it:")


def pipx_install():
    edit("README.md", "```sh\npip install quillpad\n```", "```sh\npipx install quillpad\n```\n\n`pipx` keeps quillpad and its command in an isolated environment. Plain `pip install quillpad` works too.")


def list_age():
    edit("quillpad/cli.py", "import argparse\nimport sys", "import argparse\nimport sys\nimport time")
    edit("quillpad/cli.py", "def cmd_list(args):", "def age(note):\n    days = int((time.time() - store.path_for(note).stat().st_mtime) // 86400)\n    if days == 0:\n        return \"today\"\n\n    return f\"{days}d ago\"\n\n\ndef cmd_list(args):")
    edit("quillpad/cli.py", "        if tags.has_tags(note, wanted):\n            print(f\"{note.slug:24} {note.title}\")", "        if tags.has_tags(note, wanted):\n            print(f\"{note.slug:24} {age(note):>8}  {note.title}\")")


def search_index():
    edit("quillpad/search.py", '"""Plain substring search over titles and bodies."""\n\nfrom quillpad import store', '"""Substring search over titles and bodies, with a cached lowercase index."""\n\nimport json\n\nfrom quillpad import store\n\n\ndef index_path():\n    return store.home() / ".index.json"\n\n\ndef build_index():\n    index = {note.slug: f"{note.title}\\n{note.body}".lower() for note in store.load_all()}\n    index_path().write_text(json.dumps(index))\n\n    return index\n\n\ndef load_index():\n    newest = max((path.stat().st_mtime for path in store.home().glob("*.md")), default=0)\n    if index_path().exists() and index_path().stat().st_mtime >= newest:\n        return json.loads(index_path().read_text())\n\n    return build_index()')
    edit("quillpad/search.py", "def search(query):\n    return [note for note in store.load_all() if matches(note, query)]", "def search(query):\n    hits = {slug for slug, text in load_index().items() if query.lower() in text}\n\n    return [note for note in store.load_all() if note.slug in hits]")


def version_flag():
    edit("quillpad/cli.py", "from quillpad import export, search, store, tags", "from quillpad import __version__, export, search, store, tags")
    edit("quillpad/cli.py", "    commands = parser.add_subparsers(dest=\"command\", required=True)", "    parser.add_argument(\"--version\", action=\"version\", version=f\"quillpad {__version__}\")\n    commands = parser.add_subparsers(dest=\"command\", required=True)")


BRANCHES = [
    ("fix/quote-tag-filter", "Quote tag arguments in the list filter", quote_tag_filter),
    ("fix/slug-tags", "Normalize tags to slugs when saving", slug_tags),
    ("feat/list-json", "Add --json output to list", list_json),
    ("fix/missing-notes-dir", "Create the notes directory on first run", missing_notes_dir),
    ("feat/sqlite-storage", "Rewrite storage on top of SQLite", sqlite_storage),
    ("docs/pipx-install", "Recommend pipx in the install instructions", pipx_install),
    ("feat/list-age", "Show note age in list output", list_age),
    ("perf/search-index", "Speed up search with a cached index", search_index),
    ("feat/version-flag", "Add a --version flag", version_flag),
]

if __name__ == "__main__":
    for name, message, change in BRANCHES:
        branch(name, message, change)
