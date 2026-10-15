"""Tests of loading the VFS from CSV."""

import io
import shutil
import tempfile
import unittest
from pathlib import Path

from emulator.vfs import (
    Node, VfsError, create_root, load_vfs, parse_vfs, tree_lines)

HEADER = 'path,type,encoding,content\n'


def parse(text: str) -> Node:
    """Parse CSV text that follows the header."""
    return parse_vfs(io.StringIO(HEADER + text))


class ParseVfsTest(unittest.TestCase):
    """Valid VFS sources."""

    def test_header_only(self) -> None:
        """A VFS without entries is empty."""
        self.assertEqual(parse_vfs(io.StringIO(HEADER)), create_root())

    def test_text_file(self) -> None:
        """A text file keeps its content."""
        root = parse('/a.txt,file,text,hello\n')
        self.assertEqual(root.children['a.txt'].data, b'hello')

    def test_base64_file(self) -> None:
        """A binary file is decoded from base64."""
        root = parse('/bin,file,base64,AAEC/w==\n')
        self.assertEqual(root.children['bin'].data, b'\x00\x01\x02\xff')

    def test_multiline_and_quoted_text(self) -> None:
        """CSV quoting allows commas and line breaks."""
        root = parse('/a,file,text,"x,1\ny ""z"""\n')
        self.assertEqual(root.children['a'].data, b'x,1\ny "z"')

    def test_nested_entries(self) -> None:
        """Nesting is expressed by the path."""
        root = parse(
            '/a,dir,,\n/a/b,dir,,\n/a/b/c,dir,,\n/a/b/c/f,file,text,1\n')
        node = root.children['a'].children['b'].children['c']
        self.assertEqual(node.children['f'].data, b'1')

    def test_parents_are_created_implicitly(self) -> None:
        """Missing parent directories appear automatically."""
        root = parse('/x/y/f,file,text,1\n/x,dir,,\n')
        self.assertTrue(root.children['x'].children['y'].is_dir)

    def test_root_row_and_blank_lines(self) -> None:
        """The root row and blank lines are accepted."""
        root = parse('/,dir,,\n\n/a,dir,,\n')
        self.assertEqual(list(root.children), ['a'])


class InvalidVfsTest(unittest.TestCase):
    """Broken VFS sources are reported with a line number."""

    def assert_error(self, text: str, message: str) -> None:
        """Check that parsing fails with the given message."""
        with self.assertRaisesRegex(VfsError, message):
            parse(text)

    def test_header(self) -> None:
        """A wrong header is rejected."""
        with self.assertRaisesRegex(VfsError, 'line 1: header must be'):
            parse_vfs(io.StringIO('name,kind\n'))

    def test_empty_source(self) -> None:
        """An empty source is rejected."""
        with self.assertRaisesRegex(VfsError, 'header must be'):
            parse_vfs(io.StringIO(''))

    def test_field_count(self) -> None:
        """A row with a wrong number of fields is rejected."""
        self.assert_error('/a,dir\n', 'line 2: expected 4 fields, got 2')

    def test_unknown_type(self) -> None:
        """An unknown entry type is rejected."""
        self.assert_error('/a,link,,\n', "unknown type 'link'")

    def test_unknown_encoding(self) -> None:
        """An unknown encoding is rejected."""
        self.assert_error('/a,file,hex,00\n', "unknown encoding 'hex'")

    def test_invalid_base64(self) -> None:
        """Broken base64 is rejected."""
        self.assert_error('/a,file,base64,%%%\n', 'invalid base64')

    def test_relative_path(self) -> None:
        """A relative path is rejected."""
        self.assert_error('a/b,dir,,\n', 'path must be absolute')

    def test_dot_components(self) -> None:
        """Dot components and empty components are rejected."""
        self.assert_error('/a/../b,dir,,\n', 'invalid path')
        self.assert_error('/a//b,dir,,\n', 'invalid path')
        self.assert_error('/a/,dir,,\n', 'invalid path')

    def test_duplicate_file(self) -> None:
        """The same file twice is rejected."""
        self.assert_error(
            '/a,file,text,1\n/a,file,text,2\n', 'line 3: duplicate path')

    def test_file_used_as_directory(self) -> None:
        """A file cannot contain entries."""
        self.assert_error(
            '/a,file,text,1\n/a/b,file,text,2\n', 'is a file, not')

    def test_directory_over_file(self) -> None:
        """A directory cannot replace a file."""
        self.assert_error('/a,file,text,1\n/a,dir,,\n', 'is a file, not')

    def test_directory_with_content(self) -> None:
        """A directory row must not carry content."""
        self.assert_error('/a,dir,text,x\n', 'must have empty')

    def test_root_as_file(self) -> None:
        """The root cannot be a file."""
        self.assert_error('/,file,text,x\n', 'root is a directory')


class LoadVfsTest(unittest.TestCase):
    """Loading from files."""

    def setUp(self) -> None:
        """Create a temporary directory."""
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base)

    def test_load_file(self) -> None:
        """A file is loaded into memory, including a BOM."""
        path = self.base / 'v.csv'
        path.write_text(HEADER + '/a,dir,,\n', encoding='utf-8-sig')
        self.assertIn('a', load_vfs(str(path)).children)

    def test_missing_file(self) -> None:
        """A missing file is reported."""
        with self.assertRaisesRegex(VfsError, 'file not found'):
            load_vfs(str(self.base / 'none.csv'))

    def test_directory_instead_of_file(self) -> None:
        """A directory is reported as unreadable."""
        with self.assertRaisesRegex(VfsError, 'Is a directory'):
            load_vfs(str(self.base))

    def test_binary_file(self) -> None:
        """A file that is not UTF-8 text is reported."""
        path = self.base / 'v.csv'
        path.write_bytes(b'\xff\xfe\x00\x01')
        with self.assertRaisesRegex(VfsError, 'not UTF-8'):
            load_vfs(str(path))

    def test_error_contains_path(self) -> None:
        """Format errors mention the file."""
        path = self.base / 'v.csv'
        path.write_text('bad\n', encoding='utf-8')
        with self.assertRaisesRegex(VfsError, 'v.csv: line 1'):
            load_vfs(str(path))

    def test_source_file_is_not_modified(self) -> None:
        """Loading leaves the source file untouched."""
        path = self.base / 'v.csv'
        text = HEADER + '/a,file,text,1\n'
        path.write_text(text, encoding='utf-8')
        load_vfs(str(path))
        self.assertEqual(path.read_text(encoding='utf-8'), text)
        self.assertEqual([item.name for item in self.base.iterdir()],
                         ['v.csv'])


class TreeLinesTest(unittest.TestCase):
    """Drawing of the tree."""

    def test_tree(self) -> None:
        """Entries are sorted and sizes are shown."""
        root = parse('/b/c,file,text,xyz\n/a,file,text,1\n/b/d,dir,,\n')
        self.assertEqual(tree_lines(root), [
            '|-- a (1 B)',
            '`-- b/',
            '    |-- c (3 B)',
            '    `-- d/',
        ])

    def test_empty(self) -> None:
        """An empty directory has no lines."""
        self.assertEqual(tree_lines(create_root()), [])
