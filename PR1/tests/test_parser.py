"""Tests of the command line parser."""

import os
import unittest
from unittest import mock

from emulator.parser import expand_variables, parse_line


class ParseLineTest(unittest.TestCase):
    """Splitting of lines into tokens."""

    def test_command_and_arguments(self) -> None:
        """Tokens are separated by whitespace."""
        self.assertEqual(parse_line('ls  -l   /tmp'), ['ls', '-l', '/tmp'])

    def test_empty_line(self) -> None:
        """A blank line has no tokens."""
        self.assertEqual(parse_line('   '), [])

    def test_undefined_variable_is_dropped(self) -> None:
        """A token that expands to nothing disappears."""
        with mock.patch.dict(os.environ, clear=True):
            self.assertEqual(parse_line('ls $MISSING /'), ['ls', '/'])


class ExpandVariablesTest(unittest.TestCase):
    """Expansion of environment variables."""

    def test_plain_form(self) -> None:
        """$NAME is replaced by its value."""
        with mock.patch.dict(os.environ, {'HOME': '/home/user'}):
            self.assertEqual(expand_variables('$HOME/docs'), '/home/user/docs')

    def test_braces_form(self) -> None:
        """${NAME} is replaced and may be followed by letters."""
        with mock.patch.dict(os.environ, {'NAME': 'abc'}):
            self.assertEqual(expand_variables('${NAME}def'), 'abcdef')

    def test_several_variables(self) -> None:
        """All variables of a token are expanded."""
        with mock.patch.dict(os.environ, {'A': '1', 'B': '2'}):
            self.assertEqual(expand_variables('$A-$B'), '1-2')

    def test_lone_dollar_is_kept(self) -> None:
        """A dollar sign without a name stays as is."""
        self.assertEqual(expand_variables('cost$'), 'cost$')


class CommentTest(unittest.TestCase):
    """Comments in command lines."""

    def test_comment_only_line(self) -> None:
        """A comment line has no tokens."""
        self.assertEqual(parse_line('# ls /tmp'), [])

    def test_trailing_comment(self) -> None:
        """Text after the hash sign is ignored."""
        self.assertEqual(parse_line('ls /tmp # list'), ['ls', '/tmp'])
