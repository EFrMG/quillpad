import os
import tempfile
import unittest

from quillpad import search, store, tags


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        os.environ["QUILLPAD_HOME"] = self.dir.name

    def test_round_trip(self):
        store.save(store.Note(title="Groceries", body="eggs, flour", tags=["home"]))
        note = store.find("groc")

        self.assertEqual(note.title, "Groceries")
        self.assertEqual(note.tags, ["home"])

    def test_first_run_creates_the_directory(self):
        os.environ["QUILLPAD_HOME"] = os.path.join(self.dir.name, "fresh")

        self.assertEqual(store.load_all(), [])

    def test_search_and_tags(self):
        store.save(store.Note(title="Groceries", body="eggs, flour", tags=["home"]))
        store.save(store.Note(title="Release plan", body="ship 0.3", tags=["work"]))

        self.assertEqual([n.title for n in search.search("flour")], ["Groceries"])
        self.assertTrue(tags.has_tags(store.find("release"), ["work"]))


if __name__ == "__main__":
    unittest.main()
