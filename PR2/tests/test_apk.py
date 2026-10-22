"""Tests of the Alpine index: parsing, resolution and download."""

import gzip
import unittest
from functools import cached_property

from depgraph.apk import (
    ApkIndex, Package, extract_index, index_url, load_apk_index,
    parse_index, strip_version)
from depgraph.repository import RepositoryError
from tests.support import (
    CURL_DEPENDENCIES, SAMPLE_INDEX, ServerTestCase, make_archive,
    tar_bytes, unused_port_url)


class StripVersionTest(unittest.TestCase):
    """Removal of version constraints."""

    def test_operators(self) -> None:
        """Every apk operator is removed with the version."""
        cases = {
            'musl>=1.2': 'musl', 'a<2': 'a', 'a>1': 'a', 'a=1.0-r1': 'a',
            'a~1.2': 'a', 'a<=3': 'a', 'a><1': 'a', 'plain': 'plain',
        }
        for entry, expected in cases.items():
            self.assertEqual(strip_version(entry), expected)

    def test_virtual_names(self) -> None:
        """Characters of virtual names are kept."""
        self.assertEqual(
            strip_version('so:libstdc++.so.6=6'), 'so:libstdc++.so.6')
        self.assertEqual(strip_version('cmd:sh'), 'cmd:sh')


class ParseIndexTest(unittest.TestCase):
    """Parsing of the APKINDEX text."""

    def test_packages(self) -> None:
        """All records become packages."""
        index = parse_index(SAMPLE_INDEX)
        self.assertEqual(len(index.packages), 6)
        self.assertTrue(index.has_package('curl'))
        self.assertFalse(index.has_package('wget'))

    def test_fields(self) -> None:
        """Dependencies, provides and priority are read."""
        package = parse_index(SAMPLE_INDEX).packages['musl']
        self.assertEqual(package.provides, ['so:libc.musl-x86_64.so.1=1'])
        self.assertEqual(package.priority, 9)

    def test_windows_line_endings(self) -> None:
        """Records may be separated by CRLF."""
        index = parse_index('P:a\r\nD:b\r\n\r\nP:b\r\n')
        self.assertEqual(index.dependencies('a'), ['b'])

    def test_empty_index(self) -> None:
        """An index without packages is rejected."""
        with self.assertRaisesRegex(RepositoryError, 'no packages'):
            parse_index('<html>not an index</html>\n')

    def test_first_record_wins(self) -> None:
        """A repeated package name is ignored."""
        index = parse_index('P:a\nD:b\n\nP:a\nD:c\n')
        self.assertEqual(index.dependencies('a'), ['b'])


class DependenciesTest(unittest.TestCase):
    """Resolution of direct dependencies."""

    @cached_property
    def index(self) -> ApkIndex:
        """Return the parsed sample index."""
        return parse_index(SAMPLE_INDEX)

    def test_curl(self) -> None:
        """Virtual names become packages, constraints are removed."""
        self.assertEqual(self.index.dependencies('curl'), CURL_DEPENDENCIES)

    def test_no_dependencies(self) -> None:
        """A package without D field has no dependencies."""
        self.assertEqual(
            self.index.dependencies('ca-certificates-bundle'), [])

    def test_unknown_package(self) -> None:
        """An unknown package has no dependencies."""
        self.assertEqual(self.index.dependencies('wget'), [])

    def test_negations_and_duplicates(self) -> None:
        """Conflicts are skipped and repeated entries are merged."""
        index = parse_index('P:a\nD:b !c b>=1 b<3\n\nP:b\n')
        self.assertEqual(index.dependencies('a'), ['b'])

    def test_self_dependency_is_skipped(self) -> None:
        """A package that provides its own dependency is not a loop."""
        index = parse_index('P:a\nD:so:x.so\np:so:x.so\n')
        self.assertEqual(index.dependencies('a'), [])

    def test_real_package_wins_over_provider(self) -> None:
        """A package name is not replaced by another provider."""
        index = parse_index('P:a\nD:b\n\nP:b\n\nP:c\np:b\n')
        self.assertEqual(index.dependencies('a'), ['b'])

    def test_provider_priority(self) -> None:
        """The provider with the highest priority is chosen."""
        index = ApkIndex([
            Package('x', depends=['cmd:ed']),
            Package('low', provides=['cmd:ed'], priority=10),
            Package('high', provides=['cmd:ed=1'], priority=20),
        ])
        self.assertEqual(index.dependencies('x'), ['high'])

    def test_provider_tie(self) -> None:
        """On equal priority the first provider is chosen."""
        index = ApkIndex([
            Package('x', depends=['cmd:ed']),
            Package('first', provides=['cmd:ed']),
            Package('second', provides=['cmd:ed']),
        ])
        self.assertEqual(index.dependencies('x'), ['first'])


class IndexUrlTest(unittest.TestCase):
    """Building of the index URL."""

    def test_repository_url(self) -> None:
        """The index file name is appended."""
        self.assertEqual(index_url('http://h/a/main/x86_64'),
                         'http://h/a/main/x86_64/APKINDEX.tar.gz')

    def test_trailing_slash(self) -> None:
        """A trailing slash is not doubled."""
        self.assertEqual(index_url('http://h/a/'),
                         'http://h/a/APKINDEX.tar.gz')

    def test_full_index_url(self) -> None:
        """A URL of the index itself is kept."""
        url = 'http://h/a/APKINDEX.tar.gz'
        self.assertEqual(index_url(url), url)


class ExtractIndexTest(unittest.TestCase):
    """Reading of APKINDEX.tar.gz."""

    def test_signed_archive(self) -> None:
        """The index is found after a cut signature member."""
        self.assertEqual(extract_index(make_archive('P:a\n')), 'P:a\n')

    def test_complete_signature_member(self) -> None:
        """The index is found after a complete signature archive."""
        archive = make_archive('P:a\n', cut_signature=False)
        self.assertEqual(extract_index(archive), 'P:a\n')

    def test_missing_member(self) -> None:
        """An archive without APKINDEX is rejected."""
        archive = gzip.compress(tar_bytes({'other': b'x'}))
        with self.assertRaisesRegex(RepositoryError, 'not found'):
            extract_index(archive)

    def test_garbage(self) -> None:
        """Data that is not an archive is rejected."""
        with self.assertRaisesRegex(RepositoryError, 'invalid index'):
            extract_index(b'<html>404</html>')

    def test_truncated_archive(self) -> None:
        """A truncated archive is rejected."""
        archive = make_archive(SAMPLE_INDEX)
        with self.assertRaisesRegex(RepositoryError, 'invalid index'):
            extract_index(archive[:len(archive) // 2])


class DownloadTest(ServerTestCase):
    """Loading of the index over HTTP."""

    def test_load(self) -> None:
        """The index is downloaded and parsed."""
        index = load_apk_index(self.publish_index())
        self.assertEqual(index.dependencies('curl'), CURL_DEPENDENCIES)

    def test_http_error(self) -> None:
        """A missing index is reported with the HTTP status."""
        with self.assertRaisesRegex(RepositoryError, 'HTTP 404'):
            load_apk_index(f'{self.base_url}/nothing')

    def test_connection_refused(self) -> None:
        """An unreachable server is reported."""
        with (unused_port_url() as url,
              self.assertRaisesRegex(RepositoryError, 'cannot download')):
            load_apk_index(url)

    def test_not_an_archive(self) -> None:
        """Text instead of an archive is rejected."""
        self.publish('alpine/main/x86_64/APKINDEX.tar.gz', b'<html>')
        with self.assertRaisesRegex(RepositoryError, 'invalid index'):
            load_apk_index(f'{self.base_url}/alpine/main/x86_64')
