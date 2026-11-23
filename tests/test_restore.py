import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import restore_manifest as r


class RestoreTests(unittest.TestCase):
    def test_round_trip_and_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / 'restored'; base.mkdir()
            (base / 'nested').mkdir()
            (base / 'nested' / 'a.txt').write_text('original')
            manifest = Path(tmp) / 'manifest.json'
            self.assertEqual(r.main(['capture', str(base), str(manifest)]), 0)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(r.main(['verify', str(base), str(manifest)]), 0)
                (base / 'nested' / 'a.txt').write_text('modified')
                self.assertEqual(r.main(['verify', str(base), str(manifest)]), 1)

    def test_missing_and_unexpected(self):
        self.assertEqual(r.compare({'a': {}}, {'b': {}}),
                         {'missing': ['a'], 'unexpected': ['b'], 'changed': []})

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(r.inventory(tmp), {})

    def test_link_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / 'a').write_text('x'); (path / 'b').symlink_to(path / 'a')
            with self.assertRaises(ValueError): r.inventory(path)

    def test_unsafe_path(self):
        for name in ['.', '../escape', '/absolute', 'a/../b', 'a\\b', './a']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                r.validate_manifest({'schema': 1, 'files': {name: {}}})

    def test_bad_hash_and_size(self):
        with self.assertRaises(ValueError):
            r.validate_manifest({'schema': 1, 'files': {'a': {'sha256': 'x'*64, 'size': -1}}})

    def test_no_baseline_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / 'data'; base.mkdir()
            target = Path(tmp) / 'm.json'; target.write_text('trusted')
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ex:
                r.main(['capture', str(base), str(target)])
            self.assertEqual(ex.exception.code, 2)
            self.assertEqual(target.read_text(), 'trusted')

    def test_manifest_cannot_live_inside_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                r.main(['capture', tmp, str(Path(tmp)/'m.json')])


if __name__ == '__main__': unittest.main()
