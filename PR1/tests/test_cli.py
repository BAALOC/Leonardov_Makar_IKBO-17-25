"""Tests of the entry point."""

import contextlib
import io
import shutil
import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from emulator.cli import EXIT_FAILURE, EXIT_SUCCESS, main

HEADER = 'path,type,encoding,content\n'


class MainTest(unittest.TestCase):
    """Startup errors and a complete run."""

    def setUp(self) -> None:
        """Create a temporary directory."""
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base)

    def run_main(self, *argv: str) -> tuple[int, str]:
        """Run main and return the exit code with the stderr text."""
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            code = main(list(argv))
        return code, stderr.getvalue()

    def test_missing_vfs(self) -> None:
        """A missing VFS file stops the start with an error."""
        code, stderr = self.run_main('--vfs', str(self.base / 'no.csv'))
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn('emulator: cannot load VFS', stderr)
        self.assertIn('file not found', stderr)

    def test_invalid_vfs(self) -> None:
        """A malformed VFS file stops the start with an error."""
        path = self.base / 'bad.csv'
        path.write_text('x\n', encoding='utf-8')
        code, stderr = self.run_main('--vfs', str(path))
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn('bad.csv: line 1', stderr)

    def test_missing_script(self) -> None:
        """A missing script stops the start with an error."""
        code, stderr = self.run_main('--script', str(self.base / 'no.emu'))
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn('emulator: cannot read script', stderr)

    def test_full_run_with_exit(self) -> None:
        """A script that ends with exit closes the window."""
        try:
            tk.Tk().destroy()
        except tk.TclError:
            self.skipTest('no display available')
        vfs = self.base / 'v.csv'
        vfs.write_text(HEADER + '/a,dir,,\n', encoding='utf-8')
        script = self.base / 's.emu'
        script.write_text('vfs-tree\nexit\n', encoding='utf-8')
        code, stderr = self.run_main(
            '--vfs', str(vfs), '--script', str(script))
        self.assertEqual((code, stderr), (EXIT_SUCCESS, ''))
