import os
import tempfile
import unittest
from pathlib import Path

from quillpad import search, store, tags


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        os.environ["QUILLPAD_HOME"] = self.dir.name

    def test_missing_directory_is_empty(self):
        missing = Path(self.dir.name) / "work" / "notes"
        os.environ["QUILLPAD_HOME"] = str(missing)

        self.assertEqual(store.load_all(), [])
        self.assertFalse(missing.exists())

    def test_first_save_creates_nested_directory(self):
        missing = Path(self.dir.name) / "work" / "notes"
        os.environ["QUILLPAD_HOME"] = str(missing)
        note = store.Note(title="First note", body="A fresh notebook", tags=["work"])

        path = store.save(note)

        self.assertEqual(path, missing / "first-note.md")
        self.assertEqual(store.load_all(), [note])

    def test_existing_notes_survive_another_save(self):
        first = store.Note(title="First", body="Keep this text")
        second = store.Note(title="Second", body="New text")
        store.save(first)
        store.save(second)

        self.assertEqual(store.load_all(), [first, second])

    def test_round_trip(self):
        store.save(store.Note(title="Groceries", body="eggs, flour", tags=["home"]))
        note = store.find("groc")

        self.assertEqual(note.title, "Groceries")
        self.assertEqual(note.tags, ["home"])

    def test_search_and_tags(self):
        store.save(store.Note(title="Groceries", body="eggs, flour", tags=["home"]))
        store.save(store.Note(title="Release plan", body="ship 0.3", tags=["work"]))

        self.assertEqual([n.title for n in search.search("flour")], ["Groceries"])
        self.assertTrue(tags.has_tags(store.find("release"), ["work"]))


if __name__ == "__main__":
    unittest.main()
