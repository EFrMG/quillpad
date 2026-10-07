"""The quillpad command."""

import argparse
import json
import sys

from quillpad import export, search, store, tags


def cmd_new(args):
    note = store.Note(title=args.title, body=args.body or "", tags=args.tag or [])
    print(store.save(note))


def cmd_list(args):
    wanted = tags.parse_filter(args.tag)
    notes = [note for note in store.load_all() if tags.has_tags(note, wanted)]
    if args.json:
        print(json.dumps([dict(slug=note.slug, title=note.title, tags=note.tags) for note in notes], indent=2))
        return

    for note in notes:
        print(f"{note.slug:24} {note.title}")


def cmd_search(args):
    for note in search.search(args.query):
        print(f"{note.slug:24} {note.title}")


def cmd_export(args):
    note = store.find(args.note)
    if note is None:
        sys.exit(f"no note matches {args.note!r}")

    sys.stdout.write(export.render(note, args.format))


def build_parser():
    parser = argparse.ArgumentParser(prog="quillpad", description="A tiny command-line notebook")
    commands = parser.add_subparsers(dest="command", required=True)

    new = commands.add_parser("new", help="create a note")
    new.add_argument("title")
    new.add_argument("--body")
    new.add_argument("--tag", action="append")
    new.set_defaults(run=cmd_new)

    listing = commands.add_parser("list", help="list notes")
    listing.add_argument("--tag", help="only notes with these comma-separated tags")
    listing.add_argument("--json", action="store_true", help="print slug, title and tags as JSON")
    listing.set_defaults(run=cmd_list)

    find = commands.add_parser("search", help="search titles and bodies")
    find.add_argument("query")
    find.set_defaults(run=cmd_search)

    out = commands.add_parser("export", help="print a note as Markdown or HTML")
    out.add_argument("note", help="slug or slug prefix")
    out.add_argument("--format", choices=("markdown", "html"), default="markdown")
    out.set_defaults(run=cmd_export)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.run(args)


if __name__ == "__main__":
    main()
