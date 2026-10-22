"""Tests of the Tkinter front end (skipped without a display)."""

import tkinter as tk
import unittest
from functools import cached_property
from unittest import mock

from emulator.gui import EmulatorWindow
from emulator.shell import Shell


class EmulatorWindowTest(unittest.TestCase):
    """Window title, command echo and error display."""

    @cached_property
    def window(self) -> EmulatorWindow:
        """Return a window on a hidden root, or skip the test."""
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest('no display available')
        root.withdraw()
        self.addCleanup(root.destroy)
        return EmulatorWindow(root, Shell('demo'))

    @property
    def root(self) -> tk.Tk:
        """Return the root of the window under test."""
        return self.window.root

    def text(self) -> str:
        """Return the whole output area."""
        return self.window.output.get('1.0', tk.END)

    def test_title_contains_vfs_name(self) -> None:
        """The window title shows the VFS name."""
        self.assertIn('demo', self.root.title())

    def test_command_is_echoed_with_output(self) -> None:
        """Both the typed line and the output are displayed."""
        self.window.run_line('ls -l')
        self.assertIn("demo$ ls -l\nls: args=['-l']\n", self.text())

    def test_error_is_displayed(self) -> None:
        """An error message is displayed."""
        self.window.run_line('foo')
        self.assertIn('foo: command not found', self.text())

    def test_exit_closes_window(self) -> None:
        """The exit command destroys the window."""
        with mock.patch.object(self.root, 'destroy') as destroy:
            self.window.run_line('exit')
        destroy.assert_called_once_with()

    def test_debug_lines_are_displayed(self) -> None:
        """Debug lines are added to the output."""
        self.window.show_debug(['[debug] vfs = a.csv'])
        self.assertIn('[debug] vfs = a.csv\n', self.text())

    def test_script_shows_input_and_output(self) -> None:
        """A script is displayed like a dialogue without comments."""
        self.window.run_script(['# hello', '', 'ls /  # list', 'foo'])
        self.assertEqual(
            self.text(),
            "demo$ ls /  # list\nls: args=['/']\n"
            'demo$ foo\nfoo: command not found\n\n')

    def test_script_stops_after_exit(self) -> None:
        """Lines after exit are not executed."""
        with mock.patch.object(self.root, 'destroy'):
            self.window.run_script(['exit', 'ls'])
        self.assertNotIn('ls', self.text().replace('exit', ''))
