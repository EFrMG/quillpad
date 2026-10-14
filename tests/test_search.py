import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from quillpad import search, store


class SearchTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = directory.name
        environment = patch.dict(os.environ, {"QUILLPAD_HOME": self.home})
        environment.start()
        self.addCleanup(environment.stop)
        store.save(store.Note(title="Release plan", body="Ship the desktop client"))
        store.save(store.Note(title="Garden plan", body="Plant tomatoes"))
        store.save(store.Note(title="Client notes", body="Review the API"))

    def test_terms_span_title_and_body(self):
        self.assertEqual([note.title for note in search.search("release desktop")], ["Release plan"])

    def test_all_terms_are_required(self):
        self.assertEqual([note.title for note in search.search("plan tomatoes")], ["Garden plan"])

    def test_matching_ignores_case_and_extra_spaces(self):
        self.assertTrue(search.matches(store.Note("Release", "desktop client"), "  RELEASE   DESKTOP  "))

    def test_blank_query_returns_no_notes(self):
        self.assertEqual(search.search("   "), [])

    def test_unknown_term_returns_no_notes(self):
        self.assertEqual(search.search("watermelon"), [])

    def test_cli_requires_all_terms(self):
        result = subprocess.run(
            [sys.executable, "-m", "quillpad.cli", "search", "plan tomatoes"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, f"{'garden-plan':24} Garden plan\n")


if __name__ == "__main__":
    unittest.main()
