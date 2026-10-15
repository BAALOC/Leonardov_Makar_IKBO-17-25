"""In-memory virtual file system loaded from a CSV file."""

from __future__ import annotations

import base64
import binascii
import csv
from dataclasses import dataclass, field
from typing import TextIO

CSV_COLUMNS = ['path', 'type', 'encoding', 'content']
TYPE_DIR = 'dir'
TYPE_FILE = 'file'
ENCODING_TEXT = 'text'
ENCODING_BASE64 = 'base64'
SEPARATOR = '/'
INVALID_PARTS = ('', '.', '..')
TEXT_CODEC = 'utf-8'


class VfsError(Exception):
    """Raised when a VFS cannot be loaded."""


@dataclass
class Node:
    """A directory or a file of the VFS."""

    is_dir: bool
    data: bytes = b''
    children: dict[str, Node] = field(default_factory=dict)


def create_root() -> Node:
    """Create an empty VFS that contains only the root directory."""
    return Node(is_dir=True)


def split_path(path: str) -> list[str]:
    """Split an absolute path into its components."""
    if not path.startswith(SEPARATOR):
        raise VfsError(f'path must be absolute: {path!r}')
    if path == SEPARATOR:
        return []
    parts = path[len(SEPARATOR):].split(SEPARATOR)
    if any(part in INVALID_PARTS for part in parts):
        raise VfsError(f'invalid path: {path!r}')
    return parts


def make_dirs(root: Node, parts: list[str]) -> Node:
    """Return the directory at the path, creating missing ones."""
    node = root
    for part in parts:
        node = node.children.setdefault(part, create_root())
        if not node.is_dir:
            raise VfsError(f'{part!r} is a file, not a directory')
    return node


def decode_content(encoding: str, content: str) -> bytes:
    """Convert the content field of a file row to bytes."""
    if encoding == ENCODING_TEXT:
        return content.encode(TEXT_CODEC)
    if encoding == ENCODING_BASE64:
        try:
            return base64.b64decode(content, validate=True)
        except binascii.Error:
            raise VfsError('invalid base64 content') from None
    raise VfsError(f'unknown encoding {encoding!r}')


def add_dir(
        root: Node, parts: list[str], encoding: str, content: str) -> None:
    """Add a directory entry."""
    if encoding or content:
        raise VfsError('a directory must have empty encoding and content')
    make_dirs(root, parts)


def add_file(
        root: Node, parts: list[str], encoding: str, content: str) -> None:
    """Add a file entry."""
    if not parts:
        raise VfsError('the root is a directory, not a file')
    parent = make_dirs(root, parts[:-1])
    name = parts[-1]
    if name in parent.children:
        raise VfsError(f'duplicate path: {name!r}')
    parent.children[name] = Node(
        is_dir=False, data=decode_content(encoding, content))


def add_row(root: Node, row: list[str]) -> None:
    """Add one CSV row to the tree."""
    if len(row) != len(CSV_COLUMNS):
        raise VfsError(f'expected {len(CSV_COLUMNS)} fields, got {len(row)}')
    path, kind, encoding, content = row
    parts = split_path(path)
    if kind == TYPE_DIR:
        add_dir(root, parts, encoding, content)
    elif kind == TYPE_FILE:
        add_file(root, parts, encoding, content)
    else:
        raise VfsError(f'unknown type {kind!r}')


def parse_vfs(source: TextIO) -> Node:
    """Build the tree from CSV text."""
    reader = csv.reader(source)
    root = create_root()
    try:
        if next(reader, None) != CSV_COLUMNS:
            raise VfsError('header must be ' + ','.join(CSV_COLUMNS))
        for row in reader:
            if row:
                add_row(root, row)
    except (VfsError, csv.Error) as error:
        raise VfsError(f'line {reader.line_num}: {error}') from None
    return root


def load_vfs(path: str) -> Node:
    """Load the VFS from a CSV file into memory."""
    try:
        with open(path, encoding='utf-8-sig', newline='') as source:
            return parse_vfs(source)
    except FileNotFoundError:
        raise VfsError(f'{path}: file not found') from None
    except OSError as error:
        raise VfsError(f'{path}: {error.strerror}') from None
    except UnicodeDecodeError:
        raise VfsError(f'{path}: not UTF-8 text') from None
    except VfsError as error:
        raise VfsError(f'{path}: {error}') from None


def describe(name: str, node: Node) -> str:
    """Return the tree label of a node."""
    if node.is_dir:
        return name + SEPARATOR
    return f'{name} ({len(node.data)} B)'


def tree_lines(node: Node, prefix: str = '') -> list[str]:
    """Return the lines of a tree drawing of the directory contents."""
    lines = []
    total = len(node.children)
    for index, name in enumerate(sorted(node.children), start=1):
        child = node.children[name]
        last = index == total
        lines.append(prefix + ('`-- ' if last else '|-- ')
                     + describe(name, child))
        if child.is_dir:
            indent = prefix + ('    ' if last else '|   ')
            lines.extend(tree_lines(child, indent))
    return lines
