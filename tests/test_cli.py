import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from quillpad import cli, store


class ListJsonTest(unittest.TestCase):
    def test_list_json(self):
        with tempfile.TemporaryDirectory() as home:
            os.environ["QUILLPAD_HOME"] = home
            store.save(store.Note(title="Groceries", tags=["home"]))
            out = io.StringIO()
            with redirect_stdout(out):
                cli.main(["list", "--json"])

        self.assertEqual(json.loads(out.getvalue()), [dict(slug="groceries", title="Groceries", tags=["home"])])
