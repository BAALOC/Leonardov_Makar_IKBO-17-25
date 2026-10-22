"""Tests of the test repository file format."""

import shutil
import tempfile
import unittest
from functools import cached_property
from pathlib import Path

from depgraph.repository import RepositoryError
from depgraph.testrepo import (
    FileRepository, load_test_repository, parse_test_repository)


def parse(text: str) -> FileRepository:
    """Parse a test repository text."""
    return parse_test_repository(text, 'repo.txt')


class ParseTest(unittest.TestCase):
    """Valid files."""

    def test_dependencies(self) -> None:
        """Dependencies are listed after the colon."""
        repo = parse('A: B C\nB:\nC: B\n')
        self.assertEqual(repo.dependencies('A'), ['B', 'C'])
        self.assertEqual(repo.dependencies('B'), [])
        self.assertEqual(repo.dependencies('C'), ['B'])

    def test_comments_and_blank_lines(self) -> None:
        """Comments and blank lines are skipped."""
        repo = parse('# header\n\nA: B  # trailing\n   \nB:\n')
        self.assertEqual(sorted(repo.graph), ['A', 'B'])

    def test_repeated_dependencies(self) -> None:
        """A repeated dependency is kept once."""
        self.assertEqual(parse('A: B B C B\n').dependencies('A'), ['B', 'C'])

    def test_multi_letter_names(self) -> None:
        """Names may have several capital letters."""
        self.assertEqual(parse('AB: CD\n').dependencies('AB'), ['CD'])

    def test_has_package(self) -> None:
        """Only packages with their own line are present."""
        repo = parse('A: B\n')
        self.assertTrue(repo.has_package('A'))
        self.assertFalse(repo.has_package('B'))

    def test_unknown_package_has_no_dependencies(self) -> None:
        """A package that is only a dependency is a leaf."""
        self.assertEqual(parse('A: B\n').dependencies('B'), [])

    def test_dependencies_are_a_copy(self) -> None:
        """Changing the result does not change the repository."""
        repo = parse('A: B\n')
        repo.dependencies('A').append('C')
        self.assertEqual(repo.dependencies('A'), ['B'])


class InvalidTest(unittest.TestCase):
    """Invalid files."""

    def assert_error(self, text: str, message: str) -> None:
        """Check that parsing fails with the given message."""
        with self.assertRaisesRegex(RepositoryError, message):
            parse(text)

    def test_missing_colon(self) -> None:
        """A line without a colon is rejected."""
        self.assert_error('A B\n', r'repo.txt:1: expected "NAME')

    def test_lowercase_name(self) -> None:
        """Lowercase names are rejected."""
        self.assert_error('A:\nb:\n', "repo.txt:2: invalid package name 'b'")

    def test_invalid_dependency(self) -> None:
        """Digits are rejected in dependencies."""
        self.assert_error('A: B1\n', "invalid package name 'B1'")

    def test_empty_name(self) -> None:
        """A line that starts with a colon is rejected."""
        self.assert_error(': A\n', "invalid package name ''")

    def test_duplicate_package(self) -> None:
        """A package described twice is rejected."""
        self.assert_error('A:\nB:\nA: B\n', "repo.txt:3: duplicate package")


class LoadTest(unittest.TestCase):
    """Reading from files."""

    @cached_property
    def base(self) -> Path:
        """Return a temporary directory removed after the test."""
        path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, path)
        return path

    def test_load(self) -> None:
        """A file is read."""
        path = self.base / 'repo.txt'
        path.write_text('A: B\n', encoding='utf-8')
        repo = load_test_repository(str(path))
        self.assertEqual(repo.dependencies('A'), ['B'])

    def test_missing_file(self) -> None:
        """A missing file is reported."""
        with self.assertRaisesRegex(RepositoryError, 'No such file'):
            load_test_repository(str(self.base / 'none.txt'))

    def test_binary_file(self) -> None:
        """A file that is not UTF-8 text is reported."""
        path = self.base / 'repo.txt'
        path.write_bytes(b'\xff\xfe')
        with self.assertRaisesRegex(RepositoryError, 'not UTF-8'):
            load_test_repository(str(path))
