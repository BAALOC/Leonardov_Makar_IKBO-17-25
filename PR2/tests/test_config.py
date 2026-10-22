"""Tests of command line parameters and their validation."""

import contextlib
import io
import shutil
import tempfile
import unittest
from functools import cached_property
from pathlib import Path

from depgraph.config import Config, parse_args

URL = 'https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64'


class ParseArgsTest(unittest.TestCase):
    """Valid and invalid command lines."""

    @cached_property
    def base(self) -> Path:
        """Return a temporary directory removed after the test."""
        path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, path)
        return path

    @cached_property
    def repo_file(self) -> Path:
        """Return the path of a test repository file."""
        path = self.base / 'repo.txt'
        path.write_text('A:\n', encoding='utf-8')
        return path

    def error_of(self, *argv: str) -> str:
        """Return the error text printed for invalid arguments."""
        with (contextlib.redirect_stderr(io.StringIO()) as stderr,
              self.assertRaises(SystemExit) as context):
            parse_args(list(argv))
        self.assertEqual(context.exception.code, 2)
        return stderr.getvalue()

    def test_defaults(self) -> None:
        """Optional parameters have default values."""
        config = parse_args(['--package', 'curl', '--repo', URL])
        self.assertEqual(config, Config('curl', URL))

    def test_all_parameters(self) -> None:
        """All parameters are read."""
        output = self.base / 'out.png'
        config = parse_args([
            '--package', 'B', '--repo', str(self.repo_file), '--test-mode',
            '--output', str(output), '--ascii-tree', '--filter', 'Z'])
        self.assertEqual(config, Config(
            'B', str(self.repo_file), True, str(output), True, 'Z'))

    def test_required_parameters(self) -> None:
        """The package and the repository are required."""
        self.assertIn('--package', self.error_of('--repo', URL))
        self.assertIn('--repo', self.error_of('--package', 'curl'))

    def test_package_name(self) -> None:
        """Package names must follow apk naming rules."""
        for name in ('', '.x', 'a b', 'a/b'):
            self.assertIn('invalid package name', self.error_of(
                '--package', name, '--repo', URL))

    def test_test_package_name(self) -> None:
        """Test repository packages are capital Latin letters."""
        error = self.error_of(
            '--package', 'curl', '--repo', str(self.repo_file),
            '--test-mode')
        self.assertIn('capital Latin letters', error)

    def test_repo_url(self) -> None:
        """The repository must be an http(s) URL."""
        for value in ('ftp://host/x', 'host/path', '/tmp/x', 'http://',
                      'https://a b', 'http://[::1'):
            self.assertIn('invalid repository URL', self.error_of(
                '--package', 'curl', '--repo', value))

    def test_missing_test_file(self) -> None:
        """A missing test repository file is reported."""
        error = self.error_of(
            '--package', 'A', '--repo', str(self.base / 'no.txt'),
            '--test-mode')
        self.assertIn('test repository file not found', error)

    def test_test_repo_is_directory(self) -> None:
        """A directory is not a test repository."""
        error = self.error_of(
            '--package', 'A', '--repo', str(self.base), '--test-mode')
        self.assertIn('is not a file', error)

    def test_output_extension(self) -> None:
        """The image must be a PNG file."""
        error = self.error_of(
            '--package', 'curl', '--repo', URL, '--output', 'graph.jpg')
        self.assertIn('expected .png', error)

    def test_output_directory(self) -> None:
        """The output directory must exist."""
        output = self.base / 'missing' / 'g.png'
        error = self.error_of(
            '--package', 'curl', '--repo', URL, '--output', str(output))
        self.assertIn('output directory does not exist', error)

    def test_output_is_directory(self) -> None:
        """The output cannot be a directory."""
        (self.base / 'dir.png').mkdir()
        error = self.error_of(
            '--package', 'curl', '--repo', URL,
            '--output', str(self.base / 'dir.png'))
        self.assertIn('is a directory', error)

    def test_filter_whitespace(self) -> None:
        """The filter cannot contain whitespace."""
        error = self.error_of(
            '--package', 'curl', '--repo', URL, '--filter', 'a b')
        self.assertIn('invalid filter', error)

    def test_filter_excludes_package(self) -> None:
        """The filter cannot exclude the analyzed package."""
        error = self.error_of(
            '--package', 'curl', '--repo', URL, '--filter', 'url')
        self.assertIn('excluded by filter', error)

    def test_unknown_parameter(self) -> None:
        """Unknown parameters are rejected."""
        self.assertIn('unrecognized arguments', self.error_of(
            '--package', 'curl', '--repo', URL, '--color'))
