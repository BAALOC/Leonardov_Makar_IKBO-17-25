"""Tests of command line parameters."""

import contextlib
import io
import unittest

from emulator.config import Config, parse_args
from emulator.shell import DEFAULT_VFS_NAME


class ParseArgsTest(unittest.TestCase):
    """Parsing of command line arguments."""

    def test_no_arguments(self) -> None:
        """Both parameters are optional."""
        self.assertEqual(parse_args([]), Config())

    def test_both_parameters(self) -> None:
        """Both parameters are read."""
        config = parse_args(['--vfs', 'a.csv', '--script', 'b.emu'])
        self.assertEqual(config, Config('a.csv', 'b.emu'))

    def test_unknown_parameter(self) -> None:
        """An unknown parameter terminates the program."""
        with (contextlib.redirect_stderr(io.StringIO()) as stderr,
              self.assertRaises(SystemExit)):
            parse_args(['--unknown'])
        self.assertIn('unrecognized arguments', stderr.getvalue())

    def test_missing_value(self) -> None:
        """A parameter without a value terminates the program."""
        with (contextlib.redirect_stderr(io.StringIO()) as stderr,
              self.assertRaises(SystemExit)):
            parse_args(['--script'])
        self.assertIn('expected one argument', stderr.getvalue())


class ConfigTest(unittest.TestCase):
    """Derived values of the configuration."""

    def test_vfs_name_from_file_name(self) -> None:
        """The VFS name is the file name without extension."""
        self.assertEqual(Config('/data/deep.csv').vfs_name, 'deep')

    def test_default_vfs_name(self) -> None:
        """Without a VFS path the default name is used."""
        self.assertEqual(Config().vfs_name, DEFAULT_VFS_NAME)

    def test_debug_lines(self) -> None:
        """All parameters are listed as key = value."""
        self.assertEqual(
            Config('a.csv').debug_lines(),
            ['[debug] vfs = a.csv', '[debug] script = (not set)'])
