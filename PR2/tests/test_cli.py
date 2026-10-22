"""Tests of the entry point."""

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from depgraph.cli import EXIT_FAILURE, EXIT_SUCCESS, main
from tests.support import ServerTestCase


def run_main(*argv: str) -> tuple[int, str, str]:
    """Run main and return the exit code, stdout and stderr."""
    with (contextlib.redirect_stdout(io.StringIO()) as stdout,
          contextlib.redirect_stderr(io.StringIO()) as stderr):
        code = main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


class TestModeTest(unittest.TestCase):
    """Work with a test repository file."""

    def setUp(self) -> None:
        """Create a temporary directory."""
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base)

    def write_repo(self, text: str) -> str:
        """Write a test repository file and return its path."""
        path = self.base / 'repo.txt'
        path.write_text(text, encoding='utf-8')
        return str(path)

    def test_graph_is_printed(self) -> None:
        """The graph of a test repository is printed."""
        repo = self.write_repo('A: B C\nB: C\nC:\n')
        code, stdout, _ = run_main(
            '--package', 'A', '--repo', repo, '--test-mode')
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertEqual(stdout.splitlines(), [
            'Dependency graph of A:', 'A -> B, C', 'B -> C',
            'C -> (none)', 'Packages: 3', 'Cycles: 0'])

    def test_cycle_is_reported(self) -> None:
        """A cyclic repository does not hang."""
        repo = self.write_repo('A: B\nB: A\n')
        code, stdout, _ = run_main(
            '--package', 'A', '--repo', repo, '--test-mode')
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertIn('  A -> B -> A', stdout)

    def test_filter(self) -> None:
        """The filter removes packages from the graph."""
        repo = self.write_repo('A: B C\nB:\nC:\n')
        _, stdout, _ = run_main(
            '--package', 'A', '--repo', repo, '--test-mode',
            '--filter', 'B')
        self.assertIn('A -> C', stdout)
        self.assertNotIn('B', stdout.replace('Dependency graph', ''))

    def test_unknown_package(self) -> None:
        """A package missing from the repository is an error."""
        repo = self.write_repo('A:\n')
        code, stdout, stderr = run_main(
            '--package', 'Z', '--repo', repo, '--test-mode')
        self.assertEqual((code, stdout), (EXIT_FAILURE, ''))
        self.assertIn("depgraph: error: package 'Z' not found", stderr)

    def test_invalid_repository_file(self) -> None:
        """A malformed test repository is an error."""
        repo = self.write_repo('A B\n')
        code, _, stderr = run_main(
            '--package', 'A', '--repo', repo, '--test-mode')
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn('repo.txt:1: expected', stderr)

    def test_deep_recursion_is_reported(self) -> None:
        """A chain deeper than the recursion limit is an error."""
        names = ['Q' * (index + 1) for index in range(1500)]
        lines = [f'{a}: {b}' for a, b in zip(names, names[1:], strict=False)]
        repo = self.write_repo('\n'.join(lines) + '\n')
        code, _, stderr = run_main(
            '--package', names[0], '--repo', repo, '--test-mode')
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn('too deep', stderr)


class AlpineModeTest(ServerTestCase):
    """Work with an Alpine repository over HTTP."""

    def test_graph_of_curl(self) -> None:
        """Transitive dependencies of curl are printed."""
        url = self.publish_index()
        code, stdout, _ = run_main('--package', 'curl', '--repo', url)
        self.assertEqual(code, EXIT_SUCCESS)
        lines = stdout.splitlines()
        self.assertEqual(lines[1], (
            'curl -> ca-certificates-bundle, libcurl, musl, busybox, zlib, '
            'so:libmissing.so.9'))
        self.assertIn('libcurl -> ca-certificates-bundle, musl, zlib', lines)
        self.assertIn('musl -> (none)', lines)
        self.assertIn('Cycles: 0', lines)

    def test_filter(self) -> None:
        """The filter removes libcurl, zlib and so:libmissing.so.9."""
        url = self.publish_index()
        _, stdout, _ = run_main(
            '--package', 'curl', '--repo', url, '--filter', 'lib')
        self.assertEqual(stdout.splitlines()[:2], [
            'Dependency graph of curl:',
            'curl -> ca-certificates-bundle, musl, busybox'])

    def test_unknown_package(self) -> None:
        """A package missing from the index is an error."""
        url = self.publish_index()
        code, _, stderr = run_main('--package', 'wget', '--repo', url)
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("package 'wget' not found", stderr)

    def test_repository_error(self) -> None:
        """A download error is printed without a traceback."""
        code, _, stderr = run_main(
            '--package', 'curl', '--repo', f'{self.base_url}/none')
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn('depgraph: error: cannot download', stderr)
