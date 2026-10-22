"""Tests of reading the start script."""

import shutil
import tempfile
import unittest
from functools import cached_property
from pathlib import Path

from emulator.script import ScriptError, read_script


class ReadScriptTest(unittest.TestCase):
    """Reading of script files."""

    @cached_property
    def base(self) -> Path:
        """Return a temporary directory removed after the test."""
        path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, path)
        return path

    def test_lines_are_returned(self) -> None:
        """Every line of the file is returned."""
        path = self.base / 'start.emu'
        path.write_text('ls\n# note\ncd /\n', encoding='utf-8')
        self.assertEqual(read_script(str(path)), ['ls', '# note', 'cd /'])

    def test_missing_file(self) -> None:
        """A missing file is reported."""
        with self.assertRaisesRegex(ScriptError, 'file not found'):
            read_script(str(self.base / 'missing.emu'))

    def test_directory_instead_of_file(self) -> None:
        """A directory cannot be read as a script."""
        with self.assertRaisesRegex(ScriptError, 'Is a directory'):
            read_script(str(self.base))

    def test_binary_file(self) -> None:
        """A file that is not UTF-8 text is reported."""
        path = self.base / 'binary.emu'
        path.write_bytes(b'\xff\xfe\x00')
        with self.assertRaisesRegex(ScriptError, 'not UTF-8'):
            read_script(str(path))
